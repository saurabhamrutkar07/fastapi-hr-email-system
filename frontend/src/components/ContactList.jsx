import { formatDate } from "../utils/format";
import Icon from "./Icon";

// A contact's emails / phones, primary first. Older contacts may only have the single `email` / `phone` column.
export function contactEmails(contact) {
  if (!contact.emails.length) return [contact.email]
  return [...contact.emails].sort((a, b) => b.is_primary - a.is_primary).map((e) => e.email)
}

export function contactPhones(contact) {
  if (!contact.phones.length) return contact.phone ? [contact.phone] : []
  return [...contact.phones].sort((a, b) => b.is_primary - a.is_primary).map((p) => p.phone)
}


// "Priya Sharma" -> "PS"
function initials(name){
    return name
    .split(' ')
    .filter(Boolean)
    .slice(0,2)
    .map((word)=> word[0].toUpperCase())
    .join('')
}

/*
    One page of contacts: a table on wide screens, cards on phones and tablets.
    `showAdded` adds the "Added on" date (admins only).
        `onEdit(contact)` / `onDelete(contact)` add Edit and Delete buttons to each contact (admins only).
*/
export default function ContactList({contacts, showAdded, onEdit, onDelete}) {
    return(
        <>
            <div className="hidden overflow-x-auto xl:block">
               <table className="w-full text-left text-[13.5px]">
                    <thead className="border-b border-line text-[12px] font-semibold uppercase tracking-wide text-muted">
                        <tr>
                            <th className="px-5 py-3 font-semibold">Name</th>
                            <th className="px-3 py-3 font-semibold">Company</th>
                            <th className="px-3 py-3 font-semibold">Emails</th>
                            <th className="px-3 py-3 font-semibold">Phones</th>
                            {showAdded && <th className="px-5 py-3 font-semibold">Added on</th>}
                            {onEdit && <th className="w-px px-3 py-3"><span className="sr-only">Actions</span></th>}

                        </tr>
                    </thead>
                    <tbody>
                        {contacts.map((contact) => (
                            <tr key={contact.id} className="border-b border-line align-top last:border-b-0">
                                <td className="px-5 py-3">
                                    <Person contact={contact} /> 
                                </td>  
                                <td className="px-3 py-3">{contact.company || <Empty />}</td>
                                <td className="px-3 py-3">
                                    <Lines items={contactEmails(contact)} />
                                </td>
                                <td className="whitespace-nowrap px-3 py-3 tabular-nums">
                                    <Lines items={contactPhones(contact)} />
                                </td>
                                {showAdded && (
                                    <td className="whitespace-nowrap px-5 py-3 text-muted tabular-nums">
                                        {contact.created_at ? formatDate(contact.created_at) : <Empty />}
                                    </td>  
                                )}
                                {onEdit && (
                                    <td className="px-3 py-2">
                                        <RowActions contact={contact} onEdit={onEdit} onDelete={onDelete} />
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table> 
            </div>
            
            {/* Phones: a plain list with dividers. Tablets: two columns of cards */}
            <ul className="divide-y divide-line sm:grid sm:grid-cols-2 sm:gap-3 sm:divide-y-0 sm:p-4 xl:hidden">
                {contacts.map((contact) => {
                    const phones = contactPhones(contact)
                    return(
                        <li key={contact.id} className="flex min-w-0 flex-col gap-3 p-4 sm:rounded-xl sm:border sm:border-line">
                            <div className="flex items-start justify-between gap-2">
                                <Person contact={contact} withCompany />
                                {onEdit && <RowActions contact={contact} onEdit={onEdit} onDelete={onDelete} />}
                            </div>
                            <div className="flex flex-col gap-1 text-[13.5px]">
                                <Lines items={contactEmails(contact)} />
                                {phones.length > 0 && (
                                    <div className="tabular-nums text-muted">
                                        <Lines items={phones}/>
                                    </div>
                                )}       
                            </div>
                            {showAdded && contact.created_at && (
                                <p className="text-[12px] text-muted">Added {formatDate(contact.created_at)}</p>
                            )}
                        </li>  
                    )
                })}
            </ul>

        </>
    )   
}

// Buttons that change one contact (admins only)
function RowActions({ contact, onEdit, onDelete }) {
    return (
        <div className="flex justify-end gap-1">
            <button
                type="button"
                onClick={() => onEdit(contact)}
                aria-label={`Edit ${contact.name}`}
                title="Edit"
                className="grid size-8 place-items-center rounded-lg text-muted hover:bg-surface-2 hover:text-fg"
            >
                <Icon name="edit" className="size-4" />
            </button>
            <button
                type="button"
                onClick={() => onDelete(contact)}
                aria-label={`Delete ${contact.name}`}
                title="Delete"
                className="grid size-8 place-items-center rounded-lg text-muted hover:bg-err-soft hover:text-err-text"
            >
                <Icon name="trash" className="size-4" />
            </button>
        </div>
    )
}
 
// Initials circle + name, with the title (and on cards the company) underneath
function Person({contact,withCompany = false}) {
    const subTitle = [contact.title, withCompany && contact.company].filter(Boolean).join(' · ')
    return(
        <div className="flex min-w-0 items-center gap-3">
            <span className="grid size-9 shrink-0 place-items-center rounded-full bg-brand-soft text-[12.5px] font-bold text-brand-ink">
                {initials(contact.name)}
            </span>
            <div className="min-w-0">
                <p className="truncate font-semibold">{contact.name}</p>
                {subTitle && <p className="truncate text-[12.5px] text-muted">{subTitle}</p>}   
            </div>
        </div>
    )
} 

// One value per line. A very long email wraps only when it cannot fit
function Lines({ items }) {
    if (!items.length) return <Empty/>
    return(
        <ul>
            {items.map((item) => (
                <li key={item} className="wrap-break-word">
                    {item}
                </li>
            ))}
        </ul>
    )
    
}

function Empty() {
    return <span className="text-muted">—</span>
    
}