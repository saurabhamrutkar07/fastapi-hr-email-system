const TONES = {
  error: 'bg-err-soft text-err-text',
  success: 'bg-ok-soft text-ok-text',
  info: 'bg-primary-soft text-fg',
}

// Coloured message box. Renders nothing when there is no message.

export default function Alert({ tone = 'error', children }) {
  if (!children) return null

  return (
    <div
      role={tone === 'error' ? 'alert' : 'status'}
      className={`rounded-lg px-3.5 py-3 text-[13.5px] font-medium ${TONES[tone]}`}
    >
      {children}
    </div>
  )
}
