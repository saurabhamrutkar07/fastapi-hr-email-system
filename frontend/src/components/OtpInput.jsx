import { useState } from "react";

const LENGTH = 6 

/*
    Six boxes for  a 6-digit code.
    It is really ONE invisible <input> lying on top of six boxes that only display the digits.
    That keeps typing, backspace, paste and phone SMS-autofill working like a normal text box.
    `value` is a string like "4821"; onChange receives the new string (digits only, max 6).
*/
export default function OtpInput({id, value, onChange, invalid= false, autoFocus = false }){
    const [focused, setFocused] = useState(false)
    // The box the next digit will go into 
    const activeIndex = Math.min(value.length, LENGTH - 1)

    return (
        <div className="relative">
            <input
                id={id}
                value={value}
                onChange={(e) => onChange(e.target.value.replace(/\D/g,'').slice(0, LENGTH))}
                onFocus={()=> setFocused(true)}
                onBlur={()=> setFocused(false)}
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={LENGTH}
                autoFocus={autoFocus}
                aria-invalid={invalid}
                className="absolute inset-0 h-full w-full cursor-text opacity-0"
            />
            
            <div className="grid grid-cols-6 gap-2" aria-hidden = "true">
                {Array.from({length: LENGTH}, (_, index) => (
                   <span
                   key = {index}
                   className = {`grid h-13 place-items-center rounded-lg border bg-surface font-mono text-xl ${
                        invalid
                            ? 'border-err'
                            : focused && index === activeIndex
                            ? 'border-primary ring-3 ring-primary-soft'
                            : 'border-line'
                    }`}
                   >
                    {value[index] ?? ''}
                   </span> 
                ))}
            </div>
        </div>
    )

}