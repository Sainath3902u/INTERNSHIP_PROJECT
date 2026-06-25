import Link from 'next/link';
import { getScoreColor, formatScore } from '../utils/helpers';

export default function QueryTable({ queries, categoryKey }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <table className="w-full border-collapse text-left text-sm text-slate-500 dark:text-slate-400">
        <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-600 dark:bg-slate-800/50 dark:text-slate-300">
          <tr>
            <th className="px-6 py-4">Query Operation</th>
            <th className="px-6 py-4">Abbr.</th>
            <th className="px-6 py-4">Distance Metric</th>
            <th className="px-6 py-4">Quality Status</th>
            <th className="px-6 py-4 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
          {queries.map((query) => {
            const colors = getScoreColor(query.distance_score);
            return (
              <tr key={query.id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/30 transition-colors">
                <td className="px-6 py-4 font-semibold text-slate-900 dark:text-white">
                  {query.name}
                </td>
                <td className="px-6 py-4 font-mono text-xs text-slate-500">
                  {query.abbreviation}
                </td>
                <td className="px-6 py-4 font-mono font-medium text-slate-900 dark:text-slate-100">
                  {formatScore(query.distance_score)}
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium border ${colors.border} ${colors.bg} ${colors.text}`}>
                    {colors.label}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <Link 
                    href={`/dashboard/${categoryKey}/${query.id}`}
                    className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50 hover:text-indigo-600 transition-all dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-white"
                  >
                    View Details
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}