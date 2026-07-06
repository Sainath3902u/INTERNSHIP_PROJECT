'use client';

import RankShareChart from './charts/RankShareChart';
import BarComparisonChart from './charts/BarComparisonChart';
import CategoryDistributionChart from './charts/GroupedBarChart';
import OverlayLineChart from './charts/OverlayLineChart';
import TopNKeyOverlapChart from './charts/OverlapTable';

export default function ComparisonChart({ chartData }) {
  if (!chartData) return null;

  switch (chartData.type) {
    case 'distribution':
      return <RankShareChart chartData={chartData} />;

    case 'dual_bar':
      return <BarComparisonChart chartData={chartData} />;

    case 'grouped_bar':
      return <CategoryDistributionChart chartData={chartData} />

    case 'overlay_line':
      return <OverlayLineChart chartData={chartData} />

    case 'topnkey':
      return <TopNKeyOverlapChart chartData={chartData} />

    default:
      return (
        <div className="p-8 text-center">
          Unsupported visualization type
        </div>
      );
  }
}