import { useMemo, useState } from 'react'
import { formatDate } from '../../utils/format'
import Icon from '../Icon'
import Input from '../Input'
import Select from '../Select'

export const MAX_RECIPIENTS = 50

/*
    Tick the recruiters to email. Contacts emailed before show the date and are left out of
    "Select all", so nobody gets the same email twice by accident; they can still be ticked.
    `allowedEmails` (admin test mode) limits the list to those addresses.
*/
export default function RecipientPicker({ contacts, selected, onChange, lastSent, allowedEmails }) {
  const [search, setSearch] = useState('')
  const [company, setCompany] = useState('')
  const [note, setNote] = useState('')

  const available = useMemo(
    () => (allowedEmails ? contacts.filter((c) => allowedEmails.has(c.email.toLowerCase())) : contacts),
    [contacts, allowedEmails],
  )
  const companies = useMemo(
    () => [...new Set(available.map((c) => c.company).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
    [available],
  )
  const shown = useMemo(() => {
    const words = search.trim().toLowerCase()
    return available.filter((c) => {
      if (company && c.company !== company) return false
      return !words || [c.name, c.title, c.company, c.email].join(' ').toLowerCase().includes(words)
    })
  }, [available, search, company])

  const emailedOn = (contact) => lastSent[contact.email.toLowerCase()]
  const full = selected.size >= MAX_RECIPIENTS

  function toggle(contact) {
    const next = new Set(selected)
    if (next.has(contact.id)) next.delete(contact.id)
    else next.add(contact.id)
    setNote('')
    onChange(next)
  }

  // Adds the shown contacts that weren't emailed before, up to the limit
  function selectShown() {
    const next = new Set(selected)
    let skipped = 0
    for (const contact of shown) {
      if (next.size >= MAX_RECIPIENTS) break
      if (next.has(contact.id)) continue
      if (emailedOn(contact)) skipped += 1
      else next.add(contact.id)
    }
    onChange(next)
    const parts = []
    if (skipped) parts.push(`${skipped} emailed before ${skipped === 1 ? 'was' : 'were'} left out; tick them to email again`)
    if (next.size >= MAX_RECIPIENTS) parts.push(`you can send to ${MAX_RECIPIENTS} at a time`)
    setNote(parts.length ? `${parts.join(', and ')}.` : '')
  }

  return (
    <section className="min-w-0 overflow-hidden rounded-xl border border-line bg-surface">
      <div className="flex flex-col gap-2.5 border-b border-line p-3 sm:flex-row sm:p-4">
        <label className="relative min-w-0 flex-1">
          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted">
            <Icon name="search" />
          </span>
          <Input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search name, company or email" aria-label="Search recruiters" className="pl-10" />
        </label>
        <Select value={company} onChange={(e) => setCompany(e.target.value)} aria-label="Filter by company" className="sm:w-52">
          <option value="">All companies</option>
          {companies.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </Select>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2.5 text-[13px]">
        <span className="font-semibold tabular-nums">
          {selected.size} selected <span className="font-normal text-muted">(up to {MAX_RECIPIENTS})</span>
        </span>
        <div className="flex gap-3">
          <button type="button" onClick={selectShown} disabled={full || shown.length === 0} className="font-semibold text-link hover:underline disabled:cursor-not-allowed disabled:text-muted disabled:no-underline">
            Select all shown
          </button>
          {selected.size > 0 && (
            <button type="button" onClick={() => { onChange(new Set()); setNote('') }} className="font-semibold text-muted hover:text-fg">
              Clear
            </button>
          )}
        </div>
      </div>
      {note && <p className="border-b border-line bg-surface-2 px-4 py-2 text-[12.5px] text-muted">{note}</p>}

      {shown.length === 0 ? (
        <p className="px-4 py-10 text-center text-[13.5px] text-muted">
          {available.length === 0 ? 'No recruiters to show.' : 'No recruiters match.'}
        </p>
      ) : (
        <ul className="max-h-[28rem] divide-y divide-line overflow-y-auto">
          {shown.map((contact) => {
            const checked = selected.has(contact.id)
            const sentAt = emailedOn(contact)
            return (
              <li key={contact.id}>
                <label className={`flex cursor-pointer items-start gap-3 px-4 py-3 hover:bg-surface-2 ${!checked && full ? 'cursor-not-allowed opacity-50' : ''}`}>
                  <input type="checkbox" checked={checked} disabled={!checked && full} onChange={() => toggle(contact)} className="mt-1 size-4 shrink-0" />
                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                      <span className="font-semibold">{contact.name}</span>
                      {contact.company && <span className="text-[13px] text-muted">{contact.company}</span>}
                    </span>
                    <span className="block text-[13px] wrap-break-word text-muted">{contact.email}</span>
                  </span>
                  {sentAt && (
                    <span className="shrink-0 rounded-full bg-primary-soft px-2.5 py-0.5 text-[12px] font-semibold text-primary">
                      Emailed on {formatDate(sentAt)}
                    </span>
                  )}
                </label>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
