// A multi-line text box with the same look as Input. Pass `ref` to reach the <textarea> (e.g. to insert at the cursor).
export default function Textarea({ className = '', ...props }) {
  return (
    <textarea
      {...props}
      className={`w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-fg outline-none placeholder:text-muted focus:border-primary focus:ring-3 focus:ring-primary-soft aria-invalid:border-err aria-invalid:focus:border-err aria-invalid:focus:ring-err-soft ${className}`}
    />
  )
}
