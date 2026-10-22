import { useState } from 'react'
import { getErrorMessage } from '../api/client'
import Alert from './Alert'
import Button from './Button'

/*
    The body and buttons of a "Are you sure?" popup; put it inside <Modal>.
    onConfirm returns a promise (the backend call); errors are shown here and the popup stays open.
*/
export default function ConfirmDialog({ message, confirmLabel, onConfirm, onCancel }) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleConfirm() {
    setError('')
    setBusy(true)
    try {
      await onConfirm()
    } catch (err) {
      setError(getErrorMessage(err))
      setBusy(false)
    }
  }

  return (
    <>
      <div className="flex flex-col gap-3 px-5 py-4">
        <Alert>{error}</Alert>
        <p>{message}</p>
        <p className="text-[13px] text-muted">This can’t be undone.</p>
      </div>
      <div className="flex justify-end gap-2 border-t border-line px-5 py-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="button" variant="danger" loading={busy} onClick={handleConfirm}>
          {confirmLabel}
        </Button>
      </div>
    </>
  )
}
