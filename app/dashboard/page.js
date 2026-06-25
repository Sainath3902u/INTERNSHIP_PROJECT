'use client';

import { useRouter } from 'next/navigation';
import { mockData } from '../../services/mockData';
import ScoreCard from '../../components/ScoreCard';
import { formatScore, getScoreColor } from '../../utils/helpers';

export default function DashboardPage() {
  const router = useRouter();
  const overallColors = getScoreColor(mockData.overall_score);

  return (
    <div className="space-y-8">
      <div className="p-6 rounded-xl bg-white border border-slate-200 dark:bg-slate-900 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Overall Quality Score</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-lg">
            The average distance score across all categories. Lower scores represent closer alignment with real data distributions.
          </p>
        </div>
        
        
        <div className={`flex flex-col items-center justify-center h-28 w-28 rounded-full border-2 ${overallColors.border} ${overallColors.bg}`}>
          <span className={`text-3xl font-bold ${overallColors.text}`}>
            {formatScore(mockData.overall_score)}
          </span>
          <span className="text-xs font-medium text-slate-400 mt-0.5">Distance</span>
        </div>
      </div>

      
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-slate-900 dark:text-white">Categories</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ScoreCard 
            title="Packet Level" 
            score={mockData.packet_level.score} 
            onClick={() => router.push('/dashboard/packet_level')} 
          />
          <ScoreCard 
            title="Flow Stateless" 
            score={mockData.flow_stateless.score} 
            onClick={() => router.push('/dashboard/flow_stateless')} 
          />
          <ScoreCard 
            title="Flow Stateful" 
            score={mockData.flow_stateful.score} 
            onClick={() => router.push('/dashboard/flow_stateful')} 
          />
        </div>
      </div>
    </div>
  );
}