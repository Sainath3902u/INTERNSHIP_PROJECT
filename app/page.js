import UploadForm from '../components/UploadForm';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center max-w-3xl mx-auto space-y-8">
      <div className="space-y-3">
        <span className="text-xs font-bold uppercase tracking-widest text-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 px-3 py-1.5 rounded-full">
          Network Data Evaluation Engine
        </span>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          NetSynth IQ
        </h1>
        <p className="text-base sm:text-lg text-slate-500 max-w-2xl dark:text-slate-400">
          An interactive dashboard for evaluating synthetic network data by comparing packet- and flow-level metrics with real-world traffic.
        </p>
        <ul className="mt-2 list-disc list-inside text-sm text-slate-700 dark:text-slate-300 space-y-1">
          <li>Each dataset must be less than <strong>50 MB</strong>.</li>
        </ul>
      </div>

      <UploadForm />
    </div>
  );
}