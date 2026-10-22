import { useState } from 'react'
import { getErrorMessage } from '../api/client'
import { resumesApi } from '../api/resumes'
import Alert from '../components/Alert'
import Button from '../components/Button'
import ConfirmDialog from '../components/ConfirmDialog'
import Icon from '../components/Icon'
import Modal from '../components/Modal'
import useApi from '../hooks/useApi'
import { formatDateTime } from '../utils/format'

const MAX_MB = 5

// Resume versions: upload a new one, open any version, choose the active one, delete old ones
export default function ResumesPage() {
  const resumes = useApi(resumesApi.list)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [deleting, setDeleting] = useState(null)

  // Runs a backend call and reports what happened at the top of the page
  async function run(action, doneMessage) {
    setNotice('')
    setError('')
    try {
      await action()
      setNotice(doneMessage)
      resumes.reload()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  async function chooseFile(event) {
    const file = event.target.files[0]
    event.target.value = '' // lets the same file be picked again
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setNotice('')
      setError(`${file.name} isn’t a PDF. Save your resume as PDF and upload that.`)
      return
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setNotice('')
      setError(`${file.name} is larger than ${MAX_MB} MB. Make it smaller (for example, compress the images) and try again.`)
      return
    }
    setUploading(true)
    await run(() => resumesApi.upload(file), 'Resume uploaded. It is now attached to every email.')
    setUploading(false)
  }

  // Open the tab right away (browsers block tabs opened after a wait), then point it at the PDF
  async function view(resume) {
    const tab = window.open('', '_blank')
    try {
      const { url } = await resumesApi.viewUrl(resume.id)
      tab.location.href = url
    } catch (err) {
      tab.close()
      setNotice('')
      setError(getErrorMessage(err))
    }
  }

  async function confirmDelete() {
    await resumesApi.remove(deleting.id)
    setNotice(`Version ${deleting.version_number} deleted.`)
    setDeleting(null)
    resumes.reload()
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        <h2 className="font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">Resumes</h2>
        <p className="mt-0.5 text-muted">The active version is attached to every email you send.</p>
      </div>

      <Alert tone="success">{notice}</Alert>
      <Alert>{error}</Alert>

      <label
        className={`flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed border-line bg-surface px-4 py-7 text-center hover:border-primary hover:bg-surface-2 ${uploading ? 'pointer-events-none opacity-60' : ''}`}
      >
        <Icon name="upload" className="size-6 text-muted" />
        <span className="font-semibold">{uploading ? 'Uploading…' : 'Upload a new version'}</span>
        <span className="text-[13px] text-muted">PDF, up to {MAX_MB} MB. It becomes the active resume.</span>
        <input type="file" accept="application/pdf,.pdf" onChange={chooseFile} disabled={uploading} className="sr-only" />
      </label>

      {resumes.error ? (
        <div className="flex flex-col items-start gap-3">
          <Alert>Couldn’t load your resumes. {resumes.error}</Alert>
          <Button variant="secondary" onClick={resumes.reload}>
            Try again
          </Button>
        </div>
      ) : resumes.loading ? (
        <div className="h-32 animate-pulse rounded-xl border border-line bg-surface" aria-hidden="true" />
      ) : resumes.data.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line bg-surface px-5 py-8 text-center text-[13.5px] text-muted">
          No resume yet. Emails can’t be sent until you upload one.
        </p>
      ) : (
        <ul className="divide-y divide-line rounded-xl border border-line bg-surface">
          {resumes.data.map((resume) => (
            <li key={resume.id} className="flex flex-wrap items-center gap-3 px-4 py-3 sm:px-5">
              <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-brand-soft text-brand-ink">
                <Icon name="resume" className="size-[18px]" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="flex items-center gap-2 font-semibold">
                  Version {resume.version_number}
                  {resume.is_active && (
                    <span className="rounded-full bg-ok-soft px-2.5 py-0.5 text-[12px] font-semibold text-ok-text">Active</span>
                  )}
                </p>
                <p className="text-[12.5px] text-muted">Uploaded {formatDateTime(resume.uploaded_at)}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="secondary" className="px-3 py-1.5 text-[13px]" onClick={() => view(resume)}>
                  <Icon name="eye" className="size-4" />
                  View
                </Button>
                {!resume.is_active && (
                  <button
                    type="button"
                    onClick={() => run(() => resumesApi.setActive(resume.id), `Version ${resume.version_number} is now active.`)}
                    className="text-[13px] font-semibold text-link hover:underline"
                  >
                    Make active
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setDeleting(resume)}
                  disabled={resume.is_active}
                  aria-label={`Delete version ${resume.version_number}`}
                  title={resume.is_active ? 'Make another version active before deleting this one' : 'Delete'}
                  className="grid size-8 place-items-center rounded-lg text-muted hover:bg-err-soft hover:text-err-text disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-muted"
                >
                  <Icon name="trash" className="size-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Modal open={Boolean(deleting)} onClose={() => setDeleting(null)} title="Delete this resume version?">
        <ConfirmDialog
          message={<>Version {deleting?.version_number} will be deleted from your account and storage.</>}
          confirmLabel="Delete version"
          onConfirm={confirmDelete}
          onCancel={() => setDeleting(null)}
        />
      </Modal>
    </div>
  )
}
