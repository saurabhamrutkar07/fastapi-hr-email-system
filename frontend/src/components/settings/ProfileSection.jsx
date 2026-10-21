import { useState } from "react";
import { getErrorMessage } from "../../api/client";
import { settingsApi } from "../../api/settings";
import { useAuth } from "../../auth/context";
import Alert from "../Alert";
import Button from "../Button";
import Field from "../Field";
import Input from "../Input";
import Section from "./Section"

// "+91 98765 43210" -> "+919876543210"
const cleanMobile = (value) => value.replace(/[\s-]/g, '')

// Name and mobile number. The email is the login, so it can't be changed here.
export default function ProfileSection() {
  const { user, updateUser } = useAuth()
  const [name, setName] = useState(user.name)
  const [mobile, setMobile] = useState(user.mobile ?? '')
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  // Update a value, clear its error and the "Saved" note
  const edit = (setValue, field) => (event) => {
    setValue(event.target.value)
    setFieldErrors((prev) => ({ ...prev, [field]: undefined }))
    setSaved(false)
  }

  function validate() {
    const errors = {}
    if (!name.trim()) errors.name = 'Enter your name.'
    else if (name.trim().length > 100) errors.name = 'Keep your name under 100 characters.'
    if (mobile.trim() && !/^\+?\d{10,14}$/.test(cleanMobile(mobile))) {
      errors.mobile = 'Enter a 10-digit mobile number, like 98765 43210.'
    }
    return errors
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const errors = validate()
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return
    setError('')
    setSaving(true)
    try {
      const me = await settingsApi.updateProfile({ name: name.trim(), mobile: cleanMobile(mobile) || null })
      updateUser(me)
      setSaved(true)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Section title="Profile" description="How you appear in ColdReach.">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4 px-4 py-4 sm:px-5">
        <Alert>{error}</Alert>
        <Alert tone="success">{saved && 'Profile saved.'}</Alert>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field id="profile-name" label="Name" error={fieldErrors.name}>
            <Input
              id="profile-name"
              autoComplete="name"
              value={name}
              onChange={edit(setName, 'name')}
              aria-invalid={Boolean(fieldErrors.name)}
            />
          </Field>
          <Field id="profile-mobile" label="Mobile (optional)" error={fieldErrors.mobile}>
            <Input
              id="profile-mobile"
              type="tel"
              autoComplete="tel"
              value={mobile}
              onChange={edit(setMobile, 'mobile')}
              aria-invalid={Boolean(fieldErrors.mobile)}
              placeholder="98765 43210"
            />
          </Field>
        </div>

        <Field id="profile-email" label="Email" hint="You sign in with this email, so it can’t be changed.">
          <Input id="profile-email" value={user.email} disabled className="text-muted" />
        </Field>

        <div className="flex justify-end">
          <Button type="submit" loading={saving}>
            Save profile
          </Button>
        </div>
      </form>
    </Section>
  )
}