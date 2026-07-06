'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import ComparisonChart from '../../../../components/ComparisonChart';
import { formatScore, getScoreColor } from '../../../../utils/helpers';

export default function QueryDetailPage() {
  const params = useParams();
  const { category, queryId } = params;

  const [selectedCategory, setSelectedCategory] = useState(null);
  const [queryMetric, setQueryMetric] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('syntheticEvalData');

    if (!stored) return;

    const data = JSON.parse(stored);

    const categoryMap = {
      packet_level: 'packet',
      flow_stateful: 'flow_stateful',
      flow_stateless: 'flow_stateless',
    };

    const categoryData = data[categoryMap[category]] || [];

    const flattenedMetrics = categoryData.flatMap(query =>
      (query.metrics || []).map((metric, index) => ({
        ...metric,
        query_id: query.query_id,
        query_description: query.query_description,
        query_section: query.query_section,
        sql: query.sql,
        unique_id: `${query.query_id}-${metric.metric}-${index}`
      }))
    );

    setSelectedCategory({
      name: category.replace(/_/g, ' '),
      queries: flattenedMetrics,
    });

    const metric = flattenedMetrics.find(
      item => item.unique_id === queryId
    );
    
    setQueryMetric(metric);
  }, [category, queryId]);

  if (!queryMetric) {
    return (
      <div className="text-center py-20 space-y-4">
        <h2 className="text-2xl font-bold text-slate-800">
          Analytical Metrics Missing
        </h2>

        <Link
          href="/dashboard"
          className="text-indigo-600 hover:text-indigo-700"
        >
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const metricData = queryMetric.metric?.[0] ?? {};
  
  const metricName = queryMetric.metric
    ? queryMetric.metric
        .replace(/_+/g, ' ')
        .trim()
        .replace(/\b\w/g, c => c.toUpperCase())
    : 'Unknown Metric';
  
  const score = queryMetric.score ?? 0;
  const visualization = queryMetric.visualization ?? null;

  const colorProfile = getScoreColor(score);

  return (
    <div className="space-y-8">
      {/* Navigation */}
      <nav className="text-sm font-medium text-slate-500 dark:text-slate-400 flex items-center gap-2">
        <Link
          href="/dashboard"
          className="hover:text-indigo-600 transition-colors"
        >
          Dashboard
        </Link>

        <span>&gt;</span>

        <Link
          href={`/dashboard/${category}`}
          className="hover:text-indigo-600 transition-colors"
        >
          {selectedCategory?.name}
        </Link>

        <span>&gt;</span>

        <span className="text-slate-900 font-semibold dark:text-white">
          {queryMetric.query_id}
        </span>
      </nav>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between p-6 bg-white border border-slate-100 rounded-xl gap-4 dark:bg-slate-900 dark:border-slate-800">
        <div>
          <span className="text-xs font-mono font-bold text-indigo-500 uppercase tracking-wider">
            {queryMetric.query_id} Profile
          </span>

          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
            {metricName}
          </h2>
        </div>

        <div className="text-left sm:text-right">
          <span className="text-xs font-semibold text-slate-400 block uppercase tracking-wider">
            Quality Score
          </span>

          <span className={`text-3xl font-black ${colorProfile.text}`}>
            {formatScore(score)}
          </span>
        </div>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Side */}
        <div className="space-y-4 flex flex-col justify-between">
          {/* SQL Block */}
          <div className="bg-white border border-slate-100 p-6 rounded-xl dark:bg-slate-900 dark:border-slate-800 space-y-4 flex-1">
            <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400">
              DuckDB Target Query Formula
            </h4>

            <div className="relative rounded-lg overflow-hidden bg-slate-950 p-4 border border-slate-800">
              <pre className="text-xs font-mono text-emerald-400 whitespace-pre-wrap break-all leading-relaxed">
                <code>{queryMetric.sql}</code>
              </pre>
            </div>
          </div>

          {/* Description */}
          <div className="mt-4 space-y-4 border-t border-slate-200 dark:border-slate-700 pt-4">
            <div className="bg-white border border-slate-200 p-6 rounded-xl dark:bg-slate-900 dark:border-slate-800">
              <h4 className="text-sm font-bold uppercase tracking-wider text-slate-500">
                Description
              </h4>

              <div className="relative rounded-lg overflow-hidden bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-700 mt-3">
                <p className="text-sm text-slate-900 dark:text-slate-300 leading-relaxed">
                  {queryMetric.query_description}
                </p>
              </div>
            </div>

            {/* Verdict */}
            <div
              className={`p-5 rounded-xl border ${colorProfile.border} ${colorProfile.bg} text-sm space-y-1`}
            >
              <span className="font-bold text-slate-900 dark:text-slate-200 block">
                Quality Analysis Verdict:
              </span>

              <p className="text-slate-600 dark:text-slate-400">
                This sub-section notes an index error of{' '}
                <span className="font-semibold">
                  {formatScore(score)}
                </span>
                . This tells us the synthesis output functions with an{' '}
                <span className="font-bold">
                  {colorProfile.label}
                </span>{' '}
                status rating.
              </p>
            </div>
          </div>
        </div>

        {/* Right Side - Visualization */}
        <div className="space-y-2">
          <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400 pl-1">
            Side-by-Side Distribution Mapping
          </h4>

          {visualization ? (
            <ComparisonChart chartData={visualization} />
          ) : (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center text-slate-500">
              No visualization data available.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}