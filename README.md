# NetSynth IQ - Synthetic Data Quality Dashboard

NetSynth IQ is a synthetic network data evaluation platform built with **Next.js, FastAPI, Python, and DuckDB**.

It compares a **real network dataset** against a **synthetic network dataset**, runs the evaluation pipeline locally, and displays the generated quality metrics in an interactive dashboard.

---

## Prerequisites

Before running the project locally, install:

* **Node.js:** v18.0 or higher
* **Python:** v3.10 to v3.14
* **Git:** Latest version

---

## 1. Clone the Repository

Open PowerShell or a terminal:

```bash
git clone https://github.com/Sainath3902u/INTERNSHIP_PROJECT.git
cd INTERNSHIP_PROJECT
```

---

# Running NetSynth IQ

The project has two parts:

```text
Frontend
Next.js
http://localhost:3000

Backend / Evaluation
FastAPI + Python + DuckDB
http://127.0.0.1:8000
```

For the CLI workflow, start the **frontend first**.

The Python CLI will then:

1. Read the real and synthetic CSV files directly from disk.
2. Create an evaluation job.
3. Run the evaluation.
4. Start the FastAPI server.
5. Open the dashboard automatically with the generated `job_id`.

---

## 2. Backend Setup

Open a terminal and navigate to the backend:

```powershell
cd backend
```

### Create a virtual environment

Recommended:

```powershell
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Your terminal should now show something similar to:

```text
(venv) PS ...\INTERNSHIP_PROJECT\backend>
```

### Install Python dependencies

```powershell
pip install -r requirements.txt
```

You only need to do the installation when initially setting up the project or when the requirements change.

---

## 3. Frontend Setup

Open a **separate terminal** from the backend terminal.

Navigate to the project directory:

```powershell
cd path\to\INTERNSHIP_PROJECT
```

Install the Node.js dependencies:

```bash
npm install
```

### Environment configuration

If required, create a `.env.local` file in the project root:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## 4. Start the Frontend

Start the Next.js development server:

```bash
npm run dev
```

The frontend should become available at:

```text
http://localhost:3000
```

Keep this terminal running.

---

# 5. Run an Evaluation from the CLI

Open another terminal and navigate to the backend directory:

```powershell
cd path\to\INTERNSHIP_PROJECT\backend
```

Activate the Python virtual environment if it is not already active:

```powershell
.\venv\Scripts\Activate.ps1
```

Run the evaluation using:

```powershell
python -m app.backend --real "PATH_TO_REAL_CSV" --syn "PATH_TO_SYNTHETIC_CSV"
```

For example:

```powershell
python -m app.backend --real "C:\Users\username\Downloads\Dataset\real.csv" --syn "C:\Users\username\Downloads\Dataset\synthetic.csv"
```

> Run this command from the `backend` directory. Do not run `python backend.py` from inside the `app` directory.

---

## 6. What Happens After Running the Command?

The CLI first validates both CSV files.

It then creates a new evaluation job:

```text
Job created: <job-id>
```

The real and synthetic CSV files are copied into the job's upload directory and the normal NetSynth IQ evaluation pipeline runs.

During processing, the terminal displays progress:

```text
Running evaluation ............
```

After successful completion, you should see output similar to:

```text
Evaluation completed successfully.

Job ID:    550e8400-e29b-41d4-a716-446655440000
Dashboard: http://localhost:3000/dashboard?job_id=550e8400-e29b-41d4-a716-446655440000
API:       http://127.0.0.1:8000  (Ctrl+C to stop)
```

The browser will automatically open the generated dashboard URL.

---

# CLI Workflow

The complete CLI flow is:

```text
real.csv + synthetic.csv
          │
          ▼
   Python CLI command
          │
          ▼
 JobManager.create_job()
          │
          ▼
      job_id created
          │
          ▼
 CSV files copied into
   job upload directory
          │
          ▼
 JobExecutor.run_parallel()
          │
          ▼
    Evaluation runs
          │
          ▼
 Backend stores results
          │
          ▼
   FastAPI server starts
          │
          ▼
Browser automatically opens
          │
          ▼
/dashboard?job_id=<job_id>
          │
          ▼
Frontend reads job_id
          │
          ▼
GET /jobs/<job_id>/result
          │
          ▼
Frontend receives evaluation
          │
          ▼
Result saved to localStorage
          │
          ▼
 Dashboard displays results
```

---

## Why Use CLI Mode?

In the normal browser workflow, CSV files must be uploaded to the backend through HTTP.

CLI mode avoids that unnecessary upload when the datasets already exist on the same machine.

Instead of:

```text
CSV
 ↓
Browser
 ↓
HTTP Upload
 ↓
Backend
```

CLI mode uses:

```text
CSV on disk
 ↓
