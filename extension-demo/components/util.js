export const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const when = iso => { const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }); };
export const ago = ms => { const m = Math.round((Date.now() - ms) / 60000); return m < 1 ? 'just now' : m < 60 ? m + 'm ago' : Math.round(m / 60) + 'h ago'; };
export const initials = name => String(name || '?').split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase();
export const avatarClass = id => ['', 'b', 'c', 'd'][(Number(id) || 0) % 4];
export const FLAG_LABEL = { injury: 'Injury', returning: 'Returning', fight_prep: 'Fight prep', new: 'New', drift: 'Check in' };
export const chip = f => `<span class="chip ${esc(f.type)}${/head/i.test(f.detail || '') ? ' danger' : ''}" title="${esc(f.detail || '')}">${esc(FLAG_LABEL[f.type] || f.type)}</span>`;
/** "Starts in 1h 20m" / "Started 12m ago" / "Tomorrow · 7:00 AM" from a date (YYYY-MM-DD) and local HH:MM. */
export function startsIn(dateStr, hhmm) {
  if (!dateStr) return '';
  const [y, m, d] = dateStr.split('-').map(Number);
  const [hh, mm] = (hhmm || '00:00').split(':').map(Number);
  const start = new Date(y, m - 1, d, hh, mm);
  const diff = Math.round((start - Date.now()) / 60000);
  const day = start.toLocaleDateString([], { weekday: 'short' }).toUpperCase();
  const clock = hhmm ? start.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) : '';
  const rel = diff < -90 ? '' : diff < 0 ? ` · started ${-diff}m ago` : diff < 24 * 60 ? ` · starts in ${Math.floor(diff / 60) ? Math.floor(diff / 60) + 'h ' : ''}${diff % 60}m` : '';
  return `${day} · ${clock || dateStr}${rel}`;
}
