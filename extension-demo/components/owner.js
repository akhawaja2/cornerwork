import { esc } from './util.js';

const tile = (label, value, hint = '', cls = '') =>
  `<div class="card stat ${cls}"><span class="mono">${label}</span><strong>${value == null ? '—' : esc(value)}</strong><small>${esc(hint)}</small></div>`;
const pct = v => v == null ? null : v + '%';
const hrs = v => v == null ? null : (v / 3600).toFixed(1) + ' h';

export function renderOwner(root, s, ctx) {
  root.innerHTML = `<div class="row between"><div><div class="mono">Owner · last ${s.period_days} days</div><h1>Coached tier</h1></div><span class="mono">Attendance imported from Gymdesk</span></div>` +
    `<div class="stats">` +
    tile('Coached members', s.coached, `of ${s.roster} on the roster`) +
    tile('Gym share · estimate', '$' + s.revenue_estimate_usd + ' /mo', `${s.coached} coached × $${s.gym_share_usd} gym share of the $25 add-on`, 'teal') +
    tile('Athletes logging weekly', pct(s.weekly_logging_rate), s.coached ? `${s.weekly_loggers} of ${s.coached} active` : 'no active athletes yet') +
    tile('Coach reply time', hrs(s.median_reply_seconds), s.median_reply_seconds == null ? 'no timed replies yet' : `median · ${pct(s.replied_within_48h_rate)} within 48h`) +
    `</div><div class="cols"><section class="card"><h2>At risk</h2><p class="muted">No check-in or log in 10+ days</p>` +
    (s.drift.length ? s.drift.map(d => `<div class="person"><div class="body"><h3>${esc(d.name)}</h3><p>${d.days_inactive}d quiet${d.month ? ' · month ' + d.month : ''}</p></div>` +
      (d.asked ? '<span class="chip drift">Coach asked</span>' : `<button class="secondary" data-checkin="${d.id}">Ask coach to check in</button>`) + '</div>').join('')
      : '<p class="muted">Nobody drifting.</p>') +
    `</section><section class="card"><h2>Coaches</h2>` +
    (s.per_coach.length ? s.per_coach.map(c => `<div class="person"><div class="body"><h3>Coach ${c.coach_id ?? ''}</h3><p>${c.replies} timed replies · median ${hrs(c.median_reply_seconds)}</p></div></div>`).join('') : '<p class="muted">No timed replies yet.</p>') +
    `<p class="muted" style="margin-top:14px">${s.total_replies} of ${s.total_logs} logs replied · ${s.unanswered_logs} unanswered</p></section></div>` +
    `<p class="muted">Every number comes from the events table. “—” means not enough data, never zero. Anonymous feedback and confidential concerns are not part of this pilot.</p>`;
  root.querySelectorAll('button[data-checkin]').forEach(b => b.onclick = async () => {
    b.disabled = true;
    try { await ctx.adapter.api('POST', `/api/owner/checkin/${b.dataset.checkin}`); ctx.notify('Coach asked to check in.'); ctx.refresh(); }
    catch (e) { ctx.notify(e.message); b.disabled = false; }
  });
}
