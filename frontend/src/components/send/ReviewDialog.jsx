import { useEffect, useState } from 'react'
import { getErrorMessage } from '../../api/client'
import { resumesApi } from '../../api/resumes'
import { sendApi } from '../../api/sending'
import Alert from '../Alert'
import Button from '../Button'
import EmailPreview from '../EmailPreview'
import Icon from '../Icon'

/*
    The last check before sending: the exact email each chosen recruiter will get
    (‹ › to go through them). Nothing is sent until "Send N emails" is pressed.
    Calls onSent(result of POST /email/send).
*/
export default function ReviewDialog({ recipients, templateId, profileId, testMode, onSent, onCancel }) {
  const [index, setIndex] = useState(0)
  const [preview, setPreview] = useState({ data: null, error: '', loading: true })
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  const contact = recipients[index]
  const count = recipients.length

  // Fill the email in for whichever recruiter is shown
  useEffect(() => {
    let cancelled = false
    setPreview((prev) => ({ ...prev, loading: true }))
    sendApi
      .preview({ contact_id: contact.id, template_id: templateId, sender_profile_id: profileId })
      .then((data) => !cancelled && setPreview({ data, error: '', loading: false }))
      .catch((err) => !cancelled && setPreview({ data: null, error: getErrorMessage(err), loading: false }))
    return () => {
      cancelled = true
    }
  }, [contact.id, templateId, profileId])

  // Open the tab right away (browsers block tabs opened after a wait), then point it at the active resume
  async function viewResume() {
    const tab = window.open('', '_blank')
    try {
        const active = (await resumesApi.list()).find((r)=> r.is_active)
        const { url } = await resumesApi.viewUrl(active.id)
        tab.location.href = url 
    }catch(err){
        tab.close()
        setError(getErrorMessage(err))
    }
  }

  async function handleSend() {
    setError('')
    setSending(true)
    try {
      onSent(await sendApi.send({ contact_ids: recipients.map((r) => r.id), template_id: templateId, sender_profile_id: profileId }))
    } catch (err) {
      setError(getErrorMessage(err))
      setSending(false)
    }
  }

  return (
    <>
      <div className="flex flex-col gap-3 px-5 py-4">
        <Alert>{error}</Alert>
        {testMode && <Alert tone="info">🧪 Test mode is on: these emails only go to your test emails.</Alert>}

        <div className="flex items-center justify-between gap-2 text-[13px]">
          <span className="text-muted">
            Email {index + 1} of {count}
          </span>
          <div className="flex gap-1.5">
            <button type="button" onClick={() => setIndex(index - 1)} disabled={index === 0} aria-label="Previous recruiter" className="grid size-8 place-items-center rounded-lg border border-line hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40">
              <Icon name="chevron" className="size-4 rotate-180" />
            </button>
            <button type="button" onClick={() => setIndex(index + 1)} disabled={index === count - 1} aria-label="Next recruiter" className="grid size-8 place-items-center rounded-lg border border-line hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-40">
              <Icon name="chevron" className="size-4" />
            </button>
          </div>
        </div>

        <EmailPreview
          preview={preview.data}
          error={preview.error}
          loading={preview.loading}
          to={<>{contact.name}{contact.company ? `, ${contact.company}` : ''} <span className="text-muted">&lt;{contact.email}&gt;</span></>}
                    attachment={
            preview.data ? (
              <button type="button" onClick={viewResume} title="Open your resume in a new tab" className="text-left font-semibold text-link hover:underline">
                📎 {preview.data.attachment_name}
              </button>
            ) : (
              '…'
            )
          }
        />
        <p className="text-[12.5px] text-muted">Each recruiter gets their own email; nobody sees the others.</p>
      </div>
      <div className="flex justify-end gap-2 border-t border-line px-5 py-4">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={sending}>
          Back
        </Button>
        <Button type="button" loading={sending} onClick={handleSend} disabled={Boolean(preview.error)}>
          <Icon name="send" className="size-4" />
          Send {count} {count === 1 ? 'email' : 'emails'}
        </Button>
      </div>
    </>
  )
}
