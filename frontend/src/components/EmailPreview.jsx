// How an email will read once filled in: { subject, body } from POST /email-template/preview.
// `to` and `attachment` default to the sample recruiter and a generic resume line.
export default function EmailPreview({ preview, error, loading, to, attachment }) {
  return (
    <div className="flex min-w-0 flex-col overflow-hidden rounded-xl border border-line bg-surface">
      <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 border-b border-line px-4 py-3 text-[13px]">
        <dt className="text-muted">To</dt>
        <dd className="wrap-break-word">{to ?? <>Priya Sharma, Zoho <span className="text-muted">(sample recruiter)</span></>}</dd>
        <dt className="text-muted">Subject</dt>
        <dd className="font-semibold wrap-break-word">{preview?.subject ?? '…'}</dd>
        <dt className="text-muted">Attached</dt>
        <dd className="wrap-break-word">{attachment ?? 'Your active resume (PDF)'}</dd>
      </dl>
      <div className={`min-h-40 px-4 py-3 text-[14px] ${loading ? 'opacity-60' : ''}`}>
        {error ? (
          <p className="text-err-text">{error}</p>
        ) : preview ? (
          <p className="whitespace-pre-wrap wrap-break-word">{preview.body}</p>
        ) : (
          <p className="text-muted">The preview appears here.</p>
        )}
      </div>
    </div>
  )
}
