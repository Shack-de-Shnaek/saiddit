const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
})

export function formatDate(value) {
  if (!value) return ''
  return dateFormatter.format(new Date(value))
}
