'use client';

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';

export default function RankShareChart({ chartData }) {
  if (!chartData?.ranks?.length) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        No distribution data available.
      </div>
    );
  }

  const data = chartData.ranks.map((rank, idx) => ({
    rank,
    real: Number(chartData.real[idx]),
    synthetic: Number(chartData.synthetic[idx]),
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
            bottom: 20,
          }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="#334155"
          />

          {/* Log-scaled Rank axis */}
          <XAxis
            dataKey="rank"
            type="number"
            scale="log"
            domain={['dataMin', 'dataMax']}
            tick={{ fill: '#94A3B8', fontSize: 12 }}
            axisLine={{ stroke: '#475569' }}
            tickLine={{ stroke: '#475569' }}
            label={{
              value: 'Rank (log scale)',
              position: 'insideBottom',
              offset: -10,
              fill: '#94A3B8',
            }}
          />

          {/* Linear Packet Share axis */}
          <YAxis
            tick={{ fill: '#94A3B8', fontSize: 12 }}
            axisLine={{ stroke: '#475569' }}
            tickLine={{ stroke: '#475569' }}
            tickFormatter={(v) => `${(v * 100).toFixed(1)}%`}
            label={{
              value: 'Normalized Share (%)',
              angle: -90,
              position: 'insideLeft',
              fill: '#94A3B8',
            }}
          />

          <Tooltip
            contentStyle={{
              backgroundColor: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#F8FAFC',
            }}
            labelFormatter={(rank) => `Rank ${rank}`}
            formatter={(value, name) => [
              `${(value * 100).toFixed(3)}%`,
              name,
            ]}
          />

          <Legend
            verticalAlign="top"
            height={36}
            wrapperStyle={{
              color: '#F8FAFC',
            }}
          />

          <Line
            type="monotone"
            dataKey="real"
            name="Real Distribution"
            stroke="#FF6B6B"
            strokeWidth={4}
            dot={false}
            activeDot={{ r: 6 }}
          />

          <Line
            type="monotone"
            dataKey="synthetic"
            name="Synthetic Distribution"
            stroke="#00E5FF"
            strokeWidth={3}
            strokeDasharray="8 4"
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}