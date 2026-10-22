import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { getErrorMessage } from '../api/client'
import { templatesApi } from '../api/templates'
import Alert from '../components/Alert'
import Button from '../components/Button'
import EmailPreview from '../components/EmailPreview'
import Field from '../components/Field'
import Input from '../components/Input'
import Textarea from '../components/Textarea'
import useApi from '../hooks/useApi'

// Buttons that insert a variable; the backend fills each one in per recruiter
const VARIABLES = [
  { label: 'Recruiter name', code: '{{ hr_name }}' },
  { label: 'Company', code: '{{ company_name }}' },
  { label: 'Job position', code: '{{ job_position }}' },
  { label: 'Years of experience', code: '{{ experience_years }}' },
  { label: 'Skills', code: '{{ skills | join(", ") }}' },
  { label: 'Your name', code: '{{ applicant_name }}' },
  { label: 'Your email', code: '{{ email }}' },
  { label: 'Your phone', code: '{{ contact_number }}' },
  { label: 'LinkedIn', code: '{{ linkedin_url }}' },
]

const STARTER = `Hi {{ hr_name }},

I'm {{ applicant_name }}, a {{ job_position }} with {{ experience_years }} years of experience in {{ skills | join(", ") }}.

I came across {{ company_name }} and would love to be considered for any open {{ job_position }} roles. My resume is attached.

Thanks for your time,
{{ applicant_name }}
{{ contact_number }} · {{ linkedin_url }}`

const PREVIEW_DELAY_MS = 500

// /templates/new writes a new template; /templates/:id edits one
export default function TemplateEditorPage() {
  const { id } = useParams()
  const editing = Boolean(id)
  const templates = useApi(templatesApi.list)
  const existing = editing ? templates.data?.find((t) => String(t.id) === id) : null

  if (editing && templates.loading) return <p className="text-muted">Loading…</p>
  if (editing && (templates.error || !existing)) {
    return (
      <div className="flex flex-col items-start gap-3">
        <Alert>{templates.error || 'This template doesn’t exist any more.'}</Alert>
        <Link to="/templates" className="font-semibold text-link hover:underline">
          Back to templates
        </Link>
      </div>
    )
  }

  // `key` gives a fresh form if the user goes from one template's editor to another's
  return <TemplateForm key={id ?? 'new'} template={existing} firstTemplate={!editing && templates.data?.length === 0} />
}

