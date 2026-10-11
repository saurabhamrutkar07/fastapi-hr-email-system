// Label + the input you pass inside + an optional hint or error below 


function Field({ id, label, hint, error, children }) {
  return (
    <div className="flex flex-col gap-1.5">
        <label htmlFor={id} className="text-[13px] font-semibold">
            {label}
        </label>
        {children}
        {error ? (
            <p className="text-xs text-err-text">{error}</p>
        ): (
            hint && <p className="text-xs text-muted">{hint}</p>
        )


        }
    </div>
  )
}

export default Field