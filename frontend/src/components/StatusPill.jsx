const STATUSES = {
  SUCCESS: { label: 'Sent', tone: 'bg-ok-soft text-ok-text', dot: 'bg-ok' },
  FAILED: { label: 'Failed', tone: 'bg-err-soft text-err-text', dot: 'bg-err' },
  PENDING: { label: 'Sending…', tone: 'bg-warn-soft text-warn-text', dot: 'bg-warn animate-pulse' },
  // A user's statusm from the admin's Users page
  active: { label: 'Active', tone: 'bg-ok-soft text-ok-text', dot: 'bg-ok'},
  blocked: { label: 'Blocked', tone: 'bg-err-soft text-err-text', dot: 'bg-err'},
  pending:  { label: 'Signup not finished', tone: 'bg-warn-soft text-warn-text', dot: 'bg-warn'}
}

// Coloured label for an email's status ("SUCCESS" / "FAILED" / "PENDING") or a user's ("active" / "blocked" / "pending")
export default function StatusPill({ status }) {
  const s = STATUSES[status] ?? { label: status, tone: 'bg-surface-2 text-muted', dot: 'bg-muted' }

  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${s.tone}`}>
      <i className={`size-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  )
}