function TemplateForm({ template, firstTemplate }) {
  const navigate = useNavigate()
  const [name, setName] = useState(template?.name ?? '')
  const [subject, setSubject] = useState(template?.subject ?? '')
  const [content, setContent] = useState(template?.content ?? STARTER)
  const [makeDefault, setMakeDefault] = useState(false)
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [preview, setPreview] = useState({ data: null, error: '', loading: false })

  // The box a variable button inserts into: whichever of subject / body was used last
  const subjectRef = useRef(null)
  const bodyRef = useRef(null)
  const lastBox = useRef('body')

  // Fill the template in again half a second after the user stops typing
  useEffect(() => {
    if (!content.trim()) return
    let cancelled = false
    const timer = setTimeout(() => {
      setPreview((prev) => ({ ...prev, loading: true }))
      templatesApi
        .preview({ subject: subject.trim() || null, content })
        .then((data) => !cancelled && setPreview({ data, error: '', loading: false }))
        .catch((err) => !cancelled && setPreview({ data: null, error: getErrorMessage(err), loading: false }))
    }, PREVIEW_DELAY_MS)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [subject, content])

  // Put `code` where the cursor is in the subject or body (at the end if neither has the cursor),
  // then put the cursor after it
  function insertVariable(code) {
    const isSubject = lastBox.current === 'subject'
    const box = isSubject ? subjectRef.current : bodyRef.current
    const value = isSubject ? subject : content
    const hasCursor = document.activeElement === box
    const start = hasCursor ? box.selectionStart : value.length
    const end = hasCursor ? box.selectionEnd : value.length
    const next = value.slice(0, start) + code + value.slice(end)
    if (isSubject) setSubject(next)
    else setContent(next)
    requestAnimationFrame(() => {
      box.focus()
      box.setSelectionRange(start + code.length, start + code.length)
    })
  }

  const edit = (setValue, field) => (event) => {
    setValue(event.target.value)
    setFieldErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  function validate() {
    const errors = {}
    if (!name.trim()) errors.name = 'Give the template a name, like “Backend roles”.'
    if (!content.trim()) errors.content = 'Write the email.'
    return errors
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const errors = validate()
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return
    setError('')
    setSaving(true)
    const body = { name: name.trim(), subject: subject.trim() || null, content }
    try {
      if (template) await templatesApi.update(template.id, body)
      else await templatesApi.create({ ...body, is_default: makeDefault })
      navigate('/templates', { state: { notice: `“${body.name}” saved.` } })
    } catch (err) {
      setError(getErrorMessage(err))
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <Link to="/templates" className="text-[13px] font-semibold text-link hover:underline">
          ← Templates
        </Link>
        <h2 className="mt-1 font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">
          {template ? `Edit “${template.name}”` : 'New template'}
        </h2>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <form onSubmit={handleSubmit} noValidate className="flex min-w-0 flex-col gap-4 rounded-xl border border-line bg-surface p-4 sm:p-5">
          <Alert>{error}</Alert>

          <Field id="template-name" label="Template name" hint="Only you see this." error={fieldErrors.name}>
            <Input
              id="template-name"
              value={name}
              onChange={edit(setName, 'name')}
              aria-invalid={Boolean(fieldErrors.name)}
              placeholder="Backend roles"
            />
          </Field>

          <Field id="template-subject" label="Subject (optional)" hint="Left empty, emails use “Job position | Inquiry About Openings - Your name”.">
            <Input
              id="template-subject"
              ref={subjectRef}
              value={subject}
              onChange={edit(setSubject, 'subject')}
              onFocus={() => (lastBox.current = 'subject')}
              placeholder="{{ job_position }} role at {{ company_name }}"
            />
          </Field>

          <div className="flex flex-col gap-1.5">
            <span className="text-[13px] font-semibold">Insert a variable</span>
            <div className="flex flex-wrap gap-1.5">
              {VARIABLES.map((variable) => (
                <button
                  key={variable.code}
                  type="button"
                  // Keep the cursor in the text box while clicking the button
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => insertVariable(variable.code)}
                  className="rounded-full border border-line bg-surface-2 px-2.5 py-1 text-[12.5px] font-semibold hover:border-primary hover:text-primary"
                >
                  + {variable.label}
                </button>
              ))}
            </div>
          </div>

          <Field id="template-content" label="Email" error={fieldErrors.content}>
            <Textarea
              id="template-content"
              ref={bodyRef}
              rows={14}
              value={content}
              onChange={edit(setContent, 'content')}
              onFocus={() => (lastBox.current = 'body')}
              aria-invalid={Boolean(fieldErrors.content)}
              className="font-mono text-[13.5px] leading-relaxed"
            />
          </Field>

          {!template && !firstTemplate && (
            <label className="flex items-center gap-2 text-[13.5px]">
              <input type="checkbox" checked={makeDefault} onChange={(e) => setMakeDefault(e.target.checked)} className="size-4" />
              Use this as my default template
            </label>
          )}
          {firstTemplate && <p className="text-[13px] text-muted">Your first template becomes your default.</p>}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => navigate('/templates')}>
              Cancel
            </Button>
            <Button type="submit" loading={saving}>
              Save template
            </Button>
          </div>
        </form>

        <div className="flex min-w-0 flex-col gap-2 xl:sticky xl:top-0 xl:self-start">
          <p className="text-[13px] font-semibold">Preview</p>
          <EmailPreview preview={preview.data} error={preview.error} loading={preview.loading} />
          <p className="text-[12.5px] text-muted">
            Your name, email and phone come from your profile. Job position, experience, skills and LinkedIn are
            filled in when you send.
          </p>
        </div>
      </div>
    </div>
  )
}
