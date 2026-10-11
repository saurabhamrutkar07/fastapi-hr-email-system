import { Outlet } from 'react-router'
import Logo from '../components/Logo'

const STEPS = [
  ['Add contacts', 'Type them in or import an Excel or PDF list.'],
  ['Pick a template and resume', 'Variables like hr_name fill in for each person.'],
  ['Send and track', "Every send is logged with the server's reply."],
]

/*
  Frame for the sign in / sign up / reset password pages.
    1024px+ (lg): navy panel on the left, form on the right
    smaller:      just the form, with the logo on top
*/
export default function AuthLayout() {
  return (
    <div className="grid min-h-dvh bg-bg lg:grid-cols-2">
      <aside className="hidden flex-col justify-between gap-7 bg-brand-panel p-10 text-on-brand lg:flex">
        <div>
          <Logo inverted />
          <h1 className="mt-10 max-w-[15ch] font-display text-[34px] font-bold leading-tight text-balance">
            Reach recruiters from your own inbox.
          </h1>
          <p className="mt-3 max-w-[42ch] text-on-brand-muted">
            Keep your HR contacts in one place, send personalised cold emails with your resume attached, and see
            which ones landed.
          </p>
        </div>

        <ol className="flex max-w-[400px] flex-col gap-2.5">
          {STEPS.map(([title, text], index) => (
            <li key={title} className="flex gap-3 rounded-xl border border-on-brand-line bg-on-brand-card px-3.5 py-3">
              <span className="mt-0.5 font-mono text-xs text-on-brand-accent">{index + 1}</span>
              <div>
                <p className="font-bold">{title}</p>
                <p className="text-[12.5px] text-on-brand-muted">{text}</p>
              </div>
            </li>
          ))}
        </ol>
      </aside>

      <main className="flex flex-col justify-center px-4 py-8 sm:px-6">
        <div className="mx-auto flex w-full max-w-[400px] flex-col gap-4">
          <div className="lg:hidden">
            <Logo />
          </div>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
