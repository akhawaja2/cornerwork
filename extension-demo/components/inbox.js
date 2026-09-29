import { esc, when, initials, avatarClass } from './util.js';

export async function renderInbox(root, { logs, athlete }, ctx) {
  const open = logs.filter(l => !l.reply).length;
  const drills = open ? await ctx.drills() : [];
  const scope = athlete === null ? '<p class="notice">This Gymdesk member is not in Cornerwork yet. Import their attendance from Settings, or wait for them to text JOIN.</p>'
    : athlete ? `<p class="muted">${esc(athlete.name)} · ${esc(athlete.status)} · <a href="#inbox">all athletes</a></p>` : '';
  root.innerHTML = `<div class="mono">Inbox</div><h1>${open} awaiting reply</h1>` + scope +
    (logs.length ? logs.map(l => card(l, drills)).join('') : athlete === null ? '' : '<p class="card">No logs yet. Athletes text the gym number after class; their logs appear here.</p>');
  root.querySelectorAll('form[data-log]').forEach(form => form.onsubmit = async e => {
    e.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const drill = form.drill && form.drill.value ? Number(form.drill.value) : null;
      await ctx.adapter.api('POST', '/api/replies', { log_id: Number(form.dataset.log), body: form.body.value, drill_id: drill });
      ctx.notify('Reply sent.');
      ctx.refresh();
    } catch (err) {
      ctx.notify(err.message);
      button.disabled = false;
    }
  });
}

function card(l, drills) {
  const flags = [
    l.injury ? `<span class="chip injury">Injury · ${esc(l.injury.area || 'unspecified')}</span>` : '',
    l.concussion_flag ? '<span class="chip danger">Possible head injury · review now</span>' : '',
    ...(l.techniques || []).map(t => `<span class="tag">${esc(t)}</span>`),
  ].join(' ');
  const picker = drills.length ? `<label for="drill-${l.id}">Attach a drill (optional)</label><select id="drill-${l.id}" name="drill"><option value="">None</option>${drills.map(d => `<option value="${d.id}">${esc(d.title)}</option>`).join('')}</select>` : '';
  const reply = l.reply
    ? `<p><strong>Replied</strong> <small class="muted">${l.reply.sent_at ? when(l.reply.sent_at) : '(time unknown)'}</small></p><p class="message">${esc(l.reply.body)}</p>`
    : `<form data-log="${l.id}"><label for="reply-${l.id}">Your reply${l.coach_draft ? ' · AI draft, edit freely' : ''}</label>` +
      `<textarea id="reply-${l.id}" name="body" maxlength="1600" required>${esc(l.coach_draft || '')}</textarea>${picker}<p></p><button>Send reply</button></form>`;
  return `<article class="card" style="margin-bottom:14px"><div class="row"><span class="avatar ${avatarClass(l.athlete.id)}">${esc(initials(l.athlete.name))}</span>` +
    `<div><h3><a href="#inbox?athlete=${l.athlete.id}" style="color:inherit;text-decoration:none" title="Only this athlete">${esc(l.athlete.name)}</a>${l.athlete.status === 'active' ? '<span class="coached">COACHED</span>' : ''}</h3>` +
    `<small class="muted">${esc(l.athlete.status)} · ${when(l.created_at)}</small></div></div>` +
    (l.summary && l.summary !== l.transcript ? `<p style="margin-top:12px"><strong>${esc(l.summary)}</strong></p>` : '') +
    `<p class="message" style="margin-top:12px">${esc(l.transcript)}</p>${flags ? `<p>${flags}</p>` : ''}${reply}</article>`;
}
