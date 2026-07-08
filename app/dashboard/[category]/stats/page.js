'use client';

import { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function CategoryStatsPage() {
  const params = useParams();
  const categoryKey = params.category; 

  const [liveCategoryData, setLiveCategoryData] = useState(null);

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
          const queries = Array.isArray(report) ? report : (report.queries || []);
          const flattenedMetrics = queries.flatMap(query =>
            (query.metrics || []).map((metric, index) => ({
              ...metric,
              query_id: query.query_id,
              query_section: query.query_section || query.query_id?.split('_').slice(0, 2).join('_') || 'unknown',
              unique_id: `${query.query_id}-${metric.metric}-${index}`
            }))
          );
          setLiveCategoryData({ name: targetConfig.label, queries: flattenedMetrics });
        }
      }
    }
  }, [categoryKey]);

  const stats = useMemo(() => {
    if (!liveCategoryData || !liveCategoryData.queries.length) return null;

    const scores = liveCategoryData.queries
      .map(q => parseFloat(q.value ?? q.score ?? q.distance ?? 0))
      .filter(val => !isNaN(val))
      .sort((a, b) => a - b);

    if (scores.length === 0) return null;

    const totalMetrics = scores.length;
    const sum = scores.reduce((acc, val) => acc + val, 0);
    const average = sum / totalMetrics;
    
    const mid = Math.floor(totalMetrics / 2);
    const median = totalMetrics % 2 !== 0 ? scores[mid] : (scores[mid - 1] + scores[mid]) / 2;
    const minScore = scores[0];
    const maxScore = scores[totalMetrics - 1];

    const sqDiffs = scores.map(val => Math.pow(val - average, 2));
    const stdDev = Math.sqrt(sqDiffs.reduce((acc, val) => acc + val, 0) / totalMetrics);

    const getPercentile = (p) => {
      const index = (p / 100) * (totalMetrics - 1);
      const low = Math.floor(index);
      const high = Math.ceil(index);
      return low === high ? scores[low] : scores[low] + (index - low) * (scores[high] - scores[low]);
    };

    const percentilesList = [5, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95];
    const percentiles = {};
    percentilesList.forEach(p => { percentiles[p] = getPercentile(p); });

    const byCategoryMap = {};
    const byMetricMap = {};

    liveCategoryData.queries.forEach(q => {
      const val = parseFloat(q.value ?? q.score ?? q.distance ?? 0);
      if (isNaN(val)) return;

      const sec = q.query_section || 'General';
      if (!byCategoryMap[sec]) byCategoryMap[sec] = [];
      byCategoryMap[sec].push(val);

      const type = q.metric || 'other';
      if (!byMetricMap[type]) byMetricMap[type] = [];
      byMetricMap[type].push(val);
    });

    const aggregateGroup = (map) => {
      return Object.keys(map).map(key => {
        const arr = map[key].sort((a, b) => a - b);
        return {
          name: key,
          avg: arr.reduce((a, b) => a + b, 0) / arr.length,
          min: arr[0],
          max: arr[arr.length - 1],
          count: arr.length
        };
      });
    };

    const sortedQueries = [...liveCategoryData.queries].sort((a, b) => {
      const valA = parseFloat(a.value ?? a.score ?? a.distance ?? 0);
      const valB = parseFloat(b.value ?? b.score ?? b.distance ?? 0);
      return valA - valB;
    });

    return {
      average, median, minScore, maxScore, stdDev, totalMetrics, percentiles,
      byCategory: aggregateGroup(byCategoryMap),
      byMetricType: aggregateGroup(byMetricMap),
      bestFive: sortedQueries.slice(0, 5),
      worstFive: sortedQueries.slice(-5).reverse()
    };
  }, [liveCategoryData]);

  if (!liveCategoryData || !stats) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold text-slate-800">Calculating Statistics...</h2>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 py-6">
    
      <nav className="text-sm font-medium text-slate-500 flex items-center gap-2">
        <Link href="/dashboard" className="hover:text-indigo-600">Dashboard</Link>
        <span>&gt;</span>
        <Link href={`/dashboard/${categoryKey}`} className="hover:text-indigo-600">{liveCategoryData.name}</Link>
        <span>&gt;</span>
        <span className="text-slate-900 font-semibold">Analytical Statistics</span>
      </nav>

      <div className="border-b border-slate-100 pb-4 flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900">{liveCategoryData.name} Statistics</h2>
          <p className="text-sm text-slate-500">Aggregated fidelity performance logs baseline distributions.</p>
        </div>
        <Link href={`/dashboard/${categoryKey}`} className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-xl text-sm font-medium transition-colors">
          View Raw Metric Entries
        </Link>
      </div>

      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-slate-900 border-b border-slate-100 pb-2">Overall Summary</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-50 p-3 rounded-xl">
              <p className="text-xs text-slate-500 font-medium">Average</p>
              <p className="text-xl font-bold text-indigo-600">{stats.average.toFixed(4)}</p>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <p className="text-xs text-slate-500 font-medium">Median</p>
              <p className="text-xl font-bold text-slate-800">{stats.median.toFixed(4)}</p>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <p className="text-xs text-slate-500 font-medium">Min</p>
              <p className="text-xl font-bold text-emerald-600">{stats.minScore.toFixed(4)}</p>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <p className="text-xs text-slate-500 font-medium">Max</p>
              <p className="text-xl font-bold text-rose-600">{stats.maxScore.toFixed(4)}</p>
            </div>
          </div>
          <div className="pt-2 text-xs text-slate-500 font-medium flex justify-between">
            <span>Std Dev: <b>{stats.stdDev.toFixed(4)}</b></span>
            <span>Count: <b>{stats.totalMetrics}</b></span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-bold text-slate-900 border-b border-slate-100 pb-2 mb-4">Percentile Distribution</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Object.keys(stats.percentiles).map((p) => (
              <div key={p} className="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg">
                <span className="text-xs font-semibold text-slate-500">{p}th</span>
                <span className="text-sm font-mono font-bold text-slate-700">{stats.percentiles[p].toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        
        <div className="space-y-6">
          
          <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-3">By Domain Subcategory</h3>
            <div className="space-y-2.5">
              {stats.byCategory.map((cat) => (
                <div key={cat.name} className="p-3 bg-slate-50 rounded-xl">
                  <div className="flex justify-between text-sm font-bold text-indigo-600 mb-1">
                    <span>{cat.name}</span>
                    <span className="text-xs font-medium text-slate-500">Count: {cat.count}</span>
                  </div>
                  <div className="grid grid-cols-3 text-xs text-slate-500 font-mono">
                    <div>Avg: <b>{cat.avg.toFixed(4)}</b></div>
                    <div>Min: <b>{cat.min.toFixed(4)}</b></div>
                    <div>Max: <b>{cat.max.toFixed(4)}</b></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-emerald-50/50 border border-emerald-100 p-6 rounded-2xl">
            <h3 className="text-sm font-bold text-emerald-800 uppercase tracking-wider mb-3">🏆 Best 5 Metrics (Lowest Distance)</h3>
            <div className="divide-y divide-emerald-100">
              {stats.bestFive.map((item) => (
                <div key={item.unique_id} className="py-2 flex justify-between items-center text-sm">
                  <span className="text-slate-600 truncate max-w-[280px]">{item.query_id}</span>
                  <span className="font-mono font-bold text-emerald-600 bg-white px-2 py-0.5 rounded shadow-xs">{(item.value ?? item.score ?? item.distance ?? 0).toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-rose-50/50 border border-rose-100 p-6 rounded-2xl">
            <h3 className="text-sm font-bold text-rose-800 uppercase tracking-wider mb-3">⚠️ Worst 5 Metrics (Highest Distance)</h3>
            <div className="divide-y divide-rose-100">
              {stats.worstFive.map((item) => (
                <div key={item.unique_id} className="py-2 flex justify-between items-center text-sm">
                  <span className="text-slate-600 truncate max-w-[280px]">{item.query_id}</span>
                  <span className="font-mono font-bold text-rose-600 bg-white px-2 py-0.5 rounded shadow-xs">{(item.value ?? item.score ?? item.distance ?? 0).toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-3">By Evaluation Metric Type</h3>
            <div className="space-y-2.5">
              {stats.byMetricType.map((m) => (
                <div key={m.name} className="p-3 bg-slate-50 rounded-xl">
                  <div className="flex justify-between text-sm font-bold text-slate-800 capitalize mb-1">
                    <span>{m.name}</span>
                    <span className="text-xs font-medium text-slate-500">Count: {m.count}</span>
                  </div>
                  <div className="grid grid-cols-3 text-xs text-slate-500 font-mono">
                    <div>Avg: <b>{m.avg.toFixed(4)}</b></div>
                    <div>Min: <b>{m.min.toFixed(4)}</b></div>
                    <div>Max: <b>{m.max.toFixed(4)}</b></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}