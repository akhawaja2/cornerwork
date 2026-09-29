// One athlete, for the Cornerwork tab on a Gymdesk member page (design-canvas/profile.png, staff version).
import { esc, when, chip } from './util.js';

export async function renderMember(root, data, ctx) {
  if (data === null) {
    root.innerHTML = `<div class="mono">Cornerwork</div><h1>Not in Cornerwork yet</h1>` +
      `<p class="card">This Gymdesk member has no coaching record. Import their attendance from the extension Settings, or wait for them to text JOIN to the gym number.</p>`;
    return;
  }
  const { athlete: a, stats: s, recap, working_on, flags, sessions, thread, consent } = data;
  const status = { active: 'Coached', pending: 'Not opted in yet', stopped: 'Opted out' }[a.status] || a.status;
  const drills = thread.some(l => !l.reply) ? await ctx.drills() : [];
  const tile = (n, label) => `<div class="card stat"><strong>${n == null ? '—' : esc(n)}</strong><small>${label}</small></div>`;
  root.innerHTML =
    `<div class="mono">${esc(status)}${consent ? ' · ' + esc(consent.action.replace('_', ' ')) + ' ' + when(consent.at) : ''}${a.phone_last4 ? ' · ···' + esc(a.phone_last4) : ''}</div>` +
    `<h1>${esc(a.name)}'s training</h1>` +
    (a.goal ? `<p class="muted">Goal: ${esc(a.goal)}</p>` : '') +
    `<div class="stats">${tile(s.sessions_30d, 'sessions / 30d')}${tile(s.streak_weeks ? s.streak_weeks + 'w' : 0, 'logging streak')}${tile(s.coach_notes, 'coach notes')}</div>` +
    `<section class="card dark"><div class="mono">This week · recap</div><p>${recapText(recap)}</p></section>` +
    `<div class="cols" style="margin-top:16px"><div>` +
    (flags.length ? `<section class="card" style="margin-bottom:16px"><h2>Flags</h2>${flags.map(f => `<div class="person"><div class="body">${chip(f)} <span class="muted">${esc(f.detail || '')}</span></div></div>`).join('')}</section>` : '') +
    `<section class="card"><h2>Coaching thread</h2>` +
    (thread.length ? thread.map(l => entry(l, drills)).join('') : '<p class="muted">No logs yet.</p>') + `</section></div><div>` +
    `<section class="card"><h2>Working on</h2>` +
    (working_on.length ? working_on.map(t => `<div class="row between" style="padding:6px 0;border-bottom:1px solid var(--line)"><span>${esc(t.name)}</span><span class="mono" style="color:var(--teal)">${esc(t.status)}</span></div>`).join('') : '<p class="muted">Nothing tagged in the last 30 days.</p>') +
    `</section><section class="card" style="margin-top:16px"><h2>Sessions</h2>` +
    (sessions.length ? sessions.map(x => `<div class="row" style="padding:6px 0"><span class="mono" style="width:44px">${esc(new Date(x.date || x.at).toLocaleDateString([], { weekday: 'short' }))}</span><span>${esc(x.class)} · ${esc(x.date || '')}</span></div>`).join('') : '<p class="muted">No check-ins imported yet.</p>') +
    `</section></div></div>`;
  root.querySelectorAll('form[data-log]').forEach(form => form.onsubmit = async e => {
    e.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      await ctx.adapter.api('POST', '/api/replies', { log_id: Number(form.dataset.log), body: form.body.value, drill_id: form.drill && form.drill.value ? Number(form.drill.value) : null });
      ctx.notify('Reply sent.');
      ctx.refresh();
    } catch (err) { ctx.notify(err.message); button.disabled = false; }
  });
}

function recapText(r) {
  if (!r.logs) return 'No logs this week yet.';
  return `${r.logs} log${r.logs === 1 ? '' : 's'} this week.` + (r.focus ? ` Focus: ${esc(r.focus)}.` : '') +
    (r.coach_note ? ` Coach said: “${esc(r.coach_note.length > 120 ? r.coach_note.slice(0, 117) + '…' : r.coach_note)}”` : ' No coach note yet.');
}

function entry(l, drills) {
  const tags = [l.injury ? `<span class="chip injury">Injury · ${esc(l.injury.area || '')}</span>` : '', l.concussion_flag ? '<span class="chip danger">Possible head injury</span>' : '',
    ...(l.techniques || []).map(t => `<span class="tag">${esc(t)}</span>`)].join(' ');
  const picker = drills.length ? `<select name="drill"><option value="">No drill</option>${drills.map(d => `<option value="${d.id}">${esc(d.title)}</option>`).join('')}</select>` : '';
  const reply = l.reply ? `<p><strong>Coach</strong> <small class="muted">${l.reply.sent_at ? when(l.reply.sent_at) : '(time unknown)'}</small></p><p class="message">${esc(l.reply.body)}</p>`
    : `<form data-log="${l.id}"><label for="r${l.id}">Reply${l.coach_draft ? ' · AI draft, edit freely' : ''}</label><textarea id="r${l.id}" name="body" maxlength="1600" required>${esc(l.coach_draft || '')}</textarea>${picker}<p></p><button>Send reply</button></form>`;
  return `<div class="person" style="display:block"><small class="muted">${when(l.created_at)}</small>` +
    (l.summary && l.summary !== l.transcript ? `<p><strong>${esc(l.summary)}</strong></p>` : '') +
    `<p class="message">${esc(l.transcript)}</p>${tags ? `<p>${tags}</p>` : ''}${reply}</div>`;
}
