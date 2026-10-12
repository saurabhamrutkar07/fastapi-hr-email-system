const STATUSES = {
  SUCCESS: { label: 'Sent', tone: 'bg-ok-soft text-ok-text', dot: 'bg-ok' },
  FAILED: { label: 'Failed', tone: 'bg-err-soft text-err-text', dot: 'bg-err' },
}

// Coloured label for an email's status from the backend ("SUCCESS" / "FAILED")
export default function StatusPill({ status }) {
  const s = STATUSES[status] ?? { label: status, tone: 'bg-surface-2 text-muted', dot: 'bg-muted' }

  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${s.tone}`}>
      <i className={`size-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  )
}
