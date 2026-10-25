import { useEffect, useState } from 'react'
import { getErrorMessage } from '../../api/client'
import { sendApi } from '../../api/sending'
import Alert from '../Alert'
import Button, { ButtonLink } from '../Button'
import StatusPill from '../StatusPill'

const POLL_MS = 2000
const GIVE_UP_AFTER = 90 // polls (3 minutes)

/*
    After "Send": emails go out one by one in the background, so this asks the backend
    every 2 seconds how each one went until none is still sending.
*/
export default function SendResults({ batch, onDone }) {
  const [statuses, setStatuses] = useState({}) // request_id -> { status, error_code, response_details }
  const [error, setError] = useState('')

  const ids = batch.items.map((item) => item.request_id)
  const pending = batch.items.filter((item) => (statuses[item.request_id]?.status ?? 'PENDING') === 'PENDING').length
  const sent = batch.items.filter((item) => statuses[item.request_id]?.status === 'SUCCESS').length
  const failed = batch.items.length - pending - sent

  useEffect(() => {
    let cancelled = false
    let polls = 0
    let timer

    async function poll() {
      try {
        const rows = await sendApi.status(ids)
        if (cancelled) return
        setStatuses(Object.fromEntries(rows.map((row) => [row.request_id, row])))
        setError('')
        polls += 1
        if (rows.some((row) => row.status === 'PENDING') && polls < GIVE_UP_AFTER) timer = setTimeout(poll, POLL_MS)
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err))
          timer = setTimeout(poll, POLL_MS)
        }
      }
    }

    poll()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
    // The batch never changes while this is on screen
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-line bg-surface p-4 sm:p-5">
      <div>
        <h3 className="font-display text-[17px] font-bold text-brand-ink">
          {pending ? `Sending ${batch.items.length} emails…` : 'All done'}
        </h3>
        <p className="text-[13.5px] text-muted tabular-nums">
          {sent} sent · {failed} failed{pending ? ` · ${pending} still sending` : ''}
          {batch.test_mode && ' · 🧪 test mode'}
        </p>
      </div>
      <Alert>{error}</Alert>

      <ul className="divide-y divide-line rounded-lg border border-line">
        {batch.items.map((item) => {
          const row = statuses[item.request_id]
          return (
            <li key={item.request_id} className="flex flex-wrap items-center gap-3 px-3 py-2.5">
              <div className="min-w-0 flex-1">
                <p className="font-semibold">{item.name}</p>
                <p className="text-[12.5px] wrap-break-word text-muted">{item.email}</p>
                {row?.status === 'FAILED' && (
                  <p className="mt-0.5 text-[12.5px] wrap-break-word text-err-text">
                    {row.error_code}: {row.response_details}
                  </p>
                )}
              </div>
              <StatusPill status={row?.status ?? 'PENDING'} />
            </li>
          )
        })}
      </ul>

      <div className="flex flex-wrap justify-end gap-2">
        <ButtonLink to="/history" variant="secondary">
          See history
        </ButtonLink>
        <Button onClick={onDone} disabled={pending > 0}>
          Send more
        </Button>
      </div>
    </section>
  )
}
