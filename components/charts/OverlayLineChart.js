'use client';

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

export default function OverlayLineChart({
  chartData,
  xAxisLabel = 'Bucket',
}) {
  const labels = chartData.labels ?? chartData.x_axis ?? [];

  if (!labels.length) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        No distribution data available.
      </div>
    );
  }

  const data = labels.map((bucket, idx) => ({
    bucket,
    real: chartData.real[idx],
    synthetic: chartData.synthetic[idx],
  }));

  return (
    <div className="w-full h-[500px] bg-white p-4 rounded-xl border border-slate-100 dark:bg-slate-900 dark:border-slate-800">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 40,
          }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#334155"
          />

          <XAxis
            dataKey="bucket"
            tick={{ fill: '#94A3B8', fontSize: 12 }}
            axisLine={{ stroke: '#475569' }}
            tickLine={{ stroke: '#475569' }}
            label={{
              value: xAxisLabel,
              position: 'insideBottom',
              offset: -10,
              fill: '#94A3B8',
            }}
          />

          <YAxis
            tick={{ fill: '#94A3B8', fontSize: 12 }}
            axisLine={{ stroke: '#475569' }}
            tickLine={{ stroke: '#475569' }}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            label={{
              value: 'Probability',
              angle: -90,
              position: 'insideLeft',
              fill: '#94A3B8',
            }}
          />

          <Tooltip
            formatter={(value, name) => [
              `${(value * 100).toFixed(2)}%`,
              name,
            ]}
            labelFormatter={(label) => `${xAxisLabel}: ${label}`}
            contentStyle={{
              backgroundColor: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
          />

          <Legend />

          <Line
            type="monotone"
            dataKey="real"
            name="Real"
            stroke="#FF6B6B"
            strokeWidth={3}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />

          <Line
            type="monotone"
            dataKey="synthetic"
            name="Synthetic"
            stroke="#00E5FF"
            strokeWidth={3}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}