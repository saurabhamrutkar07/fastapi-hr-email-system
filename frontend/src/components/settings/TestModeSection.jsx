import { useState } from 'react'
import { getErrorMessage } from '../../api/client'
import { testModeApi } from '../../api/sending'
import useApi from '../../hooks/useApi'
import Alert from '../Alert'
import Button from '../Button'
import Field from '../Field'
import Textarea from '../Textarea'
import Section from './Section'

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/

/*
    Admins only. While test mode is on, the admin's own sends can only go to the test
    emails listed here, so features can be tried on real Gmail without emailing recruiters.
*/
export default function TestModeSection() {
  const testMode = useApi(testModeApi.get)
  if (testMode.loading) return null
  // The form starts from the saved settings, so it waits for them to load
  return <TestModeForm initial={testMode.data} loadError={testMode.error} />
}

function TestModeForm({ initial, loadError }) {
  const [enabled, setEnabled] = useState(initial?.enabled ?? true)
  const [emails, setEmails] = useState((initial?.test_emails ?? []).join('\n'))
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const list = emails.split(/[\s,]+/).map((e) => e.trim()).filter(Boolean)
    const bad = list.find((e) => !EMAIL_PATTERN.test(e))
    if (bad) {
      setError(`“${bad}” isn’t an email address.`)
      return
    }
    setError('')
    setSaving(true)
    try {
      const saved = await testModeApi.update({ enabled, test_emails: list })
      setEmails(saved.test_emails.join('\n'))
      setNotice(saved.enabled ? 'Test mode is on.' : 'Test mode is off. Your emails go to real recruiters.')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const status = enabled ? (
    <span className="rounded-full bg-warn-soft px-2.5 py-0.5 text-[12px] font-semibold text-warn-text">On</span>
  ) : (
    <span className="rounded-full bg-surface-2 px-2.5 py-0.5 text-[12px] font-semibold text-muted">Off</span>
  )

  return (
    <Section
      title="Test mode (admin)"
      description="While on, your sends only go to the test emails below. Other users are never affected."
      aside={status}
    >
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4 px-4 py-4 sm:px-5">
        <Alert>{error || loadError}</Alert>
        <Alert tone="success">{notice}</Alert>

        <label className="flex items-center gap-2 text-[13.5px] font-semibold">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => { setEnabled(e.target.checked); setNotice('') }}
            className="size-4"
          />
          Only send to my test emails
        </label>

        <Field id="test-emails" label="Test emails" hint="One per line. Gmail aliases like you+hr1@gmail.com land in your own inbox.">
          <Textarea
            id="test-emails"
            rows={4}
            value={emails}
            onChange={(e) => { setEmails(e.target.value); setNotice('') }}
            placeholder={'you+hr1@gmail.com\nyou+hr2@gmail.com'}
            className="font-mono text-[13px]"
          />
        </Field>

        <div className="flex justify-end">
          <Button type="submit" loading={saving}>
            Save test mode
          </Button>
        </div>
      </form>
    </Section>
  )
}
