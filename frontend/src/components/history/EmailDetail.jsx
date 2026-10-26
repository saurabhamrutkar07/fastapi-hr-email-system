import { useEffect, useState } from "react";
import { getErrorMessage } from "../../api/client";
import { historyApi } from "../../api/history";
import { formatDate, formatDateTime } from "../../utils/format";
import Alert from '../Alert'
import EmailPreview from '../EmailPreview'
import StatusPill from '../StatusPill'


// Everything about one sent email: when, the result, and exactly what it said
export default function EmailDetail({ requestId, showSender }) {
  const [state, setState] = useState({ data: null, error: '', loading: true })

  useEffect(() => {
    let cancelled = false
    setState({ data: null, error: '', loading: true })
    historyApi
      .get(requestId)
      .then((data) => !cancelled && setState({ data, error: '', loading: false }))
      .catch((err) => !cancelled && setState({ data: null, error: getErrorMessage(err), loading: false }))
    return () => {
      cancelled = true
    }
  }, [requestId])

  const email = state.data

  if (state.error) return <div className="px-5 py-4"><Alert>{state.error}</Alert></div>
  if (!email) return <div className="m-5 h-64 animate-pulse rounded-xl bg-surface-2" aria-hidden="true" />

  return (
    <div className="flex flex-col gap-3 px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-2 text-[13px]">
        <StatusPill status={email.status} />
        <span className="text-muted tabular-nums" title={formatDate(email.created_at)}>
          {formatDateTime(email.created_at)}
        </span>
      </div>

      {email.status === 'FAILED' && (
        <Alert>
          {email.error_code}: {email.response_details}
        </Alert>
      )}

      {email.body ? (
        <EmailPreview
          preview={email}
          to={
            <>
              {email.contact_name}
              {email.company ? `, ${email.company}` : ''} <span className="text-muted">&lt;{email.recipient_email}&gt;</span>
            </>
          }
          attachment={email.resume_version ? `📎 Resume v${email.resume_version}` : '📎 Resume'}
        />
      ) : (
        <p className="rounded-lg border border-line bg-surface-2 px-4 py-3 text-[13.5px] text-muted">
          Sent to <b className="text-fg">{email.recipient_email}</b>. This email was sent before History kept a copy of what was
          sent.
        </p>
      )}

      <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 text-[13px]">
        {email.template_name && (
          <>
            <dt className="text-muted">Template</dt>
            <dd>{email.template_name}</dd>
          </>
        )}
        {showSender && (
          <>
            <dt className="text-muted">Sent by</dt>
            <dd className="wrap-break-word">
              {email.sender_name ?? '—'} {email.sender_email && <span className="text-muted">&lt;{email.sender_email}&gt;</span>}
            </dd>
          </>
        )}
      </dl>
    </div>
  )
} 
