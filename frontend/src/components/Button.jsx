import { Link } from 'react-router'

const VARIANTS = {
    primary : 'border-primary bg-primary text-white hover:brightness-110',
    secondary : 'border-line bg-surface text-fg hover:bg-surface-2',
    danger : 'border-err bg-err text-white hover:brightness-110',
}

const BASE = 'inline-flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 font-semibold'

// <Button loading={saving}>Save</Button> - shows a spinner and blocks double clicks while loading
function Button({variant = 'primary', loading = false, className='',children, ...props }) {
  return (
    <button
        {...props}
        disabled = {loading || props.disabled}
        className={`${BASE} disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${className}`}
    >
        {loading && (
            <span className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent" aria-hidden="true" />
        )}
        {children}
    </button>
  )
}

// A link to another page that looks like a Button: <ButtonLink to="/send">Send email</ButtonLink>
export function ButtonLink({ variant = 'primary', className = '', ...props }) {
  return <Link {...props} className={`${BASE} ${VARIANTS[variant]} ${className}`} />
}

export default Button
