import { formatDate } from '../../utils/format'
import StatusPill from '../StatusPill'

const SIGN_IN = { google: 'Google', local: 'Password'}

/*
    Users as a table on wide screens and as cards below that, each with its actions.
    onAction(user, 'promote' | 'demote' | 'block' | 'unblock') asks the page to confirm and do it.
*/
export default function UserList({ users, currentUserId, onAction }) {

    return (
        <>
            <div className="hidden overflow-x-auto lg:block">
                <table className="w-full text-left text-[13.5px]">
                    <thead className="border-b border-line text-[12px] font-semibold uppercase tracking-wide text-muted">
                        <tr>
                        <th className="px-5 py-3">User</th>
                        <th className="px-3 py-3">Role</th>
                        <th className="px-3 py-3">Status</th>
                        <th className="px-3 py-3">Emails sent</th>
                        <th className="px-3 py-3">Joined</th>
                        <th className="px-5 py-3 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                        {users.map((user) => (
                        <tr key={user.id}>
                            <td className="max-w-72 px-5 py-3">
                            <p className="font-semibold">{user.name}</p>
                            <p className="truncate text-[12.5px] text-muted">
                                {user.email} · {SIGN_IN[user.auth_provider] ?? user.auth_provider}
                            </p>
                            </td>
                            <td className="px-3 py-3">
                            <RoleBadge role={user.role} />
                            </td>
                            <td className="px-3 py-3">
                            <StatusPill status={user.status} />
                            {user.blocked_by_name && <p className="mt-0.5 text-[12px] text-muted">by {user.blocked_by_name}</p>}
                            </td>
                            <td className="px-3 py-3 tabular-nums">
                            {user.emails_sent}
                            {user.last_sent_at && <p className="text-[12px] text-muted">last {formatDate(user.last_sent_at)}</p>}
                            </td>
                            <td className="px-3 py-3 whitespace-nowrap text-muted tabular-nums">{formatDate(user.created_at)}</td>
                            <td className="px-5 py-3">
                            <UserActions user={user} isYou={user.id === currentUserId} onAction={onAction} />
                            </td>
                        </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <ul className="divide-y divide-line lg:hidden">
                {users.map((user) => (
                <li key={user.id} className="flex flex-col gap-2.5 px-4 py-3">
                    <div className="flex items-start gap-3">
                    <div className="min-w-0 flex-1">
                        <p className="flex flex-wrap items-center gap-2 font-semibold">
                        {user.name}
                        <RoleBadge role={user.role} />
                        </p>
                        <p className="text-[13px] wrap-break-word text-muted">{user.email}</p>
                        <p className="mt-0.5 text-[12.5px] text-muted tabular-nums">
                        {SIGN_IN[user.auth_provider] ?? user.auth_provider} · joined {formatDate(user.created_at)} · {user.emails_sent} sent
                        </p>
                    </div>
                    <StatusPill status={user.status} />
                    </div>
                    <UserActions user={user} isYou={user.id === currentUserId} onAction={onAction} />
                </li>
                ))}
            </ul>
        </>
    )
    
}


function RoleBadge({ role }) {
    if (role !== 'admin') return <span className="text-[13px] text-muted">User</span>
    return <span className="rounded-full bg-primary-soft px-2.5 py-0.5 text-[12px] font-semibold text-primary">Admin</span>
    
}

// Your own account and unfinished signups can't be changed, so they got a note instead of buttons
function UserActions({ user, isYou, onAction }) {
    if(isYou) return <p className="text-[13px] text-muted lg:text-right">This is you</p>
    if (user.status === 'pending') return <p className="text-[13px] text-muted lg:text-right">-</p>

    const blocked = user.status === 'blocked'
    return (
        <div className="flex flex-wrap gap-2 lg:justify-end">
            <ActionButton onClick={() => onAction(user, user.role === 'admin' ? 'demote' : 'promote')}>
                {user.role === 'admin' ? 'Make user' : 'Make admin'}
            </ActionButton>
            <ActionButton danger={!blocked} onClick={() => onAction(user, blocked  ? 'unblock' : 'block')}>
                {blocked  ? 'Unblock' : 'Block'}
            </ActionButton>   
        </div>
    )
}

function ActionButton({ danger, ...props }) {
    return(
      <button
        type="button"
        {...props}
        className={`rounded-lg border px-3 py-1.5 text-[13px] font-semibold whitespace-nowrap ${
            danger ? 'border-err/40 text-err-text hover:bg-err-soft' : 'border-line hover:bg-surface-2'
        }`}
    />  
    )
    
}