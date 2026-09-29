import { esc } from './util.js';

export function renderBrief(root, { classes, brief }, ctx) {
  const options = classes.map(c => `<option value="${c.id}"${brief && c.id === brief.class.id ? ' selected' : ''}>${esc(c.name)}${c.start_time ? ' · ' + esc(c.start_time) : ''}</option>`).join('');
  const label = !brief ? '' :
    !brief.sources.length ? '<span class="badge">No bookings for this date</span>' :
    brief.sources.every(s => s === 'gymdesk' || s === 'csv') ? '<span class="badge">From imported attendance / roster</span>' :
    '<span class="badge warn">DEMO DATA</span>';
  const athletes = !brief ? '' : brief.athletes.length ? brief.athletes.map(a =>
    `<div class="item"><strong>${esc(a.name)}</strong> <small>${esc(a.booking_status)} · ${esc(a.status)}</small> ` +
    a.flags.map(f => `<span class="flag">${esc(f.type)}${f.detail ? ': ' + esc(f.detail) : ''}</span>`).join(' ') +
    `<p>${a.latest_summary ? esc(a.latest_summary) : '<span class="muted">No log in the last 7 days.</span>'}</p></div>`).join('')
    : '<p class="muted">Nobody booked or checked in for this date.</p>';
  root.innerHTML = `<h2>Pre-class brief</h2><div class="row"><label for="cls">Class</label><select id="cls">${options || '<option value="">No classes yet</option>'}</select>` +
    `<label for="date">Date</label><input id="date" type="date" value="${esc(ctx.brief.date)}"></div>` +
    (!brief ? '<p class="card">No classes yet. Import Gymdesk attendance from the extension Settings, or post a roster.</p>' :
      `<article class="card"><div class="row"><h3>${esc(brief.class.name)} · ${esc(brief.date)}${brief.class.start_time ? ' · ' + esc(brief.class.start_time) : ''}</h3>${label}</div>` +
      `<p><strong>Focus:</strong> ${esc(brief.focus)} <small>(${esc(brief.generator)})</small></p>` +
      (brief.themes.length ? '<p>' + brief.themes.map(t => `<span class="tag">${esc(t.name)} ×${t.count}</span>`).join(' ') + '</p>' : '') +
      ((brief.notes || []).length ? '<ul>' + brief.notes.map(n => `<li><strong>${esc(n.athlete)}:</strong> ${esc(n.note)}</li>`).join('') + '</ul>' : '') +
      athletes + '</article>');
  root.querySelector('#cls').onchange = e => { ctx.brief.classId = Number(e.target.value); ctx.refresh(); };
  root.querySelector('#date').onchange = e => { ctx.brief.date = e.target.value; ctx.refresh(); };
}
