import { useState } from 'react'
import { getErrorMessage } from '../../api/client'
import { senderProfilesApi } from '../../api/sending'
import useApi from '../../hooks/useApi'
import Alert from '../Alert'
import Button from '../Button'
import ConfirmDialog from '../ConfirmDialog'
import Field from '../Field'
import Icon from '../Icon'
import Input from '../Input'
import Modal from '../Modal'
import Section from './Section'

/*
    Sets of "about me" details that fill a template's job position, experience,
    skills and LinkedIn. Users keep one per kind of role and pick one when sending.
*/
export default function SenderProfilesSection() {
  const profiles = useApi(senderProfilesApi.list)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  // null = closed, { profile: null } = add, { profile } = edit
  const [formFor, setFormFor] = useState(null)
  const [deleting, setDeleting] = useState(null)

  function done(message) {
    setNotice(message)
    setError('')
    profiles.reload()
  }

  async function makeDefault(profile) {
    setNotice('')
    try {
      await senderProfilesApi.setDefault(profile.id)
      done(`“${profile.name}” is now your default.`)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function confirmDelete() {
    await senderProfilesApi.remove(deleting.id)
    setDeleting(null)
    done('Details deleted.')
  }

  return (
    <Section
      title="Your details for emails"
      description="Fill in a template’s job position, experience, skills and LinkedIn. Keep one set per kind of role."
      aside={
        <Button variant="secondary" className="px-3 py-1.5 text-[13px]" onClick={() => { setNotice(''); setFormFor({ profile: null }) }}>
          <Icon name="plus" className="size-4" />
          Add details
        </Button>
      }
    >
      <div className="flex flex-col gap-3 px-4 py-4 sm:px-5">
        <Alert tone="success">{notice}</Alert>
        <Alert>{error || profiles.error}</Alert>

        {profiles.loading ? (
          <div className="h-16 animate-pulse rounded-lg bg-surface-2" aria-hidden="true" />
        ) : profiles.data?.length === 0 ? (
          <p className="text-[13.5px] text-muted">
            No details yet. Add a set before sending, for example “Backend roles · Backend Developer · 3 years”.
          </p>
        ) : (
          <ul className="divide-y divide-line rounded-lg border border-line">
            {profiles.data?.map((profile) => (
              <li key={profile.id} className="flex flex-wrap items-center gap-3 px-3 py-3">
                <div className="min-w-0 flex-1">
                  <p className="flex items-center gap-2 font-semibold">
                    {profile.name}
                    {profile.is_default && (
                      <span className="rounded-full bg-ok-soft px-2.5 py-0.5 text-[12px] font-semibold text-ok-text">Default</span>
                    )}
                  </p>
                  <p className="text-[13px] text-muted">
                    {profile.job_position} · {profile.experience_years} years · {profile.skills.join(', ')}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button type="button" onClick={() => { setNotice(''); setFormFor({ profile }) }} aria-label={`Edit ${profile.name}`} title="Edit" className="grid size-8 place-items-center rounded-lg text-muted hover:bg-surface-2 hover:text-fg">
                    <Icon name="edit" className="size-4" />
                  </button>
                  {!profile.is_default && (
                    <button type="button" onClick={() => makeDefault(profile)} className="text-[13px] font-semibold text-link hover:underline">
                      Make default
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setDeleting(profile)}
                    disabled={profile.is_default}
                    aria-label={`Delete ${profile.name}`}
                    title={profile.is_default ? 'Make another set the default before deleting this one' : 'Delete'}
                    className="grid size-8 place-items-center rounded-lg text-muted hover:bg-err-soft hover:text-err-text disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-muted"
                  >
                    <Icon name="trash" className="size-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <Modal open={Boolean(formFor)} onClose={() => setFormFor(null)} title={formFor?.profile ? 'Edit details' : 'Add details'}>
        <ProfileForm
          profile={formFor?.profile}
          onSaved={(name) => { setFormFor(null); done(`“${name}” saved.`) }}
          onCancel={() => setFormFor(null)}
        />
      </Modal>

      <Modal open={Boolean(deleting)} onClose={() => setDeleting(null)} title="Delete these details?">
        <ConfirmDialog
          message={<>The details <b>{deleting?.name}</b> will be deleted.</>}
          confirmLabel="Delete details"
          onConfirm={confirmDelete}
          onCancel={() => setDeleting(null)}
        />
      </Modal>
    </Section>
  )
}

function ProfileForm({ profile, onSaved, onCancel }) {
  const [values, setValues] = useState({
    name: profile?.name ?? '',
    job_position: profile?.job_position ?? '',
    experience_years: profile ? String(profile.experience_years) : '',
    skills: profile?.skills.join(', ') ?? '',
    linkedin_url: profile?.linkedin_url ?? '',
  })
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const edit = (field) => (event) => {
    setValues((prev) => ({ ...prev, [field]: event.target.value }))
    setFieldErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  function validate() {
    const errors = {}
    const years = Number(values.experience_years)
    if (!values.name.trim()) errors.name = 'Give this set a name, like “Backend roles”.'
    if (values.job_position.trim().length < 2) errors.job_position = 'Enter the job you’re applying for.'
    if (values.experience_years.trim() === '' || Number.isNaN(years) || years < 0 || years > 50) {
      errors.experience_years = 'Enter your years of experience, like 3 or 2.5.'
    }
    if (!values.skills.split(',').some((s) => s.trim())) errors.skills = 'Add at least one skill.'
    if (values.linkedin_url.trim() && !/^https?:\/\/\S+$/.test(values.linkedin_url.trim())) {
      errors.linkedin_url = 'Paste the full link, starting with https://'
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
    const body = {
      name: values.name.trim(),
      job_position: values.job_position.trim(),
      experience_years: Number(values.experience_years),
      skills: values.skills.split(',').map((s) => s.trim()).filter(Boolean),
      linkedin_url: values.linkedin_url.trim() || null,
    }
    try {
      if (profile) await senderProfilesApi.update(profile.id, body)
      else await senderProfilesApi.create(body)
      onSaved(body.name)
    } catch (err) {
      setError(getErrorMessage(err))
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="flex flex-col gap-4 px-5 py-4">
        <Alert>{error}</Alert>
        <Field id="sp-name" label="Name for this set" hint="Only you see this." error={fieldErrors.name}>
          <Input id="sp-name" value={values.name} onChange={edit('name')} aria-invalid={Boolean(fieldErrors.name)} placeholder="Backend roles" />
        </Field>
        <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_8rem]">
          <Field id="sp-job" label="Job you’re applying for" error={fieldErrors.job_position}>
            <Input id="sp-job" value={values.job_position} onChange={edit('job_position')} aria-invalid={Boolean(fieldErrors.job_position)} placeholder="Backend Developer" />
          </Field>
          <Field id="sp-years" label="Experience (years)" error={fieldErrors.experience_years}>
            <Input id="sp-years" type="number" min="0" max="50" step="0.5" inputMode="decimal" value={values.experience_years} onChange={edit('experience_years')} aria-invalid={Boolean(fieldErrors.experience_years)} placeholder="3" />
          </Field>
        </div>
        <Field id="sp-skills" label="Skills" hint="Separate them with commas." error={fieldErrors.skills}>
          <Input id="sp-skills" value={values.skills} onChange={edit('skills')} aria-invalid={Boolean(fieldErrors.skills)} placeholder="Python, FastAPI, PostgreSQL" />
        </Field>
        <Field id="sp-linkedin" label="LinkedIn (optional)" error={fieldErrors.linkedin_url}>
          <Input id="sp-linkedin" type="url" value={values.linkedin_url} onChange={edit('linkedin_url')} aria-invalid={Boolean(fieldErrors.linkedin_url)} placeholder="https://www.linkedin.com/in/your-name" />
        </Field>
      </div>
      <div className="flex justify-end gap-2 border-t border-line px-5 py-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={saving}>
          Save details
        </Button>
      </div>
    </form>
  )
}

