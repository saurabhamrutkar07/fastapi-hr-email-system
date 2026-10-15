import { useState } from "react";
import { contactsApi } from "../api/contacts";
import { getErrorMessage } from "../api/client";
import Alert from "./Alert";
import Button from "./Button";
import { contactEmails, contactPhones } from "./ContactList";
import Field from "./Field";
import Icon from "./Icon";
import Input from "./Input";

const MAX_ROWS = 5 // emails or phones per contact
const EMAIL_PATTERN = /^\S+@\S+\.\S+$/
const PHONE_PATTERN = /^\+?[\d\s-]{6,20}$/

// Form values for a new contact, or for editing an existing one 
function startingValues(contact) {
    if (!contact) return { name : '', title: '', company: '', emails:[''], phones:[''] }
    const phones = contactPhones(contact)
    return {
        name: contact.name,
        title: contact.title ?? '',
        company: contact.company ?? '',
        emails: contactEmails(contact),
        phones: phones.length? phones: [''],
    }
}

// Checks the form. Returns { name?: msg, 'email-0'?: msg, 'phone-1'?: msg, ... }
function validate(form) {
    const errors = {}
    const name = form.name.trim()
    if (name.length < 2) errors.name = 'Enter the recruiter’s name (at least 2 letters).' 
    else if (name.length > 100) errors.name = 'Keep the name under 100 characters.'
    if (form.title.trim().length > 150) errors.title = 'Keep the title under 150 characters.'
    if (form.company.trim().length > 150) errors.company = 'Keep the company under 150 characters.'

    const seen = new Set()
    form.emails.forEach((value,i) =>{
        const email = value.trim().toLowerCase()
        if (!email){
            if (i === 0) errors['email-0'] = 'Enter the main email address.'
        } else if (!EMAIL_PATTERN.test(email)){
            errors[`email-${i}`] = 'Enter a valid email address, like name@company.com.'
        } else if (seen.has(email)){
            errors[`email-${i}`] = 'This email is already in the list.'
        }
        seen.add(email)
    })

    form.phones.forEach((value,i) => {
        const phone = value.trim()
        if (phone && !PHONE_PATTERN.test(phone)) errors[`phone-${i}`] = 'Use digits only, like +91 98765 43210.'
    })
    return errors 
}

// The body the backend expects. Empty rows are dropped; the first email / phone is the main one.
function toPayload(form) {
    const emails = form.emails.map((e) => e.trim()).filter(Boolean)
    const phones = form.phones.map((p) => p.trim()).filter(Boolean)
    return {
        name: form.name.trim(),
        title: form.title.trim() || null,
        company_name: form.company.trim() || null,
        email: emails[0],
        additional_emails: emails.slice(1),
        contact_number: phones[0] ?? null,
        additional_phones: phones.slice(1),
    }
}

