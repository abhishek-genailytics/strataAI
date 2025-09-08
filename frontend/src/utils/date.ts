export const isoDate = (d: Date) => d.toISOString().slice(0,10)

export const lastNDays = (n: number) => {
  const to = new Date()
  const from = new Date()
  from.setDate(to.getDate() - (n - 1))
  return { from: isoDate(from), to: isoDate(to) }
}
