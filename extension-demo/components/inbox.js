import { esc, when } from './util.js';

export function renderInbox(root, { logs, athlete }, ctx) {
  const open = logs.filter(l => !l.reply).length;
  const scope = athlete === null ? '<p class="notice">This Gymdesk member is not in Cornerwork yet. Import their attendance from Settings, or wait for them to text JOIN.</p>'
    : athlete ? `<p class="muted">${esc(athlete.name)} · ${esc(athlete.status)} · <a href="#inbox">all athletes</a></p>` : '';
  root.innerHTML = `<h2>${open} awaiting reply</h2>` + scope +
    (logs.length ? logs.map(card).join('') : athlete === null ? '' : '<p class="card">No logs yet. Athletes text the gym number after class; their logs appear here.</p>');
  root.querySelectorAll('form[data-log]').forEach(form => form.onsubmit = async e => {
    e.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      await ctx.adapter.api('POST', '/api/replies', { log_id: Number(form.dataset.log), body: form.body.value });
      ctx.notify('Reply saved.');
      ctx.refresh();
    } catch (err) {
      ctx.notify(err.message);
      button.disabled = false;
    }
  });
}

function card(l) {
  const flags = [
    l.injury ? `<span class="flag">Injury · ${esc(l.injury.area || 'unspecified')}</span>` : '',
    l.concussion_flag ? '<span class="flag danger">Possible head injury · review now</span>' : '',
    ...(l.techniques || []).map(t => `<span class="tag">${esc(t)}</span>`),
  ].join(' ');
  const reply = l.reply
    ? `<p><strong>Replied</strong> <small>${l.reply.sent_at ? when(l.reply.sent_at) : '(time unknown)'}</small></p><p class="message">${esc(l.reply.body)}</p>`
    : `<form data-log="${l.id}"><label for="reply-${l.id}">Your reply${l.coach_draft ? ' (AI draft, edit freely)' : ''}</label>` +
      `<textarea id="reply-${l.id}" name="body" maxlength="1600" required>${esc(l.coach_draft || '')}</textarea><button>Send reply</button></form>`;
  return `<article class="card"><div class="row"><h3><a href="#inbox?athlete=${l.athlete.id}" title="Only this athlete">${esc(l.athlete.name)}</a></h3><small>${esc(l.athlete.status)} · ${when(l.created_at)}</small></div>` +
    (l.summary && l.summary !== l.transcript ? `<p><strong>${esc(l.summary)}</strong></p>` : '') +
    `<p class="message">${esc(l.transcript)}</p>${flags ? `<p>${flags}</p>` : ''}${reply}</article>`;
}
