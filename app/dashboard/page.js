'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import ScoreCard from '@/components/ScoreCard';
import {
  formatScore,
  getScoreColor,
} from '../../utils/helpers';


const API_BASE_URL = 'http://localhost:8000';


export default function DashboardPage() {
  const router = useRouter();

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Check whether this dashboard was opened by CLI mode
        //
        // Example:
        // /dashboard?job_id=abc123

        const params = new URLSearchParams(
          window.location.search
        );

        const jobId = params.get('job_id');

        // CLI FLOW
        if (jobId) {
          console.log(
            'CLI dashboard job detected:',
            jobId
          );

          const response = await fetch(
            `${API_BASE_URL}/jobs/${jobId}/result`,
            {
              method: 'GET',
              cache: 'no-store',
            }
          );


          if (!response.ok) {
            let message =
              `Failed to load job result (${response.status})`;

            try {
              const errorData = await response.json();

              if (errorData?.detail) {
                message = errorData.detail;
              }
            } catch {
              // Ignore JSON parsing errors for error responses.
            }

            throw new Error(message);
          }


          const responseData = await response.json();

          console.log(
            'CLI result received:',
            responseData
          );


          /*
           * IMPORTANT
           * ---------
           *
           * If your FastAPI endpoint returns the result directly:
           *
           * {
           *   "overallRMS": ...,
           *   "packet_report": ...,
           *   ...
           * }
           *
           * then responseData is used.
           *
           * If FastAPI wraps it like:
           *
           * {
           *   "job_id": "...",
           *   "status": "completed",
           *   "result": {
           *      ...
           *   }
           * }
           *
           * then responseData.result is used.
           *
           * This supports both formats.
           */

          const resultData = responseData?.result ?? responseData;

          // Store using exactly the same key used by
          // the normal frontend flow.
          localStorage.setItem(
            'syntheticEvalData',
            JSON.stringify(resultData)
          );

          // Optionally keep the job ID too.
          localStorage.setItem(
            'syntheticEvalJobId',
            jobId
          );


          setDashboardData(resultData);
          setLoading(false);

          return;
        }

        // NORMAL FRONTEND FLOW
        const savedData = localStorage.getItem(
          'syntheticEvalData'
        );


        if (!savedData) {
          setError(
            'No active analysis found. Please run data metrics first.'
          );

          setLoading(false);

          return;
        }

        try {
          const parsedData = JSON.parse(savedData);

          setDashboardData(parsedData);

        } catch (parseError) {
          console.error(
            'Invalid syntheticEvalData in localStorage:',
            parseError
          );

          localStorage.removeItem(
            'syntheticEvalData'
          );

          setError(
            'Saved analysis data is invalid. Please run the analysis again.'
          );
        }


      } catch (err) {
        console.error(
          'Failed to load dashboard:',
          err
        );

        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load dashboard data.'
        );

      } finally {
        setLoading(false);
      }
    };


    loadDashboardData();

  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-500">
        Loading analysis...
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 text-center">
        <p className="text-slate-500">
          {error}
        </p>

        <button
          onClick={() => router.push('/')}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
        >
          Go Back
        </button>
      </div>
    );
  }

  // Missing data fallback
  if (!dashboardData) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-500">
        No analysis data available.
      </div>
    );
  }

  // Scores
  const overallScoreValue = dashboardData.overallRMS ?? 0;
  
  const packetScore = dashboardData.packet_report?.overall?.avg ?? 0;
  const statelessScore = dashboardData.stateless_report?.overall?.avg ?? 0;
  const statefulScore = dashboardData.statefull_report?.overall?.avg ?? 0;


  const overallColors = getScoreColor(overallScoreValue);

  // Dashboard
  return (
    <div className="space-y-8">

      {/* Overall Quality Score */}

      <div className="flex flex-col items-center justify-between gap-6 rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900 sm:flex-row">

        <div className="space-y-1">

          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            Overall Quality Score
          </h2>

          <p className="max-w-lg text-sm text-slate-500 dark:text-slate-400">
            The average distance score across all categories.
            Lower scores represent closer alignment with real
            data distributions.
          </p>

        </div>


        <div
          className={`
            flex h-28 w-28
            flex-col
            items-center
            justify-center
            rounded-full
            border-2
            ${overallColors.border}
            ${overallColors.bg}
          `}
        >

          <span
            className={`
              text-3xl
              font-bold
              ${overallColors.text}
            `}
          >
            {formatScore(overallScoreValue)}
          </span>

          <span className="mt-0.5 text-xs font-medium text-slate-400">
            Distance
          </span>

        </div>

      </div>


      {/* Categories */}

      <div className="space-y-4">

        <h3 className="text-lg font-medium text-slate-900 dark:text-white">
          Categories
        </h3>


        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">

          <ScoreCard
            title="Packet Level"
            score={packetScore}
            onClick={() =>
              router.push(
                '/dashboard/packet_level'
              )
            }
          />


          <ScoreCard
            title="Flow Stateless"
            score={statelessScore}
            onClick={() =>
              router.push(
                '/dashboard/flow_stateless'
              )
            }
          />


          <ScoreCard
            title="Flow Stateful"
            score={statefulScore}
            onClick={() =>
              router.push(
                '/dashboard/flow_stateful'
              )
            }
          />

        </div>

      </div>

    </div>
  );
}