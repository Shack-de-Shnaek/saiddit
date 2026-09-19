// The API answers every error with { detail, errors?: { <field>: [message] } },
// where '__all__' holds messages that belong to the request as a whole.
export function parseApiError(error, fallback = 'Something went wrong. Please try again.') {
  const data = error?.response?.data
  const fields = { ...(data?.errors ?? {}) }
  const nonField = fields.__all__ ?? []
  delete fields.__all__

  return {
    detail: [data?.detail ?? fallback, ...nonField].join(' '),
    fields,
  }
}

// Fields carry a list of messages; forms only have room for the first one.
export function firstError(fields, name) {
  return fields[name]?.[0] ?? ''
}
