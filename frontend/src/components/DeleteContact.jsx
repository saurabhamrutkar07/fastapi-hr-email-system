import { useState } from 'react'
import { contactsApi } from '../api/contacts'
import { getErrorMessage } from '../api/client'
import Alert from './Alert'
import Button from './Button'
import { contactEmails, contactPhones } from './ContactList'

// "2 emails" / "1 phone"
const count = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

/*
    Asks before deleting a contact (admins only). Calls onDeleted() once the backend has removed it.
*/
export default function DeleteContact({ contact, onDeleted, onCancel }) {
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  const emails = contactEmails(contact).length
  const phones = contactPhones(contact).length

  async function handleDelete() {
    setError('')
    setDeleting(true)
    try {
      await contactsApi.remove(contact.id)
      onDeleted()
    } catch (err) {
      setError(getErrorMessage(err))
      setDeleting(false)
    }
  }

  return (
    <>
      <div className="flex flex-col gap-3 px-5 py-4">
        <Alert>{error}</Alert>
        <p>
          <b>{contact.name}</b>
          {contact.company && ` (${contact.company})`} and their {count(emails, 'email')}
          {phones > 0 && ` and ${count(phones, 'phone')}`} will be removed for everyone.
        </p>
        <p className="text-[13px] text-muted">This can’t be undone. Emails already sent stay in History.</p>
      </div>
      <div className="flex justify-end gap-2 border-t border-line px-5 py-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="button" variant="danger" loading={deleting} onClick={handleDelete}>
          Delete contact
        </Button>
      </div>
    </>
  )
}
