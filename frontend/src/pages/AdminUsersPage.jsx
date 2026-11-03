import { useMemo, useState } from 'react'
import { adminUsersApi } from '../api/adminUsers'
import { useAuth } from '../auth/context'
import Alert from '../components/Alert'
import Button from '../components/Button'
import ConfirmDialog from '../components/ConfirmDialog'
import Icon from '../components/Icon'
import Input from '../components/Input'
import Modal from '../components/Modal'
import Select from '../components/Select'
import UserList from '../components/admin/UserList'
import useApi from '../hooks/useApi'

// What each action asks before doing it, and what it says after
const ACTIONS = {
  promote: {
    title: 'Make this user an admin?',
    message: (name) => <><b>{name}</b> will see everyone’s emails and be able to import contacts and manage users.</>,
    confirmLabel: 'Make admin',
    run: (user) => adminUsersApi.setRole(user.id, 'admin'),
    done: (name) => `${name} is now an admin.`,
  },
  demote: {
    title: 'Remove admin rights?',
    message: (name) => <><b>{name}</b> will become a regular user.</>,
    confirmLabel: 'Make user',
    run: (user) => adminUsersApi.setRole(user.id, 'user'),
    done: (name) => `${name} is now a regular user.`,
  },
  block: {
    title: 'Block this user?',
    message: (name) => <><b>{name}</b> will be signed out and can’t sign in until you unblock them. Their emails and data stay.</>,
    confirmLabel: 'Block',
    danger: true,
    run: (user) => adminUsersApi.setBlocked(user.id, true),
    done: (name) => `${name} is blocked.`,
  },
  unblock: {
    title: 'Unblock this user?',
    message: (name) => <><b>{name}</b> will be able to sign in again.</>,
    confirmLabel: 'Unblock',
    run: (user) => adminUsersApi.setBlocked(user.id, false),
    done: (name) => `${name} can sign in again.`,
  },
}

// Admin only: everyone who uses ColdReach. Few enough users to filter in the browser.
export default function AdminUsersPage() {
  const { user: me } = useAuth()
  const users = useApi(adminUsersApi.list)

  const [search, setSearch] = useState('')
  const [role, setRole] = useState('')
  const [status, setStatus] = useState('')
  const [pending, setPending] = useState(null) // { user, action } waiting for "Are you sure?"
  const [notice, setNotice] = useState('')

  const all = useMemo(() => users.data ?? [], [users.data])
  const shown = useMemo(() => {
    const words = search.trim().toLowerCase()
    return all.filter((u) => {
      if (role && u.role !== role) return false
      if (status && u.status !== status) return false
      return !words || `${u.name} ${u.email}`.toLowerCase().includes(words)
    })
  }, [all, search, role, status])

  const admins = all.filter((u) => u.role === 'admin').length
  const blocked = all.filter((u) => u.status === 'blocked').length
  const action = pending && ACTIONS[pending.action]

  function ask(user, actionName) {
    setNotice('')
    setPending({ user, action: actionName })
  }

  async function confirmAction() {
    await action.run(pending.user)
    setNotice(action.done(pending.user.name))
    setPending(null)
    users.reload()
  }

  
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="font-display text-[22px] font-bold text-brand-ink sm:text-[26px]">Users</h2>
        <p className="mt-0.5 text-muted">
          {users.data
            ? `${all.length} ${all.length === 1 ? 'person' : 'people'} · ${admins} ${admins === 1 ? 'admin' : 'admins'} · ${blocked} blocked`
            : 'Everyone who uses ColdReach.'}
        </p>
      </div>

      <Alert tone="success">{notice}</Alert>

      <div className="flex flex-col gap-2.5 sm:flex-row">
        <label className="relative min-w-0 flex-1">
          <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted">
            <Icon name="search" />
          </span>
          <Input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name or email"
            aria-label="Search users"
            className="pl-10"
          />
        </label>
        <div className="grid grid-cols-2 gap-2.5 sm:flex">
          <Select value={role} onChange={(e) => setRole(e.target.value)} aria-label="Filter by role" className="sm:w-36">
            <option value="">All roles</option>
            <option value="admin">Admins</option>
            <option value="user">Users</option>
          </Select>
          <Select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status" className="sm:w-48">
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="blocked">Blocked</option>
            <option value="pending">Signup not finished</option>
          </Select>
        </div>
      </div>

      <section className="min-w-0 overflow-hidden rounded-xl border border-line bg-surface">
        {users.error ? (
          <div className="flex flex-col items-start gap-3 p-4 sm:p-5">
            <Alert>Couldn’t load users. {users.error}</Alert>
            <Button variant="secondary" onClick={users.reload}>
              Try again
            </Button>
          </div>
        ) : !users.data ? (
          <div className="h-64 animate-pulse bg-surface-2" aria-hidden="true" />
        ) : shown.length === 0 ? (
          <p className="px-4 py-12 text-center text-[13.5px] text-muted">No users match.</p>
        ) : (
          <div className={users.loading ? 'opacity-60' : ''}>
            <UserList users={shown} currentUserId={me.id} onAction={ask} />
          </div>
        )}
      </section>

      <Modal open={Boolean(pending)} onClose={() => setPending(null)} title={action?.title ?? ''}>
        {pending && (
          <ConfirmDialog
            message={action.message(pending.user.name)}
            confirmLabel={action.confirmLabel}
            note="You can change this back any time."
            variant={action.danger ? 'danger' : 'primary'}
            onConfirm={confirmAction}
            onCancel={() => setPending(null)}
          />
        )}
      </Modal>
    </div>
  )
}

