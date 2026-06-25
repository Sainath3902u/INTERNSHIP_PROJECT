'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { mockData } from '../../../services/mockData';
import QueryTable from '../../../components/QueryTable';

export default function CategoryPage() {
  const params = useParams();
  const categoryKey = params.category;
  const currentCategory = mockData[categoryKey];

  
  if (!currentCategory) {
    return (
      <div className="text-center py-20 space-y-4">
        <h2 className="text-2xl font-bold text-slate-800">Target Segment Not Found</h2>
        <Link href="/dashboard" className="text-indigo-600 underline">Return to main dashboard</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/*Navigation */}
      <nav className="text-sm font-medium text-slate-500 dark:text-slate-400 flex items-center gap-2">
        <Link href="/dashboard" className="hover:text-indigo-600 transition-colors">Dashboard</Link>
        <span>&gt;</span>
        <span className="text-slate-900 font-semibold dark:text-white">{currentCategory.name}</span>
      </nav>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4 dark:border-slate-800">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white">{currentCategory.name}</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Granular query verification blocks mapped inside this sector.</p>
        </div>
      </div>

      {/*table block*/}
      <QueryTable queries={currentCategory.queries} categoryKey={categoryKey} />
    </div>
  );
}