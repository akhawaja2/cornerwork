import { esc, initials, avatarClass, chip, startsIn } from './util.js';

export function renderBrief(root, { classes, brief }, ctx) {
  const options = classes.map(c => `<option value="${c.id}"${brief && c.id === brief.class.id ? ' selected' : ''}>${esc(c.name)}${c.start_time ? ' · ' + esc(c.start_time) : ''}</option>`).join('');
  const controls = `<div class="row"><select id="cls" style="width:auto;min-width:220px">${options || '<option value="">No classes yet</option>'}</select>` +
    `<input id="date" type="date" style="width:auto" value="${esc(ctx.brief.date || '')}"></div>`;
  if (!brief) {
    root.innerHTML = `<div class="mono">Today's classes</div><h1>No classes yet</h1>${controls}` +
      '<p class="card">Import Gymdesk attendance from Settings, or post a roster, and the brief appears here.</p>';
    wire(root, ctx);
    return;
  }
  const c = brief.counts, flagged = brief.athletes.filter(a => a.flags.length), quiet = brief.athletes.filter(a => !a.flags.length);
  const flagBits = Object.entries(c.flags).map(([k, v]) => `${v} ${({ injury: 'injury', returning: 'returning', fight_prep: 'fight prep', new: 'new', drift: 'check-in' })[k] || k}`).join(' · ');
  const source = !brief.sources.length ? '<span class="chip">No bookings for this date</span>' :
    brief.sources.every(s => s === 'gymdesk' || s === 'csv') ? '' : '<span class="chip injury">DEMO DATA · manual booking</span>';
  const max = Math.max(1, ...brief.themes.map(t => t.count));
  root.innerHTML =
    `<div class="row between"><div><div class="mono">${esc(startsIn(brief.date, brief.class.start_time))}</div><h1>${esc(brief.class.name)}</h1></div>${controls}</div>` +
    `<div class="stats">` +
    `<div class="card stat"><span class="mono">Registered</span><strong>${c.registered}</strong><small>${c.coached} coached · ${c.new} new ${source}</small></div>` +
    `<div class="card stat warm"><span class="mono">Flags</span><strong>${c.flagged}</strong><small>${esc(flagBits) || 'none'}</small></div>` +
    `<div class="card stat teal"><span class="mono">Suggested focus</span><strong style="font-size:22px">${esc(brief.focus)}</strong><small>${brief.themes.length ? 'from ' + brief.themes.length + ' theme(s) this week' : 'no logs this week'} · ${esc(brief.generator)}</small></div>` +
    `</div><div class="cols"><section class="card"><h2>Who's on the mat</h2>` +
    (brief.athletes.length ? flagged.map(person).join('') +
      (quiet.length ? `<details><summary style="cursor:pointer;color:var(--teal);font-weight:600;padding:10px 0">+ ${quiet.length} more with no flags</summary>${quiet.map(person).join('')}</details>` : '')
      : '<p class="muted">Nobody booked or checked in for this date.</p>') +
    `</section><div><section class="card"><h2>Themes from this week's logs</h2>` +
    (brief.themes.length ? brief.themes.map(t => `<div class="row between"><span>${esc(t.name)}</span><strong>${t.count}</strong></div><div class="bar"><i style="width:${Math.round(t.count / max * 100)}%"></i></div>`).join('') : '<p class="muted">No logs in the last 7 days.</p>') +
    `</section><section class="card dark" style="margin-top:16px"><div class="mono">Before class · say hello with</div>` +
    (brief.notes.length ? brief.notes.map(n => `<p><strong>${esc(n.athlete)}:</strong> ${esc(n.note)}</p>`).join('') : '<p>No notes yet. Notes appear once athletes log after class.</p>') +
    `</section></div></div>`;
  wire(root, ctx);
}

function person(a) {
  return `<div class="person"><span class="avatar ${avatarClass(a.id)}">${esc(initials(a.name))}</span><div class="body">` +
    `<h3><a href="#inbox?athlete=${a.id}" style="color:inherit;text-decoration:none">${esc(a.name)}</a>${a.status === 'active' ? '<span class="coached">COACHED</span>' : ''}</h3>` +
    `<p>${esc(a.note || (a.goal ? 'Goal: ' + a.goal : 'No recent log'))}</p></div>${a.flags.map(chip).join(' ')}</div>`;
}

function wire(root, ctx) {
  const cls = root.querySelector('#cls'), date = root.querySelector('#date');
  if (cls) cls.onchange = e => { ctx.brief.classId = Number(e.target.value); ctx.brief.date = null; ctx.refresh(); };
  if (date) date.onchange = e => { ctx.brief.date = e.target.value; ctx.refresh(); };
}
