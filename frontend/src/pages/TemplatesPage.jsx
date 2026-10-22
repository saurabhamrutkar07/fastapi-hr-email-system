import { useState } from 'react'
import { useLocation } from 'react-router'
import { getErrorMessage } from '../api/client'
import { templatesApi } from '../api/templates'
import Alert from '../components/Alert'
import Button, { ButtonLink } from '../components/Button'
import ConfirmDialog from '../components/ConfirmDialog'
import EmailPreview from '../components/EmailPreview'
import Icon from '../components/Icon'
import Modal from '../components/Modal'
import useApi from '../hooks/useApi'

// The user's email templates: preview, edit, choose the default, delete
export default function TemplatesPage() {
  const location = useLocation()
  const templates = useApi(templatesApi.list)
  // The editor sends us back here with { notice: 'Template saved.' }
  const [notice, setNotice] = useState(location.state?.notice ?? '')
  const [error, setError] = useState('')
  const [previewing, setPreviewing] = useState(null)
  const [deleting, setDeleting] = useState(null)

  // Default first, then A to Z
  const list = [...(templates.data ?? [])].sort((a, b) => b.is_default - a.is_default || a.name.localeCompare(b.name))

  async function makeDefault(template) {
    setNotice('')
    setError('')
    try {
      await templatesApi.setDefault(template.id)
      setNotice(`“${template.name}” is now your default template.`)
      templates.reload()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function confirmDelete() {
    await templatesApi.remove(deleting.id)
    setNotice(`“${deleting.name}” deleted.`)
    setDeleting(null)
    templates.reload()
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">Templates</h2>
          <p className="mt-0.5 text-muted">Write once. The recruiter’s name and company are filled in for each email.</p>
        </div>
        <ButtonLink to="/templates/new">
          <Icon name="plus" />
          New template
        </ButtonLink>
      </div>

      <Alert tone="success">{notice}</Alert>
      <Alert>{error}</Alert>

      {templates.error ? (
        <div className="flex flex-col items-start gap-3">
          <Alert>Couldn’t load your templates. {templates.error}</Alert>
          <Button variant="secondary" onClick={templates.reload}>
            Try again
          </Button>
        </div>
      ) : templates.loading ? (
        <div className="grid gap-3 md:grid-cols-2" aria-hidden="true">
          {[1, 2].map((n) => (
            <div key={n} className="h-40 animate-pulse rounded-xl border border-line bg-surface" />
          ))}
        </div>
      ) : list.length === 0 ? (
        <div className="flex flex-col items-center gap-1 rounded-xl border border-dashed border-line bg-surface px-5 py-12 text-center">
          <p className="font-semibold">No templates yet</p>
          <p className="max-w-md text-[13px] text-muted">
            Emails can’t be sent without one. Your first template becomes the default that every email uses.
          </p>
          <ButtonLink to="/templates/new" className="mt-3">
            Write your first template
          </ButtonLink>
        </div>
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">
          {list.map((template) => (
            <li key={template.id} className="flex min-w-0 flex-col gap-3 rounded-xl border border-line bg-surface p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate font-semibold">{template.name}</p>
                  <p className="truncate text-[13px] text-muted">{template.subject || 'Default subject'}</p>
                </div>
                {template.is_default && (
                  <span className="shrink-0 rounded-full bg-ok-soft px-2.5 py-0.5 text-[12px] font-semibold text-ok-text">
                    Default
                  </span>
                )}
              </div>
              <p className="line-clamp-3 whitespace-pre-line text-[13px] text-muted">{template.content}</p>
              <div className="mt-auto flex flex-wrap items-center gap-2 border-t border-line pt-3">
                <Button variant="secondary" className="px-3 py-1.5 text-[13px]" onClick={() => setPreviewing(template)}>
                  <Icon name="eye" className="size-4" />
                  Preview
                </Button>
                <ButtonLink to={`/templates/${template.id}`} variant="secondary" className="px-3 py-1.5 text-[13px]">
                  <Icon name="edit" className="size-4" />
                  Edit
                </ButtonLink>
                {!template.is_default && (
                  <button
                    type="button"
                    onClick={() => makeDefault(template)}
                    className="text-[13px] font-semibold text-link hover:underline"
                  >
                    Make default
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setDeleting(template)}
                  disabled={template.is_default}
                  aria-label={`Delete ${template.name}`}
                  title={template.is_default ? 'Make another template the default before deleting this one' : 'Delete'}
                  className="ml-auto grid size-8 place-items-center rounded-lg text-muted hover:bg-err-soft hover:text-err-text disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-muted"
                >
                  <Icon name="trash" className="size-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={Boolean(previewing)}
        onClose={() => setPreviewing(null)}
        title={previewing ? `Preview: ${previewing.name}` : ''}
        description="How this email reads for a sample recruiter."
      >
        <TemplatePreview template={previewing} />
      </Modal>

      <Modal open={Boolean(deleting)} onClose={() => setDeleting(null)} title="Delete this template?">
        <ConfirmDialog
          message={<>The template <b>{deleting?.name}</b> will be deleted.</>}
          confirmLabel="Delete template"
          onConfirm={confirmDelete}
          onCancel={() => setDeleting(null)}
        />
      </Modal>
    </div>
  )
}

// Fills the template in once when the popup opens
function TemplatePreview({ template }) {
  const preview = useApi(() => templatesApi.preview({ subject: template.subject, content: template.content }))
  return (
    <div className="px-5 py-4">
      <EmailPreview preview={preview.data} error={preview.error} loading={preview.loading} />
    </div>
  )
}
