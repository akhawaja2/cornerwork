import { esc, when, initials, avatarClass, chip } from './util.js';

export function renderAthletes(root, athletes) {
  const active = athletes.filter(a => a.status === 'active').length;
  root.innerHTML = `<div class="mono">Roster</div><h1>Athletes</h1><p class="muted">${athletes.length} on the roster · ${active} coached (opted in) · names come from Gymdesk or the athlete's JOIN text</p>` +
    `<section class="card">` + (athletes.length ? athletes.map(a =>
      `<div class="person"><span class="avatar ${avatarClass(a.id)}">${esc(initials(a.name))}</span><div class="body">` +
      `<h3><a href="#inbox?athlete=${a.id}" style="color:inherit;text-decoration:none">${esc(a.name)}</a>${a.status === 'active' ? '<span class="coached">COACHED</span>' : ''}</h3>` +
      `<p>${esc(a.status)}${a.phone_last4 ? ' · ···' + esc(a.phone_last4) : ''}${a.gymdesk_member_id ? ' · Gymdesk ' + esc(a.gymdesk_member_id) : ''} · ` +
      `${a.last_log_at ? 'last log ' + when(a.last_log_at) : 'no logs'} · ${a.logs_7d} this week</p></div>${a.flags.map(chip).join(' ')}</div>`).join('')
      : '<p class="muted">No athletes yet. Import Gymdesk attendance or wait for the first JOIN text.</p>') + '</section>';
}
