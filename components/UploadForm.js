'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function UploadForm() {
  const router = useRouter();
  const [realFile, setRealFile] = useState(null);
  const [syntheticFile, setSyntheticFile] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);


  const handleFormSubmit = async (e) => {
  e.preventDefault();
  if (!realFile || !syntheticFile) return;

  setIsSimulating(true);

  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // 1. Tell the backend to prepare the datasets inside DuckDB
    const uploadResponse = await fetch(`${backendUrl}/load-datasets`, {
      method: 'POST',
    });

    if (!uploadResponse.ok) {
      throw new Error('Backend failed to load the datasets into DuckDB.');
    }
    const uploadData = await uploadResponse.json();
    console.log('Ingestion success:', uploadData);

    // 2. Trigger the statistical calculations
    const evalResponse = await fetch(`${backendUrl}/evaluate-seq`);
    if (!evalResponse.ok) {
      throw new Error('Backend evaluation metrics calculation failed.');
    }
    const liveEvaluationData = await evalResponse.json();

    // 3. Store the live calculation result into browser storage
    localStorage.setItem('syntheticEvalData', JSON.stringify(liveEvaluationData));

    setIsSimulating(false);
    router.push('/dashboard'); // Go to dashboard page!

  } catch (error) {
    console.error('Connection Error:', error);
    setIsSimulating(false);
    alert(`Failed to analyze datasets: ${error.message}`);
  }
};

  return (
    <form onSubmit={handleFormSubmit} className="w-full max-w-2xl space-y-6 bg-white p-8 rounded-2xl shadow-sm border border-slate-100 dark:bg-slate-800 dark:border-slate-700">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/*Real Input*/}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Target Real Dataset (CSV)</label>
          <div className="relative flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-500 transition-colors dark:border-slate-600 bg-slate-50/50 dark:bg-slate-900/50">
            <input 
              type="file" 
              accept=".csv" 
              onChange={(e) => setRealFile(e.target.files[0])}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {realFile ? `✅ ${realFile.name}` : 'Drop or browse real data'}
            </span>
          </div>
        </div>

        {/* Synthetic Inpu */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Generated Synthetic Dataset (CSV)</label>
          <div className="relative flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-500 transition-colors dark:border-slate-600 bg-slate-50/50 dark:bg-slate-900/50">
            <input 
              type="file" 
              accept=".csv" 
              onChange={(e) => setSyntheticFile(e.target.files[0])}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {syntheticFile ? `✅ ${syntheticFile.name}` : 'Drop or browse synthetic data'}
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
            <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            Running Analytical Models...
          </>
        ) : 'Analyze Datasets'}
      </button>
    </form>
  );
}
