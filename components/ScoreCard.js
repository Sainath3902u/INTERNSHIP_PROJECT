import { getScoreColor, formatScore, convertToConfidence } from '../utils/helpers';

export default function ScoreCard({ title, score, onClick }) {
  const statusStyles = getScoreColor(score);
  const formattedDistance = formatScore(score);
  const matchPercentage = convertToConfidence(score);

  return (
    <div 
      onClick={onClick}
      className={`p-6 rounded-none border ${statusStyles.zx} ${statusStyles.bg} shadow-sm hover:shadow-md hover:scale-[1.01] transition-all duration-200 cursor-pointer group flex flex-col justify-between`}
    >
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
            {title}
          </h3>
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium border ${statusStyles.border} bg-white dark:bg-slate-900 ${statusStyles.text}`}>
            {statusStyles.label}
          </span>
        </div>
        
        <div className="space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
            Distance Score
          </span>
          <div className={`text-3xl font-extrabold tracking-tight ${statusStyles.text}`}>
            {formattedDistance}
          </div>
        </div>
      </div>

      {/* Progress Metric bar tracker */}
      <div className="mt-6 space-y-1.5">
        <div className="flex justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
          <span>Data Similarity Profile</span>
          <span>{matchPercentage}</span>
        </div>
        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden dark:bg-slate-800">
          <div 
            className={`h-full rounded-full transition-all duration-500 bg-current ${statusStyles.text}`}
            style={{ width: matchPercentage }}
          />
        </div>
      </div>
    </div>
  );
}