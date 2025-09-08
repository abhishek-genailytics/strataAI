export const formatMoney = (n?: number, c: 'USD'|'INR' = 'USD') =>
  n == null ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: c }).format(n)

export const caps = (s?: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : '')
