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

/** Convert "HH:MM" (24h) -> { h12:1..12, m:0|15|30|45, am:true|false } */
export function to12Parts(hhmm: string) {
  const [hStr, mStr] = hhmm.split(':');
  const h24 = Math.max(0, Math.min(23, parseInt(hStr || '0', 10)));
  const m = Math.max(0, Math.min(59, parseInt(mStr || '0', 10)));
  const am = h24 < 12;
  let h12 = h24 % 12;
  if (h12 === 0) h12 = 12;
  return { h12, m, am };
}

/** Convert 12-hour parts -> "HH:MM" (24h) */
export function from12Parts(h12: number, m: number, am: boolean): string {
  let h = h12 % 12;
  if (!am) h += 12;
  const hh = h.toString().padStart(2, '0');
  const mm = Math.max(0, Math.min(59, m)).toString().padStart(2, '0');
  return `${hh}:${mm}`;
}
