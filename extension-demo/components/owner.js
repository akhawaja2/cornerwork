import { esc } from './util.js';

const tile = (label, value, hint = '') =>
  `<div class="tile"><small>${label}</small><strong>${value == null ? '—' : esc(value)}</strong>${hint ? `<small>${esc(hint)}</small>` : ''}</div>`;
const pct = v => v == null ? null : v + '%';
const hrs = v => v == null ? null : (v / 3600).toFixed(1) + ' h';

export function renderOwner(root, s) {
  root.innerHTML = `<h2>Owner view</h2><div class="tiles">` +
    tile('Coached athletes', s.coached, `${s.roster} on roster`) +
    tile('Logging this week', pct(s.weekly_logging_rate), `${s.weekly_loggers} of ${s.coached} active`) +
    tile('Median reply time', hrs(s.median_reply_seconds), s.median_reply_seconds == null ? 'no timed replies yet' : '') +
    tile('Replied within 48h', pct(s.replied_within_48h_rate), `${s.total_replies} of ${s.total_logs} logs replied`) +
    tile('Unanswered logs', s.unanswered_logs) +
    `</div><article class="card"><h3>Early warning · quiet 10+ days</h3>` +
    (s.drift.length ? s.drift.map(d => `<div class="item"><strong>${esc(d.name)}</strong> <small>${d.days_inactive} days</small></div>`).join('') : '<p class="muted">Nobody drifting.</p>') +
    `</article><article class="card"><h3>Coaches</h3>` +
    (s.per_coach.length ? s.per_coach.map(c => `<div class="item">Coach ${c.coach_id ?? '(unassigned)'} · ${c.replies} timed replies · median ${hrs(c.median_reply_seconds)}</div>`).join('') : '<p class="muted">No timed replies yet.</p>') +
    `</article><p class="muted">Every number comes from the events table (last ${s.period_days} days). “—” means not enough data, never zero.</p>`;
}
