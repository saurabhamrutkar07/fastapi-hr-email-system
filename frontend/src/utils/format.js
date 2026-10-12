const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const twoDigits = (n) => String(n).padStart(2, '0')

// A backend timestamp in the viewer's local time: "Today, 11:42" / "Yesterday, 18:05" / "8 Oct, 10:17"
export function formatDateTime(iso) {
  const date = new Date(iso)
  const time = `${twoDigits(date.getHours())}:${twoDigits(date.getMinutes())}`

  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(today.getDate() - 1)
  const sameDay = (a, b) => a.toDateString() === b.toDateString()

  if (sameDay(date, today)) return `Today, ${time}`
  if (sameDay(date, yesterday)) return `Yesterday, ${time}`
  return `${date.getDate()} ${MONTHS[date.getMonth()]}, ${time}`
}

// "2026-10-08T..." -> "8 Oct 2026"
export function formatDate(iso) {
  const date = new Date(iso)
  return `${date.getDate()} ${MONTHS[date.getMonth()]} ${date.getFullYear()}`
}
