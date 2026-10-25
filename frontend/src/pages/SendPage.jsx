import { useMemo, useState } from 'react'
import { Link } from 'react-router'
import { contactsApi } from '../api/contacts'
import { senderProfilesApi, sendApi, testModeApi } from '../api/sending'
import { templatesApi } from '../api/templates'
import { useAuth } from '../auth/context'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Field from '../components/Field'
import Icon from '../components/Icon'
import Modal from '../components/Modal'
import ReadyChecklist from '../components/ReadyChecklist'
import Select from '../components/Select'
import RecipientPicker from '../components/send/RecipientPicker'
import ReviewDialog from '../components/send/ReviewDialog'
import SendResults from '../components/send/SendResults'
import useApi from '../hooks/useApi'
import useSetupStatus from '../hooks/useSetupStatus'

const noTestMode = async () => null

// Pick recruiters, check the exact emails, send, and watch them go out
export default function SendPage() {
  const { user } = useAuth()
  const setup = useSetupStatus()
  const contacts = useApi(contactsApi.list)
  const profiles = useApi(senderProfilesApi.list)
  const templates = useApi(templatesApi.list)
  const lastSent = useApi(sendApi.lastSent)
  const testMode = useApi(user.role === 'admin' ? testModeApi.get : noTestMode)

  const [profileId, setProfileId] = useState(null)
  const [templateId, setTemplateId] = useState(null)
  const [selected, setSelected] = useState(() => new Set())
  const [reviewing, setReviewing] = useState(false)
  const [batch, setBatch] = useState(null)

  // Until the user picks, use their defaults
  const profile = profiles.data?.find((p) => p.id === profileId) ?? profiles.data?.find((p) => p.is_default) ?? profiles.data?.[0]
  const template = templates.data?.find((t) => t.id === templateId) ?? templates.data?.find((t) => t.is_default)

  // Admin test mode: only these addresses can be emailed
  const allowedEmails = useMemo(
    () => (testMode.data?.enabled ? new Set(testMode.data.test_emails.map((e) => e.toLowerCase())) : null),
    [testMode.data],
  )

  const recipients = (contacts.data ?? []).filter((c) => selected.has(c.id))
  const loading = setup.loading || contacts.loading || profiles.loading || templates.loading || lastSent.loading || testMode.loading
  const loadError = contacts.error || profiles.error || templates.error || lastSent.error || testMode.error
  const needsDetails = !profiles.loading && profiles.data?.length === 0

  function sendMore() {
    setBatch(null)
    setSelected(new Set())
    lastSent.reload()
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">Send Email</h2>
        <p className="mt-0.5 text-muted">Emails go out from your own Gmail with your active resume attached.</p>
      </div>

      {allowedEmails && (
        <Alert tone="info">
          🧪 Test mode is on: only your {allowedEmails.size} test {allowedEmails.size === 1 ? 'email is' : 'emails are'} listed.
          Change it in <Link to="/settings" className="font-semibold text-link hover:underline">Settings</Link>.
        </Alert>
      )}

      {loadError ? (
        <Alert>Couldn’t load the page. {loadError}</Alert>
      ) : loading ? (
        <div className="h-64 animate-pulse rounded-xl border border-line bg-surface" aria-hidden="true" />
      ) : !setup.allReady || needsDetails ? (
        <div className="flex max-w-xl flex-col gap-3">
          <p className="font-semibold">Before you send</p>
          {!setup.allReady && <ReadyChecklist setup={setup} />}
          {needsDetails && (
            <Alert tone="info">
              Add your details for emails (job position, experience, skills) in{' '}
              <Link to="/settings" className="font-semibold text-link hover:underline">Settings</Link>.
            </Alert>
          )}
        </div>
      ) : batch ? (
        <SendResults batch={batch} onDone={sendMore} />
      ) : (
        <>
          <div className="grid gap-4 rounded-xl border border-line bg-surface p-4 sm:grid-cols-2 sm:p-5">
            <Field id="send-profile" label="Your details" hint={`${profile.job_position} · ${profile.experience_years} years · ${profile.skills.join(', ')}`}>
              <Select id="send-profile" value={profile.id} onChange={(e) => setProfileId(Number(e.target.value))}>
                {profiles.data.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}{p.is_default ? ' (default)' : ''}
                  </option>
                ))}
              </Select>
            </Field>
            <Field id="send-template" label="Template" hint={template.subject || 'Default subject'}>
              <Select id="send-template" value={template.id} onChange={(e) => setTemplateId(Number(e.target.value))}>
                {templates.data.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}{t.is_default ? ' (default)' : ''}
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          <RecipientPicker
            contacts={contacts.data}
            selected={selected}
            onChange={setSelected}
            lastSent={lastSent.data}
            allowedEmails={allowedEmails}
          />

          <div className="sticky bottom-0 -mx-4 flex items-center justify-between gap-3 border-t border-line bg-bg/95 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-xl sm:border sm:bg-surface">
            <span className="text-[13.5px] tabular-nums">
              <b>{recipients.length}</b> {recipients.length === 1 ? 'recruiter' : 'recruiters'} selected
            </span>
            <Button onClick={() => setReviewing(true)} disabled={recipients.length === 0}>
              Review & send
              <Icon name="chevron" className="size-4" />
            </Button>
          </div>
        </>
      )}

      <Modal
        open={reviewing}
        onClose={() => setReviewing(false)}
        title="Check your emails"
        description={`${recipients.length} ${recipients.length === 1 ? 'email' : 'emails'} with “${template?.name}”`}
      >
        <ReviewDialog
          recipients={recipients}
          templateId={template?.id}
          profileId={profile?.id}
          testMode={Boolean(allowedEmails)}
          onSent={(result) => {
            setReviewing(false)
            setBatch(result)
          }}
          onCancel={() => setReviewing(false)}
        />
      </Modal>
    </div>
  )
}