/*
    Add a contact, or edit one when `contact` is given (admins only).
    Calls onSaved({ merged }) after the backend accepts it.
*/
export default function ContactForm({ contact, onSaved, onCancel }) {
    const [form, setForm] = useState(() => startingValues(contact))
    const [fieldErrors, setFieldErrors] = useState({})
    const [error, setError] = useState('')
    const [saving, setSaving] = useState(false)
    
    // Update one value and clear its error while the user types
    function edit(key,value) {
        setForm((prev) => ({...prev, [key]: value}))
        setFieldErrors((prev)=> ({ ...prev, [key]: undefined }))
    }

    // Same for one row of the emails / phones lists. `list` is 'emails' or 'phones'
    function editRow(list,index,value) {
        setForm((prev) => ({ ...prev, [list]: prev[list].map((v,i) => (i === index ? value : v) )}))
        setFieldErrors((prev) => ({ ...prev, [`${list.slice(0, -1)}-${index}`]: undefined }))
    } 
    function addRow(list) {
        setForm((prev) => ({...prev, [list]: [...prev[list], '']}))
    }
    function removeRow(list,index) {
        setForm((prev) => ({ ...prev, [list]: prev[list].filter((_, i) => i !== index) }))
        setFieldErrors({}) // row numbers have shifted, so old errors would point at the wrong rows
    }

    async function handleSubmit(event) {
        event.preventDefault()
        const errors = validate(form)
        setFieldErrors(errors)
        if (Object.keys(errors).length > 0) return
        setError('')
        setSaving(true)

        try{
            const payload = toPayload(form)
            const result = contact ? await contactsApi.update(contact.id, payload): await contactsApi.add(payload)
            onSaved({ merged: Boolean(result.merged)})
        } catch (err) {
            setError(getErrorMessage(err))
            setSaving(false)
        }
    }

    return(
        <form onSubmit={handleSubmit} noValidate>
            <div className="flex flex-col gap-4 px-5 py-4">
                <Alert>{error}</Alert>   

                <Field id="contact-name" label="Name *" error={fieldErrors.name}>
                <Input
                    id="contact-name"
                    value={form.name}
                    onChange={(e) => edit('name', e.target.value)}
                    aria-invalid={Boolean(fieldErrors.name)}
                    placeholder="Priya Sharma"
                />
                </Field>

                <div className="grid gap-4 sm:grid-cols-2">
                    <Field id="contact-title" label="Job title" error={fieldErrors.title}>
                        <Input
                        id="contact-title"
                        value={form.title}
                        onChange={(e) => edit('title', e.target.value)}
                        aria-invalid={Boolean(fieldErrors.title)}
                        placeholder="Talent Acquisition Lead"
                        />
                    </Field>
                    <Field id="contact-company" label="Company" error={fieldErrors.company}>
                        <Input
                        id="contact-company"
                        value={form.company}
                        onChange={(e) => edit('company', e.target.value)}
                        aria-invalid={Boolean(fieldErrors.company)}
                        placeholder="Zoho"
                        />
                    </Field>
                </div>

                <RowList
                    label="Email *"
                    hint="Cold emails are sent to the first address."
                    addLabel="Add another email"
                    type="email"
                    placeholder="name@company.com"
                    prefix="email"
                    values={form.emails}
                    errors={fieldErrors}
                    onChange={(i, value) => editRow('emails', i, value)}
                    onAdd={() => addRow('emails')}
                    onRemove={(i) => removeRow('emails', i)}
                    />

                <RowList
                    label="Phone"
                    addLabel="Add another phone"
                    type="tel"
                    placeholder="+91 98765 43210"
                    prefix="phone"
                    values={form.phones}
                    errors={fieldErrors}
                    onChange={(i, value) => editRow('phones', i, value)}
                    onAdd={() => addRow('phones')}
                    onRemove={(i) => removeRow('phones', i)}
                />
            </div>     

            <div className="flex justify-end gap-2 border-t border-line px-5 py-4">
                <Button type="button" variant="secondary" onClick={onCancel}>
                Cancel
                </Button>
                <Button type="submit" loading={saving}>
                {contact ? 'Save changes' : 'Add contact'}
                </Button>
            </div>    

        </form>
    )
}

// A label, one input per value with a remove button (not on the first), and an "add another" link
function RowList({ label, hint, addLabel, type, placeholder, prefix, values, errors, onChange, onAdd, onRemove }) {
    const firstId = `contact-${prefix}-0`
    return (
        <div className="flex flex-col gap-1.5">
            <label htmlFor={firstId} className="text-[13px] font-semibold">
                {label}
            </label>
            {values.map((value, i) => {
                const error = errors[`${prefix}-${i}`]
                return (
                <div key={i}>
                    <div className="flex gap-2">
                    <Input
                        id={`contact-${prefix}-${i}`}
                        type={type}
                        value={value}
                        onChange={(e) => onChange(i, e.target.value)}
                        aria-invalid={Boolean(error)}
                        aria-label={i === 0 ? undefined : `${label.replace(' *', '')} ${i + 1}`}
                        placeholder={placeholder}
                    />
                    {i > 0 && (
                        <button
                        type="button"
                        onClick={() => onRemove(i)}
                        aria-label={`Remove ${value || 'this row'}`}
                        className="grid size-11 shrink-0 place-items-center rounded-lg border border-line text-muted hover:bg-surface-2 hover:text-err-text"
                        >
                        <Icon name="x" />
                        </button>
                    )}
                    </div>
                    {error && <p className="mt-1 text-xs text-err-text">{error}</p>}
                </div>
                )
            })}
            {hint && <p className="text-xs text-muted">{hint}</p>}
            {values.length < MAX_ROWS && (
                <button
                type="button"
                onClick={onAdd}
                className="flex w-fit items-center gap-1.5 text-[13px] font-semibold text-link hover:underline"
                >
                <Icon name="plus" className="size-4" />
                {addLabel}
                </button>
            )}
        </div>
    )        
}
