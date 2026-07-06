'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function BarComparisonChart({ chartData }) {
  const data = chartData
    ? [
        {
          name: chartData.label,
          real: chartData.real,
          synthetic: chartData.synthetic,
        },
      ]
    : [];

  return (
    <div className="w-full h-[400px] bg-white p-4 rounded-xl border border-slate-100 dark:bg-slate-900 dark:border-slate-800">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" className="dark:stroke-slate-800" />
          <XAxis 
            dataKey="name" 
            tick={{ fill: '#64748B', fontSize: 12 }}
            axisLine={{ stroke: '#CBD5E1' }}
          />
          <YAxis 
            tick={{ fill: '#64748B', fontSize: 12 }}
            axisLine={{ stroke: '#CBD5E1' }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1E293B', 
              borderRadius: '8px', 
              color: '#F8FAFC',
              border: 'none'
            }} 
          />
          <Legend verticalAlign="top" height={36} iconType="circle" />
          
          {/* Side-by-Side Evaluation Target Metrics */}
          <Bar 
            name="Real Data Distribution" 
            dataKey="real" 
            fill="#4F46E5" 
            radius={[4, 4, 0, 0]} 
          />
          <Bar 
            name="Synthetic Data Distribution" 
            dataKey="synthetic" 
            fill="#06B6D4" 
            radius={[4, 4, 0, 0]} 
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}