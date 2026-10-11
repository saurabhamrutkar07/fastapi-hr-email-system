// A text box with the app's look. Takes every normal <input> prop (type, value, onchange...).
export default function Input({className='', ...props }){
    return(
        <input 
            {...props}
            className={`w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-fg outline-none placeholder:text-muted focus:border-primary focus:ring-3 focus:ring-primary-soft aria-invalid:border-err aria-invalid:focus:border-err aria-invalid:focus:ring-err-soft ${className}`}
        />
    )
}