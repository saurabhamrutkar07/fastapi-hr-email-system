import { Link } from 'react-router'
import { dashboardApi } from '../api/dashboard'
import useApi from '../hooks/useApi'
import { formatDateTime } from '../utils/format'
import StatusPill from './StatusPill'

// The last 5 emails, newest first, with a link to the full history
export default function RecentSends() {
  const sends = useApi(dashboardApi.recentSends)

  return (
    <section className="rounded-xl border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3.5 sm:px-5">
        <h3 className="font-display text-[15.5px] font-bold text-brand-ink">Recent sends</h3>
        <Link to="/history" className="text-[13px] font-semibold text-link hover:underline">
          View all
        </Link>
      </div>

      {sends.loading ? (
        <ul aria-hidden="true">
          {[1, 2, 3].map((n) => (
            <li key={n} className="flex items-center gap-3 border-b border-line px-4 py-3 last:border-b-0 sm:px-5">
              <div className="h-3.5 flex-1 animate-pulse rounded bg-surface-2" />
              <div className="h-5 w-14 animate-pulse rounded-full bg-surface-2" />
            </li>
          ))}
        </ul>
      ) : sends.error ? (
        <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-4 text-[13px] sm:px-5">
          <span className="text-err-text">Couldn't load recent sends. {sends.error}</span>
          <button onClick={sends.reload} className="font-semibold text-link hover:underline">
            Try again
          </button>
        </div>
      ) : sends.data.length === 0 ? (
        <div className="flex flex-col items-center gap-1 px-5 py-8 text-center">
          <p className="font-semibold">No emails sent yet</p>
          <Link to="/send" className="text-[13px] font-semibold text-link hover:underline">
            Send your first email
          </Link>
        </div>
      ) : (
        <ul>
          {sends.data.map((send) => (
            <li key={send.id} className="flex items-center gap-3 border-b border-line px-4 py-3 last:border-b-0 sm:px-5">
              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold">{send.recipient_email}</p>
                <p className="text-xs text-muted">
                  {formatDateTime(send.created_at)}
                  {send.error_code && <span className="text-err-text"> · {send.error_code}</span>}
                </p>
              </div>
              <StatusPill status={send.status} />
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
