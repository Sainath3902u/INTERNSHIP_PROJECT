# Network Traffic Benchmark Backend
## Complete Technical & Architecture Report

**Project:** Network Data Benchmark Backend
**Stack:** FastAPI + DuckDB + SQLite + APScheduler

---

## Table of Contents

1. [What This Backend Does](#1-what-this-backend-does)
2. [Technology Stack & Why Each Was Chosen](#2-technology-stack--why-each-was-chosen)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Folder Structure](#4-folder-structure)
5. [Module-by-Module Deep Dive](#5-module-by-module-deep-dive)
6. [The Job Lifecycle (State Machine)](#6-the-job-lifecycle-state-machine)
7. [Complete Request Workflows](#7-complete-request-workflows-every-frontend-call)
8. [The Evaluation Engine — How Scoring Actually Works](#8-the-evaluation-engine--how-scoring-actually-works)
9. [Concurrency & Parallelism Design](#9-concurrency--parallelism-design)
10. [Storage Layout & Cleanup Policy](#10-storage-layout--cleanup-policy)
11. [Configuration Reference](#11-configuration-reference)
12. [Error-Handling Philosophy](#12-error-handling-philosophy)
13. [Full API Reference](#13-full-api-reference)
14. [Design Decisions — Trade-offs Explained](#14-design-decisions--trade-offs-explained)
15. [Known Limitations & Suggested Improvements](#15-known-limitations--suggested-improvements)

---

## 1. What This Backend Does

This backend answers one question: **"How statistically similar is a synthetic (AI-generated) network packet trace to a real one?"**

A user (via the frontend) uploads two CSV files — a **real** packet capture and a **synthetic** packet capture, both with the schema:

```
time, pkt_len, srcip, dstip, srcport, dstport, proto
```

The backend runs **70 distinct analytical queries** against both datasets (grouped into three categories — packet-level, flow-level stateless, flow-level stateful), computes **~135 individual fidelity metrics** by comparing the real vs. synthetic result of each query using statistical distance functions (Jensen–Shannon Divergence, Absolute Relative Error, Wasserstein Distance, relative L1 distance, Top-N key overlap), and returns a structured **fidelity report** — per-metric scores, category roll-ups, percentiles, best/worst performing metrics, and ready-to-plot visualization payloads.

This is the kind of tool used to validate synthetic data generators (e.g., GANs / diffusion models for network traffic) — "does the fake traffic *statistically* look like the real traffic?"

---

## 2. Technology Stack & Why Each Was Chosen

| Component | Choice | Reason |
|---|---|---|
| **Web framework** | FastAPI | Supports asynchronous requests, automatically validates inputs, and is well suited for job submission and polling. |
| **Analytical database** | DuckDB (embedded, per-job `.duckdb` file) | Embedded columnar OLAP database that executes analytical SQL efficiently over large CSV files without requiring a separate database server. |
| **Job metadata store** | SQLite (via `job_store.py`) | Lightweight, serverless ACID database with WAL mode for concurrent reads and writes. Can be replaced with PostgreSQL if higher concurrency is needed. |
| **Background execution** | FastAPI `BackgroundTasks` + `ThreadPoolExecutor` | Supports background execution of CPU- and I/O-intensive tasks while keeping the API responsive. |
| **Scheduled maintenance** | APScheduler (`BackgroundScheduler`) | Schedules periodic maintenance tasks, such as purging old job directories, without requiring external scheduling infrastructure. |
| **Config management** | `pydantic-settings` | Type-safe `.env`-driven configuration with a single shared `Settings` instance — avoids scattering `os.environ` calls everywhere. |
| **Numerical / stats** | numpy, scipy, pandas | Distance metrics (Jensen-Shannon, Wasserstein), dataframe manipulation of SQL query results. |

---

## 3. High-Level Architecture

The backend follows a **layered service architecture** — each layer has one job and only talks to the layer directly below it. This is the classic reason to choose this style for an internship/production codebase: **testability** (each layer can be tested independently), **replaceability** (the SQLite job store can become Postgres without touching the API layer), and **clarity** (a new engineer can trace any request top-to-bottom through exactly one path).

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (SPA)                          │
└───────────────────────────────┬───────────────────────────────-┘
                                 │  HTTP (CORS-enabled)
┌────────────────────────────────▼────────────────────────────────┐
│  API LAYER  (app/api/*)                                          │
│  upload.py · evaluate.py · jobs.py                                │
│  — FastAPI routers, request validation, HTTP status mapping       │
└────────────────────────────────┬──────────────────────────────-─┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│  SERVICE LAYER  (app/services/*)                                 │
│  ┌───────────────┐ ┌────────────────┐ ┌────────────────────────┐│
│  │ job/           │ │ ingestion/     │ │ execution/             ││
│  │ JobManager     │ │ CSVLoader      │ │ BaseRunner             ││
│  │ FileManager    │ │ ParquetConv.   │ │ PacketRunner           ││
│  │ JobExecutor    │ │                │ │ FlowStatelessRunner    ││
│  │ cleanup.py     │ │                │ │ FlowStatefulRunner     ││
│  └───────────────┘ └────────────────┘ └────────────────────────┘│
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ evaluation/                                                 │ │
│  │ EvaluationController (sequential) / Parallel version         │ │
│  │ MetricRunner · ReportGenerator                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬─────────────────────────────-──┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│  DATA / DEFINITION LAYER                                         │
│  app/queries/*   → 70 SQL query definitions (3 category files)   │
│  app/measures/*  → ~135 metric functions (distance computations) │
│  app/database/*  → DuckDBManager, job_store (SQLite)              │
└────────────────────────────────┬──────────────────────────────-─┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│  PERSISTENCE                                                     │
│  storage/job_metadata.db   (SQLite — job status/lifecycle)       │
│  storage/jobs/{job_id}/    (per-job directory — see Section 10)  │
│    uploads/  database/  outputs/  logs/                          │
└──────────────────────────────────────────────────────────────-──┘
```

**Why this shape specifically?** Two design principles run through the whole codebase:

1. **Separation of "what to run" from "how to run it."** The `queries/` files are pure data — lists of dicts describing SQL + which metric functions apply. The `execution/` layer (`BaseRunner`) is a generic engine that runs *any* list of such queries, sequentially or in parallel, and turns SQL errors and metric errors into structured failures instead of crashes. `PacketRunner`, `FlowStatelessRunner`, `FlowStatefulRunner` are three near-zero-code subclasses that just point `QUERIES` at a different list. Adding a fourth evaluation category later means writing one query list — zero changes to the execution engine.

2. **Separation of "job metadata" from "job files."** `job_store.py` (SQLite) only ever stores status/timestamps — small, fast, queryable rows. `JobManager` (filesystem) only ever manages paths and directories. Neither layer knows about the other's internals; `JobExecutor` is the only place that coordinates both.

---

## 4. Folder Structure

```
backend/
├── .env                          # Environment configuration
├── requirements.txt              # fastapi, uvicorn, duckdb, pandas, numpy, scipy,
│                                  # tqdm, pydantic-settings, apscheduler
│
└── app/
    ├── main.py                   # FastAPI app factory, lifespan, CORS, routers
    │
    ├── core/                     # Cross-cutting application concerns
    │   ├── config.py             #   Settings (pydantic-settings) — single source of config
    │   ├── logging_config.py     #   JSON structured logging setup
    │   └── scheduler.py          #   APScheduler wrapper for periodic cleanup
    │
    ├── database/                 # Persistence primitives
    │   ├── db.py                 #   get_connection() / get_read_connection() → DuckDB
    │   ├── duckdb_manager.py     #   Thin wrapper around duckdb.connect()
    │   └── job_store.py          #   SQLite-backed job metadata (status, timestamps)
    │
    ├── api/                      # HTTP boundary — FastAPI routers only
    │   ├── upload.py             #   POST /create-job, /upload-real, /upload-synthetic
    │   ├── evaluate.py           #   POST /evaluate, /evaluate/parallel
    │   └── jobs.py               #   GET  /jobs/{id}/status, /jobs/{id}/result, /jobs
    │
    ├── services/
    │   ├── job/                  # Job orchestration & filesystem
    │   │   ├── job_manager.py    #   Path resolution, directory creation
    │   │   ├── file_manager.py   #   Chunked, size-limited file save
    │   │   ├── job_executor.py   #   Orchestrates ingest → evaluate → persist result
    │   │   └── cleanup.py        #   Deletes expired job directories + DB rows
    │   │
    │   ├── ingestion/            # CSV → DuckDB table loading
    │   │   ├── csv_loader.py     #   Loads CSVs, builds per-entity inter-arrival "gap" tables
    │   │   └── parquet_converter.py  # (utility, not wired into the main pipeline)
    │   │
    │   ├── execution/            # Generic query-running engine
    │   │   ├── base_executor.py  #   BaseRunner — runs queries seq/parallel, isolates failures
    │   │   ├── packet_executor.py
    │   │   ├── flow_stateless_executor.py
    │   │   └── flow_stateful_executor.py
    │   │
    │   └── evaluation/           # Orchestrates the 3 phases + report building
    │       ├── evaluation_controller.py           # Sequential (safe fallback)
    │       ├── evaluation_controller_parallel.py  # Parallel (production default)
    │       ├── metric_imports.py                  # Aggregates all metric functions
    │       ├── metric_runner.py                   # Safe dispatcher: name → function, never throws
    │       └── report_generator.py                # Aggregates raw metrics into a summary report
    │
    ├── queries/                  # SQL + metadata — the "what to measure" definitions
    │   ├── packet_queries.py             #  29 queries (packet-level)
    │   ├── flow_stateless_queries.py     #  21 queries (flow-level, stateless)
    │   ├── flow_stateful_queries.py      #  21 queries (flow-level, stateful/timing)
    │   └── queries.md                    #  Human-readable catalog of all 70 queries
    │
    └── measures/                 # Metric functions — the "how to score" implementations
        ├── packet_metrics.py         #  ~55 metric functions
        ├── flow_stateless_metrics.py #  ~40 metric functions
        ├── flow_stateful_metrics.py  #  ~40 metric functions
        └── response_builders.py      #  Shared helpers that shape metric output +
                                       #  visualization payloads (bar/distribution charts)
```

**Runtime-generated storage** (not checked into source, created by the app):

```
storage/
├── job_metadata.db                 # SQLite: one row per job
└── jobs/
    └── {job_id}/                   # uuid4 hex, one directory per job
        ├── uploads/
        │   ├── real.csv
        │   └── synthetic.csv
        ├── database/
        │   └── benchmark.duckdb    # DuckDB file: real/synthetic tables + gap tables
        ├── outputs/
        │   └── result.json         # Final fidelity report
        └── logs/                   # Reserved for per-job log files
```

---

## 5. Module-by-Module Deep Dive

### 5.1 `app/main.py` — Application Entry Point

- Defines an `asynccontextmanager` **lifespan** hook. On startup it: configures JSON logging, initializes the SQLite `jobs` table (`job_store.init_db()`), and starts the APScheduler background cleanup job. On shutdown it stops the scheduler cleanly.
- Registers CORS middleware using `settings.cors_origin_list` — this is what allows the frontend (default `localhost:3000` / `localhost:5173`) to call the API from the browser.
- Mounts three routers: `upload_router`, `evaluate_router`, `jobs_router`.
- Two trivial endpoints: `GET /` (liveness banner) and `GET /health` (health check for load balancers / uptime monitors).

### 5.2 `app/core/config.py` — Settings

A single `Settings` object (Pydantic `BaseSettings`) reads every variable prefixed `BENCHMARK_` from `.env`:

| Setting | Default | Purpose |
|---|---|---|
| `storage_base_dir` | `storage/jobs` | Root of all per-job directories (resolved to an absolute path at startup so it's correct regardless of the process's working directory). |
| `job_db_path` | `storage/job_metadata.db` | SQLite file location. |
| `max_upload_mb` | 2048 (2 GB) | Hard cap enforced during file save. |
| `cors_origins` | `localhost:3000,localhost:5173` | Comma-separated list, parsed into `cors_origin_list`. |
| `cleanup_failed_after_hours` | 24 | Delete failed jobs after this long. |
| `cleanup_done_after_days` | 1 (see note below) | Delete completed jobs after this long. |
| `cleanup_abandoned_after_hours` | 24 | Delete jobs stuck in created/uploading/queued/running with no status update. |
| `cleanup_interval_minutes` | 60 | How often the background cleanup sweep runs. |

> **Note on the `.env` file:** the shipped `.env` sets `BENCHMARK_CLEANUP_DONE_AFTER_DAYS=1`, while the Python default in `config.py` is `7`. Since `.env` is loaded by `pydantic-settings`, the **effective runtime value is 1 day**, not 7 — worth flagging in a report because it means completed results are only guaranteed to be downloadable for 24 hours in the current `.env`, not a week.

Two computed properties: `max_upload_bytes` (MB → bytes) and `cors_origin_list` (CSV string → list).

### 5.3 `app/core/logging_config.py` — Structured Logging

Implements a custom `JsonFormatter` that emits every log line as a single JSON object (timestamp, level, logger name, message, and any extra fields passed via `extra={...}`). `configure_logging()` replaces the root logger's handlers so **all** app and framework logs share this format — this makes logs directly ingestible by log aggregation tools (ELK, CloudWatch, etc.) without a separate parser.

`get_job_logger(job_id)` returns a `LoggerAdapter` that automatically stamps every log line for that job with `job_id` — this is what lets you `grep`/filter a single job's entire lifecycle out of a shared log stream.

### 5.4 `app/core/scheduler.py` — Background Scheduler

Wraps APScheduler's `BackgroundScheduler`. `start_scheduler()` registers `run_cleanup` (from `services/job/cleanup.py`) on a fixed interval (`cleanup_interval_minutes`), with `max_instances=1` and `coalesce=True` — meaning **only one cleanup pass runs at a time**, and if a run is missed/overlaps, it doesn't queue up multiple redundant runs. `stop_scheduler()` shuts it down without blocking app shutdown (`wait=False`).

### 5.5 `app/database/` — Persistence Primitives

- **`duckdb_manager.py`**: a one-method static wrapper (`DuckDBManager.connect`) around `duckdb.connect()`. Exists purely to centralize DuckDB connection creation in one place.
- **`db.py`**: exposes two intent-revealing functions:
  - `get_connection(path)` → **read-write** connection. Used only during ingestion, where a single writer builds tables.
  - `get_read_connection(path)` → **read-only** connection. Used during evaluation. DuckDB allows *multiple concurrent read-only connections* to the same file as long as no read-write connection is open — this is precisely what makes the 3-way parallel evaluation phase (packet / stateless / stateful, each with its own connection) safe.
- **`job_store.py`**: the SQLite-backed job metadata layer (detailed fully in Section 6 — job lifecycle). Key design points:
  - Opens a fresh short-lived connection per call rather than a long-lived shared one (documented reasoning: SQLite connections aren't safely shared across threads, and job writes are infrequent, so the overhead is negligible).
  - Enables **WAL mode** so status reads (frequent, from polling clients) never block status writes.
  - `find_cleanup_candidates()` encodes the entire cleanup policy as a single parameterized SQL query with three OR'd conditions (failed/done/abandoned).

### 5.6 `app/api/` — HTTP Boundary

This layer is intentionally *thin* — routers validate input, translate service-layer results/exceptions into HTTP responses, and delegate everything else. No business logic lives here.

- **`upload.py`**
  - `POST /create-job` → `JobManager.create_job()`, returns `{job_id}`.
  - `POST /upload-real/{job_id}` and `POST /upload-synthetic/{job_id}` → validates the job exists and the file extension is `.csv`, then calls `FileManager.save_upload` **inside a threadpool** (`run_in_threadpool`) so a large multi-GB upload doesn't block the async event loop for every other concurrent request. Sets job status to `uploading`.
- **`evaluate.py`**
  - Shared validator `_validate_ready_for_evaluation`: checks the job exists, both CSVs are present, and — importantly — **rejects a second evaluation request if one is already `queued`/`running`** (HTTP 409) to prevent two concurrent writers hitting the same DuckDB file.
  - `POST /evaluate/{job_id}` → sequential path, sets status to `queued`, schedules `JobExecutor.run` as a FastAPI `BackgroundTask`.
  - `POST /evaluate/parallel/{job_id}` → same but schedules `JobExecutor.run_parallel` — the production-recommended endpoint.
  - Both return immediately with `{"job_id", "status": "queued"}` — the actual work happens after the HTTP response is sent.
- **`jobs.py`**
  - `GET /jobs/{job_id}/status` → returns the current lifecycle state + timestamps + error (if any). This is what the frontend polls.
  - `GET /jobs/{job_id}/result` → returns the full fidelity report JSON, but only if status is `done` (409 otherwise) — it also runs every value through `_json_safe()`, which recursively replaces `NaN`/`Infinity` floats with `null`, since raw `NaN` is not valid JSON and would break the response. Marks the job's `result_downloaded_at` timestamp on first successful fetch.
  - `GET /jobs?status=&limit=` → paginated job listing for a dashboard view.

### 5.7 `app/services/job/` — Job Orchestration

- **`job_manager.py`**: pure path-resolution utility. Every method is a `@staticmethod` returning a `Path` — `get_job_dir`, `get_upload_dir`, `get_database_dir`, `get_output_dir`, `get_logs_dir`, `get_real_csv`, `get_synthetic_csv`, `get_database_path`, `get_result_path`. `create_job()` calls `job_store.create_job()` (metadata) then creates the four subdirectories (`uploads/database/outputs/logs`) on disk. This class is the **single source of truth for where anything related to a job lives** — no other module hardcodes a path.
- **`file_manager.py`**: `save_upload(file, destination)` streams the incoming file to disk in 1 MB chunks (never loads the whole file into memory), enforcing `max_upload_bytes` mid-stream — if the limit is exceeded, it deletes the partial file and raises `ValueError` (which `upload.py` turns into HTTP 413). Logs the final size and duration.
- **`job_executor.py`**: the orchestrator that ties ingestion + evaluation together (see Section 7.3 for the full sequence). Exposes `run()` (sequential) and `run_parallel()` (parallel) — both share a single `_ingest()` helper so the two paths can never drift apart on how data is loaded.
- **`cleanup.py`**: implements the retention policy described in Section 10. Deletes files *before* the metadata row on purpose — if the process crashes mid-cleanup, the job just looks "abandoned" again next pass rather than becoming an orphaned, undiscoverable directory.

### 5.8 `app/services/ingestion/`

- **`csv_loader.py`**:
  - `load_csv_to_table(csv_path, table_name, conn)` — uses DuckDB's `read_csv_auto()` to infer schema and bulk-load a CSV directly into a table (`CREATE OR REPLACE TABLE ... AS SELECT * FROM read_csv_auto(...)`). This is dramatically faster than loading via pandas row-by-row because DuckDB's CSV reader is a native, multi-threaded, columnar loader.
  - `build_stateful_tables(table_name, conn)` — pre-computes **inter-arrival "gap" tables** for four partitioning granularities (`srcip`, `dstip`, `(srcip,dstip)` pair, and the full 5-tuple flow) using the SQL window function `time - LAG(time) OVER (PARTITION BY ... ORDER BY time)`. These four tables (`{table}_srcip_gaps`, `{table}_dstip_gaps`, `{table}_ippair_gaps`, `{table}_fivetuple_gaps`) are what every "Flow Level Stateful" query (Section 8) reads from — computing the gap once at ingestion time instead of recomputing it inside every one of the 20+ stateful queries.
- **`parquet_converter.py`**: a standalone utility class for converting a CSV to Parquet with a fixed 7-column schema. It is **not called anywhere else in the codebase** — it exists as a ready-to-use helper (e.g. for future data-export features or offline preprocessing) but is not part of the live request path.

### 5.9 `app/services/execution/` — The Generic Query Engine

- **`base_executor.py`** — `BaseRunner` is the heart of the "run many independent SQL+metric checks safely" pattern:
  - `run_query(conn, query)`: formats the query's `sql` template against both `real_packets` and `synthetic_packets` (or the gap tables), executes both, and for every metric name listed in `query["metric"]` calls `MetricRunner.compute(...)`. **Any exception — SQL syntax error, missing column, whatever — is caught** and turned into a structured `{"status": "error", ...}` entry rather than raising, so one broken query never aborts the batch.
  - `run_all(conn, max_workers=1)`: if `max_workers <= 1`, queries run one after another on the given connection. If `max_workers > 1`, it spins up a `ThreadPoolExecutor` and gives **each thread its own DuckDB cursor** (`conn.cursor()`) rather than sharing the connection object across threads — DuckDB cursors are safe for this, connections are not guaranteed to be under concurrent use from the same object.
- **`packet_executor.py` / `flow_stateless_executor.py` / `flow_stateful_executor.py`** — each is a **three-line subclass** of `BaseRunner` that only overrides `QUERIES` to point at the relevant query list (`PACKET_QUERIES`, `FLOW_STATELESS`, `FLOW_STATEFUL`). This is the payoff of the "data vs. engine" separation described in Section 3 — all the actual execution logic lives once, in the base class.

### 5.10 `app/services/evaluation/` — Orchestration & Reporting

- **`metric_imports.py`**: a single `import *` aggregator that pulls every function out of the three `measures/*.py` files into one namespace, so `MetricRunner` can look up any metric by name string regardless of which file it's defined in.
- **`metric_runner.py`**: `MetricRunner.compute(metric_name, real_df, synthetic_df)` — looks up the function by name via `getattr`, calls it, and **guarantees it never raises**: unknown metric names, `None` returns, and any exception inside the metric function itself are all caught and converted into `{"status": "error", "score": None, "error": "..."}`. This is the second layer of the "one bad thing shouldn't kill the whole job" philosophy (the first layer is `BaseRunner.run_query`).
- **`evaluation_controller.py`** (`EvaluationController`, sequential) and **`evaluation_controller_parallel.py`** (`ParallelEvaluationController`, parallel) — both orchestrate the same three phases (packet / flow-stateless / flow-stateful), generate a `ReportGenerator` report for each, and compute an **overall RMS (root-mean-square) score** across the three phase averages. Full detail in Section 8 and Section 9.
- **`report_generator.py`**: `ReportGenerator.generate(results)` turns the raw list of per-query results into a statistical summary:
  - Splits into `metrics` (succeeded, has a numeric score) vs `failed` (query or metric errored).
  - `overall`: mean / median / min / max / std / count across all scores.
  - `percentiles`: 5th through 95th percentile of scores (13 percentile points).
  - `by_category`: scores grouped by metric category, derived from the metric name prefix (`packet_*` / `flow_*` → first two underscore-separated tokens).
  - `by_metric_type`: scores grouped by metric *type* — `distribution`, `topnkey`, `topnvalue`, or `other`, inferred from the metric function's name suffix.
  - `best_5` / `worst_5`: the 5 lowest-scoring (best fidelity — lower distance = more similar) and 5 highest-scoring (worst fidelity) individual metrics.

### 5.11 `app/queries/` — What Gets Measured

Three Python files, each a flat list of dictionaries, one per query:

```python
{
    "id": "P-SRCIP-DIST",
    "section": "Packet Level",
    "sub_section": "Global Packet Statistics",
    "description": "Number of packets sent by each source IP",
    "category": "packet_level",
    "metric": ["packet_stateless_srcip_distribution"],
    "sql": "SELECT srcip, COUNT(*) AS pkts FROM {table_name} GROUP BY srcip ORDER BY pkts DESC"
}
```

- `{table_name}` is a template placeholder — `BaseRunner` substitutes `real_packets` and `synthetic_packets` (or the pre-built `*_gaps` tables for stateful queries) so the exact same query dict is run against both datasets.
- A query can list **more than one metric** — e.g. the same "distribution of packets per source IP" result is scored three different ways (`_topnkey`, `_topnvalue`, `_distribution` — comparing which keys dominate, how close their magnitudes are, and the full distribution shape respectively).
- `queries.md` is hand-written documentation mirroring all 70 queries in readable form — a genuinely useful artifact for onboarding, and it explicitly documents which query functions are **defined in the metrics files but intentionally not registered/active** (e.g. `flag`/`ttl`-based queries, since those CSV columns aren't part of the ingested schema).

**Query category breakdown:**

| Category | # Queries | # Metrics computed | What it measures |
|---|---|---|---|
| Packet Level | 29 | 55 | Global counts, per-source-port and per-destination-port aggregations — no notion of time ordering. |
| Flow Level — Stateless | 21 | 40 | Per-source-IP, per-destination-IP, per-IP-pair, per-5-tuple-flow aggregations (packet counts, byte totals, cardinalities) — still no time ordering. |
| Flow Level — Stateful | 21 | 40 | Timing-dependent metrics per entity: average inter-arrival time, flow duration, byte rate, std-dev and coefficient-of-variation of inter-arrival time — requires the `LAG()`-based gap tables built during ingestion. |
| **Total** | **70** (queries.md documents ~70; actual code has 71 across the 3 files) | **~135** | |

### 5.12 `app/measures/` — How Similarity Is Scored

Four files, ~135 functions total, all following the same contract: `f(real_df, synthetic_df) -> dict` where the returned dict always contains `"score"` (a float, generally normalized so **0 = identical, higher = more different**) and a `"visualization"` payload shaped for direct frontend charting (`response_builders.py` factory functions standardize this shape — `build_single_value`, `build_distribution`, `build_topnkey`, `build_topn`, `build_category_distribution`).

The recurring distance functions:

| Function | Used for | What it computes |
|---|---|---|
| **Absolute Relative Error (ARE)** | Single scalar comparisons (counts, sums, averages) | `min(|real - synth| / real, 1.0)` — clamped to `[0,1]`. |
| **Jensen–Shannon Divergence (JSD)** | Distribution shape comparisons | Symmetric, bounded (0–1 with `base=2`) divergence between two normalized probability distributions. Both arrays are zero-clipped, zero-padded to equal length, and normalized to sum to 1 before comparison. Handles all-zero / empty edge cases explicitly (returns 0 if both empty, 1 if only one is empty). |
| **Wasserstein Distance** (Earth Mover's Distance) | Some numeric distributions (e.g. raw value comparisons where ordering/magnitude matters, not just rank) | `scipy.stats.wasserstein_distance` — the "cost to reshape one distribution into the other." |
| **Top-N relative L1 distance** | `_topnvalue` metrics | `mean(|x_i - y_i| / (x_i + y_i + ε))` over the top-N ranked values from each side — bounded `[0,1]`. |
| **Top-N key overlap** | `_topnkey` metrics | Compares *which* entities (IPs/ports) dominate the top-N ranks, independent of their exact magnitude. |

**Example — `packet_stateless__count`** (the simplest metric): counts total packets in each trace, computes `min(|real-synth|/real, 1.0)`, wraps it via `build_single_value` for a two-bar chart.

**Example — `packet_stateless_srcip_distribution`**: takes the per-source-IP packet-count column from both SQL results, normalizes each to a probability distribution, **sorts descending (IP-agnostic — comparing shape, not which specific IP)**, zero-pads to equal length, and scores with JSD. This IP-agnostic design choice matters: it means the metric checks "does the *skew* of traffic across sources look realistic" rather than "does IP 10.0.0.5 specifically send the same volume in both traces" (which would be an unreasonable ask for synthetic data using different fake IPs).

---

## 6. The Job Lifecycle (State Machine)

Every job moves through a strict, one-directional state machine, persisted in the `jobs` table (`job_store.py`):

```
        create-job
            │
            ▼
        ┌────────┐
        │created │
        └───┬────┘
            │ upload-real / upload-synthetic
            ▼
      ┌───────────┐
      │ uploading │
      └─────┬─────┘
            │ evaluate/{id}  or  evaluate/parallel/{id}
            ▼
       ┌─────────┐
       │ queued  │ ◄── (409 if evaluate is called again while queued/running)
       └────┬────┘
            │ background task picks it up
            ▼
       ┌─────────┐
       │ running │
       └────┬────┘
       ┌─────┴─────┐
       ▼           ▼
   ┌──────┐    ┌────────┐
   │ done │    │ failed │
   └──────┘    └────────┘
       │ any state, if stale/expired
       ▼
   [deleted by scheduled cleanup — Section 10]
```

Each row tracks: `job_id`, `status`, `created_at`, `updated_at`, `completed_at` (set only on `done`/`failed`), `error` (populated only on `failed`), `result_downloaded_at` (set on first successful `GET /jobs/{id}/result`, used by cleanup to prioritize jobs whose result was never picked up... though in the current policy `done`-based cleanup is time-based, not download-based).

---

## 7. Complete Request Workflows (Every Frontend Request)

### 7.1 `POST /create-job`

```
Frontend                     API (upload.py)          JobManager           job_store (SQLite)
   │  POST /create-job              │                      │                      │
   ├────────────────────────────────►                      │                      │
   │                                 │  JobManager.create_job()                   │
   │                                 ├──────────────────────►                     │
   │                                 │                      │  job_store.create_job()
   │                                 │                      ├──────────────────────►
   │                                 │                      │   INSERT row, status=created
   │                                 │                      │◄──────────────────────┤ job_id
   │                                 │                      │  mkdir uploads/database/outputs/logs
   │                                 │◄──────────────────────┤
   │  200 {"job_id": "<uuid4hex>"}  │                      │                      │
   ◄────────────────────────────────┤                      │                      │
```
Nothing is uploaded yet — this call only reserves a `job_id` and creates the on-disk skeleton.

### 7.2 `POST /upload-real/{job_id}` and `POST /upload-synthetic/{job_id}`

```
Frontend              API (upload.py)                  FileManager                job_store
  │ POST /upload-real/{id}  (multipart file)              │                          │
  ├──────────────────────────►                             │                          │
  │                            │ 404 if job_id unknown      │                          │
  │                            │ 400 if not .csv             │                          │
  │                            │ run_in_threadpool(save_upload)                        │
  │                            ├─────────────────────────────►                         │
  │                            │        stream file to disk in 1MB chunks              │
  │                            │        enforce max_upload_bytes (413 if exceeded)      │
  │                            │◄─────────────────────────────┤                        │
  │                            │  job_store.set_status(uploading)                       │
  │                            ├──────────────────────────────────────────────────────►│
  │  200 {"message": "..."}   │                             │                          │
  ◄────────────────────────────┤                            │                          │
```
Called twice by the frontend — once for `real.csv`, once for `synthetic.csv`. The file save runs in a **thread pool**, not directly in the `async def` route, specifically so a multi-GB upload doesn't freeze the event loop for other in-flight requests (a subtlety explicitly commented in the code).

### 7.3 `POST /evaluate/parallel/{job_id}` — The Core Pipeline

This is the most important workflow in the system — everything else exists to support it.

```
Frontend        evaluate.py         JobExecutor          CSVLoader         DuckDB          EvaluationController(Parallel)
  │ POST /evaluate/parallel/{id}      │                     │                 │                        │
  ├─────────────────────────────────►│                      │                 │                        │
  │  validate: job exists,            │                      │                 │                        │
  │  both CSVs uploaded,              │                      │                 │                        │
  │  not already queued/running       │                      │                 │                        │
  │  set_status(queued)               │                      │                 │                        │
  │  background_tasks.add_task(run_parallel)                 │                 │                        │
  │  200 {"job_id","status":"queued"} │                      │                 │                        │
  ◄─────────────────────────────────┤                      │                 │                        │
  ┊ (HTTP response already sent — everything below happens async, in-process) ┊
  │                                   │  set_status(running)│                 │                        │
  │                                   ├──────────────────────►                │                        │
  │                                   │  _ingest(job_id)      │                 │                        │
  │                                   ├───────────────────────►                │                        │
  │                                   │        load_csv_to_table(real.csv → real_packets)               │
  │                                   │        load_csv_to_table(synthetic.csv → synthetic_packets)      │
  │                                   │        ├─────────────────────────────►│                        │
  │                                   │        build_stateful_tables() ×2 IN PARALLEL (ThreadPoolExecutor, 2 workers)
  │                                   │        (creates *_srcip_gaps, *_dstip_gaps, *_ippair_gaps, *_fivetuple_gaps
  │                                   │         for both real_packets and synthetic_packets, 8 tables total)
  │                                   │◄───────────────────────┤                                        │
  │                                   │  ParallelEvaluationController.run_all(db_path)                   │
  │                                   ├──────────────────────────────────────────────────────────────────►
  │                                   │                                                     3 threads, one per phase:
  │                                   │                                                     ┌─ PacketRunner
  │                                   │                                                     │    open read-only conn
  │                                   │                                                     │    run 29 queries, 8 threads
  │                                   │                                                     ├─ FlowStatelessRunner
  │                                   │                                                     │    open read-only conn
  │                                   │                                                     │    run 21 queries, 8 threads
  │                                   │                                                     └─ FlowStatefulRunner
  │                                   │                                                          open read-only conn
  │                                   │                                                          run 21 queries, 8 threads
  │                                   │                                          each query: MetricRunner.compute()
  │                                   │                                          per phase: ReportGenerator.generate()
  │                                   │◄──────────────────────────────────────────────────────────────────┤
  │                                   │  compute overallRMS across 3 phase averages                        │
  │                                   │  _save_result() → outputs/result.json                              │
  │                                   │  set_status(done)                                                   │
```

If **any** exception escapes this whole pipeline (bad CSV schema, disk full, DuckDB error, etc.), `JobExecutor` catches it at the top level, calls `job_store.set_status(job_id, FAILED, error=...)`, and logs the full traceback — the job simply becomes visible as `failed` with a human-readable error string, rather than leaving the job stuck in `running` forever.

### 7.4 `POST /evaluate/{job_id}` — Sequential Fallback

Identical validation and status transitions to 7.3, but calls `JobExecutor.run()` → `EvaluationController.run_all(conn)`, which runs the three phases **one after another on a single connection**, and within each phase runs queries **one after another** (`max_workers=1` implicitly, since `BaseRunner.run_all` is called with the default). Same output shape, same correctness — just slower. Documented in the code as "the safe fallback" — useful for debugging (deterministic ordering, easier to reason about in logs) or environments where thread-pool concurrency against DuckDB is undesirable.

### 7.5 `GET /jobs/{job_id}/status` — Polling

```
Frontend                    jobs.py                 job_store (SQLite)
  │  GET /jobs/{id}/status     │                          │
  ├────────────────────────────►                          │
  │                             │  get_job(job_id)          │
  │                             ├──────────────────────────►
  │                             │◄──────────────────────────┤ row or None
  │  404 if job unknown        │                          │
  │  200 {job_id, status,      │                          │
  │       created_at,          │                          │
  │       updated_at,          │                          │
  │       completed_at, error} │                          │
  ◄────────────────────────────┤                          │
```
The frontend is expected to **poll this endpoint** (e.g. every 1–2 seconds) after calling `/evaluate/...` until `status` becomes `done` or `failed`. There is no WebSocket/SSE push channel in this codebase — status delivery is pull-based.

### 7.6 `GET /jobs/{job_id}/result` — Fetching the Report

```
Frontend                jobs.py                   job_store          filesystem (outputs/result.json)
  │  GET /jobs/{id}/result       │                     │                       │
  ├───────────────────────────────►                    │                       │
  │                               │  get_job(job_id)     │                       │
  │                               ├─────────────────────►                       │
  │                               │◄─────────────────────┤                       │
  │  404 unknown job              │                     │                       │
  │  422 if status == failed (returns job_store.error)   │                       │
  │  409 if status not in {done}  │                     │                       │
  │                               │  read result.json     │                       │
  │                               ├───────────────────────────────────────────────►
  │                               │◄───────────────────────────────────────────────┤
  │                               │  mark_result_downloaded(job_id)                │
  │                               ├─────────────────────►                       │
  │  200  { full fidelity report, NaN/Infinity sanitized to null }              │
  ◄───────────────────────────────┤                     │                       │
```

### 7.7 `GET /jobs?status=&limit=` — Dashboard Listing

Straight pass-through to `job_store.list_jobs()`, returns a lightweight array (`job_id, status, created_at, updated_at`) — intended for a jobs dashboard/history table in the frontend, not for the detailed report view.

### 7.8 Background: Periodic Cleanup (not a frontend-triggered request)

Runs automatically every `cleanup_interval_minutes` (default 60) via APScheduler, independent of any HTTP request — but it's part of the complete system workflow because it directly determines how long a frontend user has to call `/jobs/{id}/result` before the data disappears. See Section 10.

---

## 8. The Evaluation Engine — How Scoring Actually Works

### 8.1 The Three Phases, Conceptually

| Phase | Entity granularity | Time-aware? | Example question answered |
|---|---|---|---|
| **Packet Level** | Individual packets, source ports, destination ports | No | "Does the synthetic trace have a realistic number of distinct destination ports, and a realistic packet-length distribution?" |
| **Flow Level — Stateless** | Source IP, destination IP, IP pairs, 5-tuple flows | No | "Does each source IP talk to a realistic number of distinct destinations, and send a realistic byte volume?" |
| **Flow Level — Stateful** | Same entities as above | **Yes** — uses inter-packet gap (`LAG()`) tables | "Are the *timing dynamics* realistic — how bursty is each flow, how long do flows last, how variable is the send rate?" |

### 8.2 Per-Query Execution Contract

Every one of the 70+ query definitions is executed identically by `BaseRunner.run_query`:

1. Format the query's SQL template with `real_packets` (or a real gap table), execute, fetch as a pandas DataFrame.
2. Repeat with `synthetic_packets` (or the synthetic gap table).
3. For each metric name listed against that query, call `MetricRunner.compute(metric_name, real_df, synth_df)`.
4. Metric functions compare the two DataFrames using one of the distance functions in Section 5.12 and return a normalized score + a chart-ready visualization payload.
5. Everything is wrapped so a single SQL typo or a single metric edge case (e.g. divide-by-zero on an empty dataset) degrades to a recorded failure — never a crashed job.

### 8.3 Aggregation — From ~135 Raw Scores to a Report

`ReportGenerator.generate()` runs once **per phase** (packet / stateless / stateful), producing three separate reports, each with:

- `overall` (mean/median/min/max/std/count),
- `percentiles` (13 percentile bands),
- `by_category` (grouped by metric name prefix),
- `by_metric_type` (grouped by `distribution` / `topnkey` / `topnvalue` / `other`),
- `best_5` / `worst_5` individual metrics,
- `failed` / `failed_count`.

Then, at the top level, `EvaluationController`/`ParallelEvaluationController` combines the three phases' `overall.avg` scores into a single **RMS (root-mean-square)** headline number (`overallRMS`) — RMS rather than a plain average because it penalizes any one phase performing badly more than a simple mean would, which is a deliberate choice to surface "one category is way off" rather than letting it be smoothed away by two good categories.

The final JSON persisted to `outputs/result.json` (and returned by `GET /jobs/{id}/result`) has this top-level shape:

```json
{
  "mode": "parallel",
  "packet": [ /* 29 raw per-query results */ ],
  "packet_report": { /* ReportGenerator output for packet phase */ },
  "flow_stateless": [ /* 21 raw per-query results */ ],
  "stateless_report": { /* ... */ },
  "flow_stateful": [ /* 21 raw per-query results */ ],
  "statefull_report": { /* ... */ },
  "overallRMS": 0.1234,
  "packet_time": 2.31,
  "less_time": 1.02,
  "full_time": 3.87,
  "overallTime": 3.9
}
```

---

## 9. Concurrency & Parallelism Design

The system layers **three independent levels of parallelism**, each solving a different bottleneck:

```
Level 1 — Phase-level (3-way)
   ThreadPoolExecutor(max_workers=3) in ParallelEvaluationController
   packet-phase | stateless-phase | stateful-phase   — run concurrently,
   each on its OWN read-only DuckDB connection.

Level 2 — Query-level (up to 8-way per phase)
   ThreadPoolExecutor(max_workers=QUERY_WORKERS=8) inside BaseRunner.run_all
   Within one phase, up to 8 of that phase's queries execute concurrently,
   each on its own cursor() off the phase's shared connection.

Level 3 — Ingestion-level (2-way)
   ThreadPoolExecutor(max_workers=2) inside JobExecutor._ingest
   The real-trace gap tables and synthetic-trace gap tables are built
   concurrently (two independent cursors on the single ingestion connection).
```

**Why this is safe**: DuckDB releases Python's GIL during query execution (it's implemented in C++), so multiple threads genuinely execute SQL in parallel rather than fighting over the interpreter lock. The critical correctness rule the code follows throughout: **only one read-write connection is ever open on a job's database at a time** (during ingestion), and **evaluation only ever opens read-only connections**, of which DuckDB permits many concurrently. This is why `evaluate.py` explicitly rejects a second `/evaluate` call while a job is `queued`/`running` — that's the one scenario that could create two simultaneous writers.

**Worker count math for the parallel path**: 3 phases × up to 8 queries = up to 24 concurrent SQL executions at peak, bounded by `QUERY_WORKERS = 8` inside each phase and 3 phase-threads outer. This is a deliberate, tunable constant (`QUERY_WORKERS` in `evaluation_controller_parallel.py`) rather than something scaled dynamically off CPU count — a reasonable, simple default for a single-instance deployment.

---

## 10. Storage Layout & Cleanup Policy

Every job gets an isolated directory: `storage/jobs/{job_id}/{uploads,database,outputs,logs}/`. This isolation means jobs can never interfere with each other's data, and deleting a job is a single `shutil.rmtree()`.

**Retention policy** (`app/services/job/cleanup.py`, run every `cleanup_interval_minutes`, default 60 min) — a job is deleted if **any** of the following is true:

| Condition | Default threshold |
|---|---|
| Status `failed`, and `completed_at` was more than `cleanup_failed_after_hours` ago | 24 hours |
| Status `done`, and `completed_at` was more than `cleanup_done_after_days` ago | 1 day (per shipped `.env`) |
| Status is `created` / `uploading` / `queued` / `running`, and `updated_at` hasn't changed in more than `cleanup_abandoned_after_hours` | 24 hours |

Deletion order is deliberate: **files first, database row second**. If the process crashes mid-sweep, a partially-cleaned job just looks "abandoned" again on the next pass (self-healing) rather than becoming an orphaned file tree with no matching metadata row that no future query could ever find again. One job's delete failure (e.g. a locked file handle) is caught and logged without aborting the rest of the sweep — same fault-isolation philosophy used throughout the evaluation engine.

---

## 11. Configuration Reference

All configuration is environment-driven via `.env`, prefix `BENCHMARK_`, loaded once into a shared `Settings` singleton (`app/core/config.py`). Shipped `.env` values:

```
BENCHMARK_STORAGE_BASE_DIR=storage/jobs
BENCHMARK_JOB_DB_PATH=storage/job_metadata.db

BENCHMARK_MAX_UPLOAD_MB=2048

BENCHMARK_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

BENCHMARK_CLEANUP_FAILED_AFTER_HOURS=24
BENCHMARK_CLEANUP_DONE_AFTER_DAYS=1
BENCHMARK_CLEANUP_ABANDONED_AFTER_HOURS=24
BENCHMARK_CLEANUP_INTERVAL_MINUTES=60
```

To point the frontend at a different origin, or to run in production behind a reverse proxy on a different domain, only `BENCHMARK_CORS_ORIGINS` needs to change — no code edits.

---

## 12. Error-Handling Philosophy

This codebase applies **fault isolation at every layer**, consistently, which is worth calling out explicitly as an architectural principle rather than an accident:

1. **Metric-level**: `MetricRunner.compute()` never raises — a broken metric function becomes one `"status": "error"` entry.
2. **Query-level**: `BaseRunner.run_query()` never raises — a broken SQL query becomes one failed query entry, the rest of that phase's queries still run.
3. **Phase-level**: each phase (packet/stateless/stateful) is independent — a systemic problem in one phase's queries doesn't prevent the other two phases from completing and being reported.
4. **Job-level**: `JobExecutor.run`/`run_parallel` wrap the *entire* pipeline in a try/except — any escaping exception marks the job `failed` with a structured error message rather than leaving it silently stuck.
5. **Cleanup-level**: one job's deletion failure doesn't stop the sweep from processing the rest of the batch.

The result: a corrupted CSV, a single bad row, a DuckDB edge case, or a numpy division-by-zero anywhere in ~135 metric functions can only ever cost you *that one number* in the final report — never the whole evaluation run.

---

## 13. Full API Reference

| Method & Path | Purpose | Success | Key errors |
|---|---|---|---|
| `GET /` | Liveness banner | 200 | — |
| `GET /health` | Health check | 200 `{"status":"healthy"}` | — |
| `POST /create-job` | Reserve a new job ID + directory skeleton | 200 `{"job_id"}` | — |
| `POST /upload-real/{job_id}` | Upload the real-trace CSV | 200 | 404 unknown job · 400 not .csv · 413 too large |
| `POST /upload-synthetic/{job_id}` | Upload the synthetic-trace CSV | 200 | 404 · 400 · 413 |
| `POST /evaluate/{job_id}` | Start sequential evaluation (background) | 200 `{"status":"queued"}` | 404 · 400 missing CSVs · 409 already queued/running |
| `POST /evaluate/parallel/{job_id}` | Start parallel evaluation (background, production default) | 200 `{"status":"queued"}` | 404 · 400 · 409 |
| `GET /jobs/{job_id}/status` | Poll job lifecycle state | 200 | 404 unknown job |
| `GET /jobs/{job_id}/result` | Fetch the finished fidelity report | 200 (full JSON report) | 404 · 422 job failed · 409 not finished · 500 result file missing |
| `GET /jobs?status=&limit=` | List jobs (dashboard) | 200 `[{job_id,status,created_at,updated_at}]` | — |

**Typical frontend integration sequence:**
`create-job` → `upload-real` → `upload-synthetic` → `evaluate/parallel` → poll `status` until `done`/`failed` → `result`.

---

## 14. Design Decisions — Trade-offs Explained

| Decision | Alternative considered | Why this choice |
|---|---|---|
| DuckDB per-job embedded file, not a shared Postgres | A shared analytical DB (Postgres, ClickHouse) | Each job uses a separate DuckDB file, preventing conflicts between concurrent users, avoiding the accumulation of tables in a shared database, and simplifying data isolation and cleanup. |
| SQLite for job metadata, DuckDB for job data | One database for everything | Separates transactional metadata from analytical data, allowing each workload to use the database best suited to its access pattern. |
| Background Tasks + threads, not Celery/RQ | Dedicated task queue with a broker (Redis/RabbitMQ) | Provides asynchronous background job execution for a single-instance deployment without requiring a message broker or worker infrastructure. |
| Polling (`GET /status`) instead of WebSockets | Server-Sent Events / WebSocket push | Polling provides sufficient responsiveness for long-running jobs while avoiding the complexity of maintaining persistent WebSocket or SSE connections. |
| Sequential AND parallel evaluation controllers both kept | Delete the sequential path once parallel works | The sequential path is explicitly kept as a "known-correct, deterministic" fallback for debugging and for environments where thread-pool DuckDB access is a concern — a pragmatic reliability decision, not dead code. |

---

## 15. Known Limitations & Suggested Improvements

1. **No authentication/authorization** on any endpoint — The current implementation does not authenticate users or restrict access to API endpoints. Any client can submit jobs and, if a valid job ID is known, retrieve the corresponding results. While UUID4 job IDs make unauthorized discovery unlikely, they should not be considered a security mechanism. A production deployment should implement authentication and authorization to ensure that users can access only their own jobs.
2. **No validation of CSV schema/content** beyond the file extension — a `.csv` file missing required columns (`time`, `pkt_len`, `srcip`, etc.) will fail deep inside ingestion or evaluation rather than being rejected immediately at upload with a clear message.
3. **`parquet_converter.py` is currently dead code** — implemented but never called from the live request path; either it's for a planned feature or can be removed/documented as "future use."
4. **No request-level rate limiting** on `/create-job` or the upload endpoints — a client could create unbounded jobs/directories between cleanup sweeps (bounded only by disk space and the 24-hour "abandoned" cleanup window).
5. **No progress reporting within a running job** — `status` is a single flat `running` state; a job evaluating a very large CSV gives the frontend no indication of *which phase* is currently executing or an ETA, only "still running."

---