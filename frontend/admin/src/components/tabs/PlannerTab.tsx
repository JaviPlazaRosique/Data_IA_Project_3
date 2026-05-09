export function PlannerTab() {
  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div className="bg-amber-950/40 border border-amber-800 rounded-xl p-5 flex flex-col gap-2">
        <p className="text-sm font-semibold text-amber-300">Usage logging not yet instrumented</p>
        <p className="text-xs text-amber-400/80 leading-relaxed">
          The AI planner (<code className="bg-amber-900/50 px-1 rounded">POST /api/v1/agent/chat</code>)
          proxies requests to Vertex AI Agent Engine but does not currently log calls to a database.
          To enable this tab, instrument the portal-api endpoint to record each invocation.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">How to enable planner analytics</p>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4 text-sm text-gray-300">
          <Step n={1} text="Add a planner_calls table to PostgreSQL via an Alembic migration (user_id, session_id, created_at, message_length)." />
          <Step n={2} text="In portal-api/app/api/v1/endpoints/agent.py, insert a row on every successful chat call." />
          <Step n={3} text="Add GET /api/v1/planner-usage to admin-api that aggregates daily call counts from that table." />
          <Step n={4} text="Wire the response into this tab." />
        </div>
      </div>
    </div>
  );
}

function Step({ n, text }: { n: number; text: string }) {
  return (
    <div className="flex gap-3">
      <span className="shrink-0 w-6 h-6 rounded-full bg-gray-800 text-gray-400 text-xs flex items-center justify-center font-semibold">
        {n}
      </span>
      <p className="text-gray-400 text-xs leading-relaxed">{text}</p>
    </div>
  );
}
