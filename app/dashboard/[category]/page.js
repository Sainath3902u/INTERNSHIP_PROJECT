'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import QueryTable from '../../../components/QueryTable';

export default function CategoryPage() {
  const params = useParams();
  const categoryKey = params.category; // e.g., 'packet_level', 'flow_stateless'

  const [liveCategoryData, setLiveCategoryData] = useState(null);

  // Map the URL path slug to the exact keys returned by the backend payload
  const reportKeyMap = {
    packet_level: { key: 'packet', label: 'Packet Level Metrics' },
    flow_stateless: { key: 'flow_stateless', label: 'Flow Stateless Metrics' },
    flow_stateful: { key: 'flow_stateful', label: 'Flow Stateful Metrics' }
  };

  useEffect(() => {
    const savedData = localStorage.getItem('syntheticEvalData');
    if (savedData) {
      const parsed = JSON.parse(savedData);
      
      const targetConfig = reportKeyMap[categoryKey];

      if (targetConfig) {
        const report = parsed[targetConfig.key];

        if (report) {
          const queries = Array.isArray(report)
            ? report
            : (report.queries || []);

          const flattenedMetrics = queries.flatMap(query =>
            (query.metrics || []).map((metric, index) => ({
              ...metric,
              query_id: query.query_id,
              query_description: query.query_description,
              query_section: query.query_section,
              sql: query.sql,
              query_exec_time_sec: query.query_exec_time_sec,
              unique_id: `${query.query_id}-${metric.metric}-${index}`
            }))
          );

          setLiveCategoryData({
            name: targetConfig.label,
            queries: flattenedMetrics
          });
        }
      }
    }
  }, [categoryKey]);

  if (!liveCategoryData) {
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
        <span className="text-slate-900 font-semibold dark:text-white">{liveCategoryData.name}</span>
      </nav>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4 dark:border-slate-800">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white">{liveCategoryData.name}</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Granular query verification blocks mapped inside this sector.</p>
        </div>
      </div>

      {/*table block*/}
      <QueryTable queries={liveCategoryData.queries} categoryKey={categoryKey} />
    </div>
  );
}