import { useState } from 'react'
import { getErrorMessage } from '../../api/client'
import { settingsApi } from '../../api/settings'
import { useAuth } from '../../auth/context'
import useApi from '../../hooks/useApi'
import Alert from '../Alert'
import Button from '../Button'
import Field from '../Field'
import Input from '../Input'
import PasswordInput from '../PasswordInput'
import Section from './Section'

const APP_PASSWORDS_URL = 'https://myaccount.google.com/apppasswords'

/*
    The Gmail account cold emails are sent from. Saving logs in to Gmail first,
    so a wrong App Password shows up here instead of on the first send.
*/
export default function GmailSection() {
  const { user } = useAuth()
  const smtp = useApi(settingsApi.smtp)
  const connected = Boolean(smtp.data?.is_active)

  const [email, setEmail] = useState(null) // null until the user types
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  // Until the user types, suggest the connected address, else their sign-in email
  const shownEmail = email ?? smtp.data?.email_address ?? user.email

  const edit = (setValue, field) => (event) => {
    setValue(event.target.value)
    setFieldErrors((prev) => ({ ...prev, [field]: undefined }))
    setNotice('')
  }

  function validate() {
    const errors = {}
    if (!/^\S+@\S+\.\S+$/.test(shownEmail.trim())) errors.email = 'Enter your Gmail address.'
    const letters = password.replace(/\s/g, '')
    if (!letters) errors.password = 'Paste the App Password you created in Google.'
    else if (letters.length !== 16) {
      errors.password = 'An App Password has 16 letters, like abcd efgh ijkl mnop. Your normal Gmail password won’t work.'
    }
    return errors
  }

  async function handleSave(event) {
    event.preventDefault()
    const errors = validate()
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return
    setError('')
    setNotice('')
    setSaving(true)
    try {
      await settingsApi.saveSmtp({ email_address: shownEmail.trim(), password })
      setPassword('')
      setEmail(null)
      setNotice('Gmail connected. Send a test email to check it.')
      smtp.reload()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleTest() {
    setError('')
    setNotice('')
    setTesting(true)
    try {
      const result = await settingsApi.testSmtp()
      setNotice(result.message)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setTesting(false)
    }
  }

  const status = smtp.loading ? null : connected ? (
    <span className="rounded-full bg-ok-soft px-2.5 py-0.5 text-[12px] font-semibold text-ok-text">Connected</span>
  ) : (
    <span className="rounded-full bg-warn-soft px-2.5 py-0.5 text-[12px] font-semibold text-warn-text">Not connected</span>
  )

  return (
    <Section
      title="Gmail"
      description="Cold emails go out from your own Gmail, so replies come straight to your inbox."
      aside={status}
    >
      <form onSubmit={handleSave} noValidate className="flex flex-col gap-4 px-4 py-4 sm:px-5">
        {smtp.error && <Alert>Couldn’t check your Gmail connection. {smtp.error}</Alert>}
        <Alert>{error}</Alert>
        <Alert tone="success">{notice}</Alert>

        {connected && (
          <p className="text-[13.5px]">
            Sending from <b className="break-all">{smtp.data.email_address}</b>. To change it, enter a new address or
            App Password below.
          </p>
        )}

        <ol className="list-decimal rounded-lg bg-surface-2 py-3 pl-8 pr-4 text-[13px] text-muted">
          <li>Turn on 2-Step Verification in your Google account.</li>
          <li>
            Open{' '}
            <a href={APP_PASSWORDS_URL} target="_blank" rel="noreferrer" className="font-semibold text-link hover:underline">
              App Passwords
            </a>
            , create one named “ColdReach” and copy the 16 letters.
          </li>
          <li>Paste it below. Your normal Gmail password won’t work here.</li>
        </ol>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field id="gmail-address" label="Gmail address" error={fieldErrors.email}>
            <Input
              id="gmail-address"
              type="email"
              autoComplete="email"
              value={shownEmail}
              onChange={edit(setEmail, 'email')}
              aria-invalid={Boolean(fieldErrors.email)}
            />
          </Field>
          <Field id="gmail-password" label="App Password" error={fieldErrors.password}>
            <PasswordInput
              id="gmail-password"
              autoComplete="off"
              value={password}
              onChange={edit(setPassword, 'password')}
              aria-invalid={Boolean(fieldErrors.password)}
              placeholder="abcd efgh ijkl mnop"
            />
          </Field>
        </div>

        <div className="flex flex-wrap justify-end gap-2">
          {connected && (
            <Button type="button" variant="secondary" loading={testing} onClick={handleTest}>
              Send test email
            </Button>
          )}
          <Button type="submit" loading={saving}>
            {connected ? 'Save changes' : 'Connect Gmail'}
          </Button>
        </div>
      </form>
    </Section>
  )
}