Backend directly
```

The evaluation logic itself does not change.

CLI mode uses the same:

* `JobManager`
* `JobExecutor`
* Job database
* Evaluation pipeline
* Result format
* FastAPI application
* Dashboard

This means CLI-created jobs behave like regular backend jobs.

---

# Dashboard Job Handoff

After the evaluation finishes, the CLI already knows the generated `job_id`.

It therefore opens:

```text
http://localhost:3000/dashboard?job_id=<job_id>
```

For example:

```text
http://localhost:3000/dashboard?job_id=550e8400-e29b-41d4-a716-446655440000
```

The dashboard extracts the `job_id` and requests:

```text
GET http://127.0.0.1:8000/jobs/<job_id>/result
```

The returned evaluation result is stored using:

```javascript
localStorage.setItem(
  'syntheticEvalData',
  JSON.stringify(resultData)
);
```

This allows the existing dashboard and its category pages to continue using the same data structure as the normal frontend workflow.

---

# Running Without Automatically Opening the Browser

Use the `--no-browser` option:

```powershell
python -m app.backend --real "C:\path\real.csv" --syn "C:\path\synthetic.csv" --no-browser
```

The CLI will still print the dashboard URL.

You can copy and open it manually.

---

# Custom Frontend URL

The default frontend dashboard URL is:

```text
http://localhost:3000/dashboard
```

You can override it:

```powershell
python -m app.backend --real "C:\path\real.csv" --syn "C:\path\synthetic.csv" --frontend-url "http://localhost:3001/dashboard"
```

The CLI automatically appends the generated `job_id`.

---

# Custom Backend Port

The default backend port is:

```text
8000
```

You can change it using:

```powershell
python -m app.backend --real "C:\path\real.csv" --syn "C:\path\synthetic.csv" --port 8080
```

---

# Architecture & Tech Stack

| Component            | Technology               |
| -------------------- | ------------------------ |
| Frontend             | Next.js                  |
| UI                   | React + Tailwind CSS     |
| Charts               | Recharts                 |
| Backend              | FastAPI                  |
| Evaluation           | Python                   |
| Analytics / Queries  | DuckDB                   |
| Scheduling           | APScheduler              |
| Communication        | REST APIs                |
| Local Result Handoff | `job_id` query parameter |

---

# Development Server Mode

If you want to run FastAPI independently for development or API testing, navigate to:

```powershell
cd backend
```

and run:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

> This separate Uvicorn command is **not required for CLI evaluation mode**. The CLI starts the FastAPI application itself after the evaluation finishes.

Also, do not run both commands on port `8000` simultaneously.

---

# Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

Make sure you are running the CLI from the `backend` directory.

Correct:

```text
INTERNSHIP_PROJECT
└── backend
    ├── app
    │   ├── backend.py
    │   └── ...
    └── requirements.txt
```

Run:

```powershell
cd INTERNSHIP_PROJECT\backend
python -m app.backend --real "C:\path\real.csv" --syn "C:\path\synthetic.csv"
```

Do not run:

```powershell
cd backend\app
python backend.py ...
```

---

### `can't open file 'backend.py'`

The CLI file is inside the `app` Python package.

Run it as a module from the backend directory:

```powershell
python -m app.backend --real "C:\path\real.csv" --syn "C:\path\synthetic.csv"
```

---

### `Error: real file not found`

Check that the full path is correct:

```powershell
python -m app.backend --real "C:\Users\username\Downloads\Dataset\real.csv" --syn "C:\Users\username\Downloads\Dataset\synthetic.csv"
```

Use quotes around Windows paths.

---

### `ERR_CONNECTION_REFUSED`

First make sure the Next.js frontend is running:

```bash
npm run dev
```

It should be accessible at:

```text
http://localhost:3000
```

During CLI mode, FastAPI is started automatically after evaluation.

---

### Port 8000 is already in use

You may already have a FastAPI/Uvicorn server running.

Stop the existing server with:

```text
Ctrl+C
```

and run the CLI again.

Alternatively, use another port with `--port`.

---

### Dashboard says no analysis was found

For CLI mode, check that the browser URL contains a `job_id`:

```text
http://localhost:3000/dashboard?job_id=<job_id>
```

The dashboard uses this ID to retrieve the evaluation result from FastAPI.

Also check the browser developer console and Network tab for errors from:

```text
GET /jobs/<job_id>/result
```

---

# Quick Start

After the initial dependency setup, running NetSynth IQ requires only two terminals.

**Terminal 1 — Frontend**

```powershell
cd INTERNSHIP_PROJECT
npm run dev
```

**Terminal 2 — CLI Evaluation**

```powershell
cd INTERNSHIP_PROJECT\backend
.\venv\Scripts\Activate.ps1

python -m app.backend --real "C:\path\to\real.csv" --syn "C:\path\to\synthetic.csv"
```

Then wait for the evaluation to finish.

NetSynth IQ will automatically open:

```text
http://localhost:3000/dashboard?job_id=<generated-job-id>
```

with the evaluation results.
