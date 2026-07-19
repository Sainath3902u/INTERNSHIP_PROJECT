'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

// How often to poll job status, and how long to wait before giving up.
// The backend runs evaluation in the background now,
// so the frontend can no longer assume one blocking request returns the
// result - it has to ask "are we done yet?" until the job reaches a
// terminal state (done/failed).
const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes

const STATUS_LABELS = {
  creating: 'Creating job...',
  uploading: 'Uploading datasets...',
  queued: 'Queued for evaluation...',
  running: 'Running analytical models...',
  done: 'Done!',
};

export default function UploadForm() {
  const router = useRouter();

  const [realFile, setRealFile] = useState(null);
  const [syntheticFile, setSyntheticFile] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [statusLabel, setStatusLabel] = useState('');

  const timedFetch = async (url, options, label) => {
    const start = performance.now();

    const response = await fetch(url, options);

    const end = performance.now();
    const latencySeconds = ((end - start) / 1000).toFixed(2);
    console.log(`${label}: ${latencySeconds} s`);

    return response;
  };

  // Poll GET /jobs/{job_id}/status until it reaches "done" or "failed".
  // Throws on failure (with the backend's error message) or on timeout,
  // so the caller's existing try/catch handles both the same way it
  // already handles upload/network errors.
  const waitForJobCompletion = async (backendUrl, jobId) => {
    const deadline = performance.now() + POLL_TIMEOUT_MS;

    while (performance.now() < deadline) {
      const statusResponse = await fetch(`${backendUrl}/jobs/${jobId}/status`);

      if (!statusResponse.ok) {
        throw new Error('Lost track of the job while checking status.');
      }

      const { status, error } = await statusResponse.json();

      if (status === 'failed') {
        throw new Error(error || 'Evaluation failed.');
      }

      if (status === 'done') {
        return;
      }

      setStatusLabel(STATUS_LABELS[status] ?? STATUS_LABELS.running);

      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
    }

    throw new Error('Evaluation is taking longer than expected. Please try again shortly.');
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();

    if (!realFile || !syntheticFile) {
      alert('Please select both CSV files.');
      return;
    }

    setIsSimulating(true);
    setStatusLabel(STATUS_LABELS.creating);

    const workflowStart = performance.now();

    try {
      const backendUrl =
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // Create Job
      const jobResponse = await timedFetch(
        `${backendUrl}/create-job`,
        {
          method: 'POST',
        },
        'Create Job'
      );

      if (!jobResponse.ok) {
        throw new Error('Failed to create job.');
      }

      const { job_id } = await jobResponse.json();

      // Upload Real Dataset
      setStatusLabel(STATUS_LABELS.uploading);

      const realForm = new FormData();
      realForm.append('file', realFile);

      console.log(
        `Real file: ${realFile.name} (${(
          realFile.size /
          1024 /
          1024
        ).toFixed(2)} MB)`
      );

      const realResponse = await timedFetch(
        `${backendUrl}/upload-real/${job_id}`,
        {
          method: 'POST',
          body: realForm,
        },
        'Upload Real Dataset'
      );

      if (!realResponse.ok) {
        throw new Error('Real upload failed.');
      }

      // Upload Synthetic Dataset
      const syntheticForm = new FormData();
      syntheticForm.append('file', syntheticFile);

      console.log(
        `Synthetic file: ${syntheticFile.name} (${(
          syntheticFile.size /
          1024 /
          1024
        ).toFixed(2)} MB)`
      );

      const syntheticResponse = await timedFetch(
        `${backendUrl}/upload-synthetic/${job_id}`,
        {
          method: 'POST',
          body: syntheticForm,
        },
        'Upload Synthetic Dataset'
      );

      if (!syntheticResponse.ok) {
        throw new Error('Synthetic upload failed.');
      }

      // Trigger evaluation. The backend enqueues this and returns
      // immediately with {status: "queued"} - it does NOT return the
      // result anymore, so this request is fast regardless of dataset
      // size. The actual evaluation happens in the background; we find
      // out it's done via polling below.
      const evalResponse = await timedFetch(
        `${backendUrl}/evaluate/parallel/${job_id}`,
        {
          method: 'POST',
        },
        'Queue Evaluation'
      );

      if (!evalResponse.ok) {
        const body = await evalResponse.json().catch(() => ({}));
        throw new Error(body.detail || 'Failed to start evaluation.');
      }

      // Poll until the job finishes (or throws on failure/timeout).
      setStatusLabel(STATUS_LABELS.queued);
      await waitForJobCompletion(backendUrl, job_id);

      // Now that status is "done", fetch the actual result.
      const resultResponse = await timedFetch(
        `${backendUrl}/jobs/${job_id}/result`,
        { method: 'GET' },
        'Fetch Result'
      );

      if (!resultResponse.ok) {
        throw new Error('Evaluation finished, but the result could not be retrieved.');
      }

      const result = await resultResponse.json();

      localStorage.setItem('job_id', job_id);

      localStorage.setItem(
        'syntheticEvalData',
        JSON.stringify(result)
      );

      const workflowEnd = performance.now();

      console.log(
        `Total Workflow Time: ${(
          (workflowEnd - workflowStart) / 1000
        ).toFixed(2)} s`
      );

      setIsSimulating(false);

      router.push('/dashboard');
    } catch (error) {
      const workflowEnd = performance.now();

      console.error('Connection Error:', error);

      console.log(
        `Workflow Failed After: ${(
          workflowEnd - workflowStart
        ).toFixed(2)} ms`
      );

      setIsSimulating(false);
      setStatusLabel('');

      alert(`Failed to analyze datasets: ${error.message}`);
    }
  };

  return (
    <form
      onSubmit={handleFormSubmit}
      className="w-full max-w-2xl space-y-6 bg-white p-8 rounded-2xl shadow-sm border border-slate-100 dark:bg-slate-800 dark:border-slate-700"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Real Input */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">
            Target Real Dataset (CSV)
          </label>

          <div className="relative flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-500 transition-colors dark:border-slate-600 bg-slate-50/50 dark:bg-slate-900/50">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setRealFile(e.target.files?.[0] || null)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />

            <span className="text-sm text-slate-500 dark:text-slate-400">
              {realFile
                ? `✅ ${realFile.name}`
                : 'Drop or browse real data'}
            </span>
          </div>
        </div>

        {/* Synthetic Input */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">
            Generated Synthetic Dataset (CSV)
          </label>

          <div className="relative flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-500 transition-colors dark:border-slate-600 bg-slate-50/50 dark:bg-slate-900/50">
            <input
              type="file"
              accept=".csv"
              onChange={(e) =>
                setSyntheticFile(e.target.files?.[0] || null)
              }
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />

            <span className="text-sm text-slate-500 dark:text-slate-400">
              {syntheticFile
                ? `✅ ${syntheticFile.name}`
                : 'Drop or browse synthetic data'}
            </span>
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={!realFile || !syntheticFile || isSimulating}
        className="w-full py-3 px-4 rounded-xl text-white font-medium bg-indigo-600 hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md shadow-indigo-100 dark:shadow-none"
      >
        {isSimulating ? (
          <>
            <svg
              className="animate-spin h-5 w-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />

              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>

            {statusLabel || 'Working...'}
          </>
        ) : (
          'Analyze Datasets'
        )}
      </button>
    </form>
  );
}