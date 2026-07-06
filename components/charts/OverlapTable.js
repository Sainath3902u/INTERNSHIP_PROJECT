'use client';

export default function TopNKeyOverlapChart({ chartData }) {
  if (!chartData?.real || !chartData?.synthetic) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        No overlap data available.
      </div>
    );
  }

  const realSet = new Set(chartData.real);
  const syntheticSet = new Set(chartData.synthetic);

  const allKeys = [
    ...new Set([
      ...chartData.real,
      ...chartData.synthetic,
    ]),
  ].sort();

  const overlapCount = allKeys.filter(
    key => realSet.has(key) && syntheticSet.has(key)
  ).length;

  return (
    <div className="w-full bg-white p-4 rounded-xl border border-slate-100 dark:bg-slate-900 dark:border-slate-800">
      
      {/* Summary */}
      <div className="mb-3 grid grid-cols-3 gap-3">
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800">
          <div className="text-xs text-slate-500">
            Real
          </div>
          <div className="text-xl font-semibold">
            {chartData.real.length}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800">
          <div className="text-xs text-slate-500">
            Synthetic
          </div>
          <div className="text-xl font-semibold">
            {chartData.synthetic.length}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800">
          <div className="text-xs text-slate-500">
            Overlap
          </div>
          <div className="text-xl font-semibold">
            {overlapCount}
          </div>
        </div>
      </div>

      {/* Matrix */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="text-left py-2 px-2">Key</th>
              <th className="text-center py-2 px-2">R</th>
              <th className="text-center py-2 px-2">S</th>
            </tr>
          </thead>

          <tbody>
            {allKeys.map(key => (
              <tr
                key={key}
                className="border-b border-slate-100 dark:border-slate-800"
              >
                <td className="py-2 px-2 font-medium">
                  {key}
                </td>

                <td className="text-center py-2 px-2">
                  {realSet.has(key) ? (
                    <span className="text-green-500 text-base">✓</span>
                  ) : (
                    <span className="text-slate-400 text-base">✕</span>
                  )}
                </td>

                <td className="text-center py-2 px-2">
                  {syntheticSet.has(key) ? (
                    <span className="text-green-400 text-base">✓</span>
                  ) : (
                    <span className="text-slate-400 text-base">✕</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}