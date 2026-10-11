const VARIANTS = {
    primary : 'border-primary bg-primary text-white hover:brightness-110',
    secondary : 'border-line bg-surface text-fg hover:bg-surface-2'
}

// <Button loading={saving}>Save</Button> - shows a spinner and blocks double clicks while loading



function Button({variant = 'primary', loading = false, className='',children, ...props }) {
  return (
    <button
        {...props}
        disabled = {loading || props.disabled}
        className={`inline-flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 font-semibold disabled:cursor-not-allowed disabled:opacity-60 ${VARIANTS[variant]} ${className}`}
    >
        {loading && (
            <span className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent" aria-hidden="true" />
        )}
        {children}
    </button>
  )
}

export default Button