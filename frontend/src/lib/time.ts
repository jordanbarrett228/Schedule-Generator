export function hhmmToMin(s: string): number {
  const [h, m] = s.split(':').map(Number)
  return h * 60 + m
}

export function format12(hhmm: string): string {
  const [H, M] = hhmm.split(':').map(Number)
  const am = H < 12
  const h12 = ((H + 11) % 12) + 1
  return `${h12}:${String(M).padStart(2, '0')} ${am ? 'AM' : 'PM'}`
}