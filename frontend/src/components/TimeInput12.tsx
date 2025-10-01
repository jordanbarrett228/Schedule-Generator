import { useMemo } from 'react';
import { to12Parts, from12Parts } from '../lib/time';

type Props = {
  /** Stored value in "HH:MM" 24h (e.g. "15:00"). Empty means no selection. */
  value: string | null | undefined;
  /** Called with "HH:MM" 24h on change */
  onChange: (hhmm: string) => void;
  /** Optional: minute step (default 15) */
  stepMinutes?: 5 | 10 | 15 | 30;
  /** Optional: compact size */
  small?: boolean;
  /** Optional: aria-label */
  label?: string;
};

export default function TimeInput12({ value, onChange, stepMinutes = 15, small, label }: Props) {
  const { h12, m, am } = useMemo(() => to12Parts(value ?? '00:00'), [value]);
  const minutes = useMemo(() => {
    const arr: number[] = [];
    for (let k = 0; k < 60; k += stepMinutes) arr.push(k);
    return arr;
  }, [stepMinutes]);

  const cls = small ? 'time12 time12--sm' : 'time12';

  return (
    <div className={cls} aria-label={label}>
      <select
        className="time12__h"
        value={h12}
        onChange={e => onChange(from12Parts(parseInt(e.target.value, 10), m, am))}
      >
        {Array.from({ length: 12 }, (_, i) => i + 1).map(h => (
          <option key={h} value={h}>{h}</option>
        ))}
      </select>

      <span className="time12__sep">:</span>

      <select
        className="time12__m"
        value={m}
        onChange={e => onChange(from12Parts(h12, parseInt(e.target.value, 10), am))}
      >
        {minutes.map(mm => (
          <option key={mm} value={mm}>{mm.toString().padStart(2, '0')}</option>
        ))}
      </select>

      <select
        className="time12__ampm"
        value={am ? 'AM' : 'PM'}
        onChange={e => onChange(from12Parts(h12, m, e.target.value === 'AM'))}
      >
        <option>AM</option>
        <option>PM</option>
      </select>
    </div>
  );
}
