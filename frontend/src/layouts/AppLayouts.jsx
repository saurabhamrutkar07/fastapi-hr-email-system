import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router'
import Icon from '../components/Icon'
import Logo from '../components/Logo'
import useTheme from '../hooks/useTheme'
import { BOTTOM_NAV, MORE_PATHS, NAV_GROUPS } from '../config/navigation'

// Placeholder until Step 3 loads the signed-in user from the backend
const CURRENT_USER = { name: 'Saurabh A.', email: 'saurabh.dev@example.com', initials: 'SA' }

const ICON_BTN =
  'grid size-9 shrink-0 place-items-center rounded-lg border border-line bg-surface text-fg hover:bg-surface-2'

/*
  Screen sizes (Tailwind breakpoints):
    < 640px   (mobile)  top bar with menu button + bottom nav, menu opens as a drawer
    640px+    (sm)      72px icon-only sidebar ("rail")
    1024px+   (lg)      full 236px sidebar with labels
*/
export default function AppLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <div className="flex h-dvh bg-bg">
      <aside className="hidden w-[72px] shrink-0 flex-col gap-1.5 overflow-y-auto border-r border-line bg-surface px-3 py-3.5 sm:flex lg:w-[236px]">
        <div className="flex justify-center px-1.5 pb-3 pt-1 lg:justify-start">
          <Logo nameClassName="hidden lg:inline" />
        </div>
        <SideNav rail />
        <UserFooter rail />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onMenu={() => setDrawerOpen(true)} />
        <main className="flex-1 overflow-y-auto px-4 pb-7 pt-5 sm:p-6 lg:px-8 lg:pb-9 lg:pt-7">
          <Outlet />
        </main>
        <BottomNav onMore={() => setDrawerOpen(true)} />
      </div>

      {drawerOpen && <Drawer onClose={() => setDrawerOpen(false)} />}
    </div>
  )
}

// rail = true: labels hidden between 640px and 1024px (icon-only sidebar)
function SideNav({ rail = false, onNavigate }) {
  const showOnWide = rail ? 'hidden lg:block' : ''

  return (
    <nav className="flex flex-col gap-0.5">
      {NAV_GROUPS.map((group) => (
        <div key={group.label} className="flex flex-col gap-0.5">
          <p className={`px-2.5 pb-1.5 pt-3.5 text-[11px] font-bold uppercase tracking-[0.08em] text-muted ${showOnWide}`}>
            {group.label}
          </p>
          {group.items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              title={item.label}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-2.5 py-2.5 font-semibold ${
                  rail ? 'justify-center lg:justify-start' : ''
                } ${isActive ? 'bg-brand-soft text-brand' : 'text-muted hover:bg-surface-2 hover:text-fg'}`
              }
            >
              <Icon name={item.icon} />
              <span className={showOnWide}>{item.label}</span>
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  )
}

function UserFooter({ rail = false }) {
  return (
    <div
      className={`mt-auto flex items-center gap-2.5 border-t border-line px-1.5 pt-2.5 ${
        rail ? 'flex-col lg:flex-row' : ''
      }`}
    >
      <Avatar />
      <div className={`min-w-0 flex-1 ${rail ? 'hidden lg:block' : ''}`}>
        <p className="text-[13px] font-bold">{CURRENT_USER.name}</p>
        <p className="truncate text-xs text-muted">{CURRENT_USER.email}</p>
      </div>
      <button className={ICON_BTN} title="Sign out" aria-label="Sign out">
        <Icon name="logout" />
      </button>
    </div>
  )
}

function Avatar() {
  return (
    <span className="grid size-[34px] shrink-0 place-items-center rounded-full bg-brand-soft text-[12.5px] font-bold text-brand">
      {CURRENT_USER.initials}
    </span>
  )
}

function TopBar({ onMenu }) {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="flex items-center gap-2.5 border-b border-line bg-surface px-4 py-2.5 sm:px-6 sm:py-3">
      <button className={`${ICON_BTN} sm:hidden`} onClick={onMenu} aria-label="Open menu">
        <Icon name="menu" />
      </button>
      <div className="sm:hidden">
        <Logo />
      </div>

      <label className="hidden max-w-[420px] flex-1 items-center gap-2 rounded-lg border border-line bg-surface-2 px-2.5 text-muted sm:flex">
        <Icon name="search" />
        <input
          className="w-full bg-transparent py-2 text-fg outline-none placeholder:text-muted"
          placeholder="Search contacts, companies, emails"
        />
      </label>

      <span className="flex-1" />
      <button className={ICON_BTN} onClick={toggleTheme} aria-label="Toggle light or dark theme">
        <Icon name={theme === 'dark' ? 'sun' : 'moon'} />
      </button>
      <Avatar />
    </header>
  )
}

function BottomNav({ onMore }) {
  const { pathname } = useLocation()
  const moreActive = MORE_PATHS.some((path) => pathname.startsWith(path))
  const itemClass = (active) =>
    `flex flex-col items-center gap-0.5 pb-2.5 pt-2 text-[11px] font-semibold ${active ? 'text-brand' : 'text-muted'}`

  return (
    <nav className="grid grid-cols-5 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] sm:hidden">
      {BOTTOM_NAV.map((item) => (
        <NavLink key={item.to} to={item.to} end={item.to === '/'} className={({ isActive }) => itemClass(isActive)}>
          <Icon name={item.icon} />
          {item.label}
        </NavLink>
      ))}
      <button onClick={onMore} className={itemClass(moreActive)}>
        <Icon name="more" />
        More
      </button>
    </nav>
  )
}

function Drawer({ onClose }) {
  // Close on Escape key
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-30 flex bg-slate-950/45 sm:hidden" onClick={onClose}>
      <div
        className="flex h-full w-[min(290px,84%)] flex-col gap-1.5 overflow-y-auto bg-surface px-3 py-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-1 pb-2">
          <Logo />
          <button className={ICON_BTN} onClick={onClose} aria-label="Close menu">
            <Icon name="x" />
          </button>
        </div>
        <SideNav onNavigate={onClose} />
        <UserFooter />
      </div>
    </div>
  )
}
