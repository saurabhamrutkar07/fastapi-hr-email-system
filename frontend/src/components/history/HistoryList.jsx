import { formatDateTime } from '../../utils/format'
import StatusPill from '../StatusPill'

/*
    Sent emails as a table on wide screens and as cards below that.
    Emails sent before History saved names only have the address.
    `showSender` adds who sent each one (admins see everyone's).
*/

export default function HistoryList({ items, showSender, onOpen}) {
    return (
        <>
            <div className="hidden overflow-x-auto lg:block">
                <table className="w-full text-left text-[13.5px]">
                    <thead className="border-b border-line text-[12px] font-semibold uppercase tracking-wide text-muted">
                        <tr>
                           <th className="px-5 py-3">Recruiter</th>
                            <th className="px-3 py-3">Subject</th>
                            {showSender && <th className="px-3 py-3">Sent by</th>}
                            <th className="px-3 py-3">Status</th>
                            <th className="px-5 py-3 text-right">When</th> 
                        </tr>
                    </thead>   
                    <tbody className="divide-y divide-line">
                       {items.map((item) => (
                        <tr key={item.request_id} onClick={() => onOpen(item)} className="cursor-pointer hover:bg-surface-2">
                            <td className="max-w-64 px-5 py-3">
                            {/* The row opens the email; the button lets keyboards reach it too */}
                            <button type="button" className="text-left font-semibold hover:underline">
                                {item.contact_name ?? item.recipient_email}
                            </button>
                            <p className="truncate text-[12.5px] text-muted">
                                {item.contact_name ? [item.company, item.recipient_email].filter(Boolean).join(' · ') : '—'}
                            </p>
                            </td>
                            <td className="max-w-80 truncate px-3 py-3">{item.subject ?? <span className="text-muted">—</span>}</td>
                            {showSender && <td className="px-3 py-3 text-muted">{item.sender_name ?? '—'}</td>}
                            <td className="px-3 py-3">
                            <StatusPill status={item.status} />
                            </td>
                            <td className="px-5 py-3 text-right whitespace-nowrap text-muted tabular-nums">{formatDateTime(item.created_at)}</td>
                        </tr>
                        ))} 
                    </tbody>
                </table>
            </div>

            <ul className="divide-y divide-line lg:hidden">
                {items.map((item) => (
                <li key={item.request_id}>
                    <button type="button" onClick={() => onOpen(item)} className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-surface-2">
                    <span className="min-w-0 flex-1">
                        <span className="block font-semibold wrap-break-word">{item.contact_name ?? item.recipient_email}</span>
                        {item.company && <span className="block text-[13px] text-muted">{item.company}</span>}
                        {item.subject && <span className="mt-0.5 block truncate text-[13px]">{item.subject}</span>}
                        <span className="mt-1 block text-[12.5px] text-muted tabular-nums">
                        {formatDateTime(item.created_at)}
                        {showSender && item.sender_name && ` · by ${item.sender_name}`}
                        </span>
                    </span>
                    <StatusPill status={item.status} />
                    </button>
                </li>
                ))}
            </ul>
        </>
    )
}
