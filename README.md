
---

```markdown
# NetSynth IQ - Synthetic Data Quality Dashboard

A high-performance evaluation platform and interactive dashboard designed to benchmark the fidelity of synthetic network packet data against real-world production logs using Next.js, FastAPI, and DuckDB.

---

## Prerequisites

Before running the project locally, ensure you have installed:

- **Node.js**: v18.0 or higher ([Download Node.js](https://nodejs.org/))
- **Python**: v3.10 to v3.14 ([Download Python](https://www.python.org/))
- **Git**: Latest version ([Download Git](https://git-scm.com/))

---

## Step 1: Clone the Repository

Open your terminal or PowerShell and run:

```bash
git clone [https://github.com/Sainath3902u/INTERNSHIP_PROJECT.git](https://github.com/Sainath3902u/INTERNSHIP_PROJECT.git)
cd INTERNSHIP_PROJECT

```

---

## Step 2: Set Up and Run the Backend (FastAPI)

Open a terminal window dedicated to the backend service:

1. **Navigate to the backend folder:**
```powershell
cd backend

```

2. **Install backend dependencies:**
```powershell
pip install -r requirements.txt

```

3. **Start the FastAPI backend server:**
```powershell
python -m uvicorn app.main:app --reload --port 8000

```

> **Backend Verification:** Once active, Uvicorn will display `INFO: Uvicorn running on http://127.0.0.1:8000`. You can test API endpoints interactively at [http://127.0.0.1:8000/docs](https://www.google.com/search?q=http://127.0.0.1:8000/docs). Keep this terminal window open and running in the background!

---

## Step 3: Set Up and Run the Frontend (Next.js)

Open a **new, separate terminal window** for the frontend interface:

1. **Navigate to the root directory of the project:**
```powershell
cd path/to/INTERNSHIP_PROJECT

```

2. **Install Node.js dependencies:**
```bash
npm install

```

3. **Configure Environment Variables (Optional):**
Create a `.env.local` file in the root folder with:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000

```

4. **Start the Next.js development server:**
```bash
npm run dev

```

> **Frontend Verification:** Open your browser and navigate to [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000) to view the dashboard.

---

## Architecture & Tech Stack Overview

* **Frontend:** Next.js (App Router), React, Tailwind CSS, Recharts
* **Backend:** FastAPI, Python, DuckDB, APScheduler
* **Communication:** REST APIs over HTTP (`localhost:3000` $\leftrightarrow$ `localhost:8000`)

---

## Troubleshooting

1. ISSUE: uvicorn: The term 'uvicorn' is not recognized...
   CAUSE: System PATH issue in Windows
   SOLUTION: Always use `python -m uvicorn app.main:app --reload --port 8000` to start the server.

2. ISSUE: ModuleNotFoundError: No module named '...'
   CAUSE: Missing Python dependency
   SOLUTION: Run `pip install -r requirements.txt` (or `pip install <package_name>`).

3. ISSUE: ERR_CONNECTION_REFUSED in browser
   CAUSE: Backend server is offline
   SOLUTION: Ensure the backend server is active on port 8000 in a separate terminal window before submitting data in the frontend.
