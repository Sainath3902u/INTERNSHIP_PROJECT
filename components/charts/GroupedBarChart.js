'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

export default function CategoryDistributionChart({ chartData }) {

  if (!chartData?.labels?.length) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        No category distribution data available.
      </div>
    );
  }

  const data = chartData.labels.map((label, idx) => ({
    category: label,
    real: chartData.real[idx],
    synthetic: chartData.synthetic[idx],
  }));
  const isTopN = chartData?.flag === 'topn';

  return (
    <div className="w-full h-[500px] bg-white p-4 rounded-xl border border-slate-100 dark:bg-slate-900 dark:border-slate-800">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{
            top: 20,
            right: 30,
            left: 40,
            bottom: 20,
          }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            horizontal={false}
            stroke="#334155"
          />

          <XAxis
            type="number"
            tick={{ fill: '#94A3B8', fontSize: 12 }}
            axisLine={{ stroke: '#475569' }}
            tickLine={{ stroke: '#475569' }}
            tickFormatter={(v) =>
              isTopN
                ? Number(v).toLocaleString()
                : `${(v * 100).toFixed(1)}%`
            }
          />

          <YAxis
            type="category"
            dataKey="category"
            tick={{ fill: '#94A3B8', fontSize: 12 }}
            axisLine={{ stroke: '#475569' }}
            tickLine={{ stroke: '#475569' }}
            width={70}
          />

          <Tooltip
            formatter={(value, name) => [
              isTopN
                ? Number(value).toLocaleString()
                : `${(value * 100).toFixed(2)}%`,
              name,
            ]}
            labelFormatter={(label) => String(label)}
            contentStyle={{
              backgroundColor: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
          />

          <Legend />

          <Bar
            dataKey="real"
            name={isTopN ? "Real" : "Real Distribution"}
            fill="#FF6B6B"
            radius={[0, 4, 4, 0]}
          />

          <Bar
            dataKey="synthetic"
            name={isTopN ? "Synthetic" : "Synthetic Distribution"}
            fill="#00E5FF"
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}