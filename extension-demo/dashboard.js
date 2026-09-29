// Dashboard shell: hash router + fetch/cache/stale handling. Components never see chrome.*.
import { renderInbox } from './components/inbox.js';
import { renderBrief } from './components/brief.js';
import { renderOwner } from './components/owner.js';
import { renderAthletes } from './components/athletes.js';
import { renderDrills } from './components/drills.js';
import { renderMember } from './components/member.js';
import { renderSettings } from './components/settings.js';
import { esc, ago } from './components/util.js';

const $ = s => document.querySelector(s);
const VIEWS = ['brief', 'inbox', 'athletes', 'drills', 'owner', 'settings', 'member'];

let adapter;
try {
  adapter = (await import('./adapter.js')).default;
} catch (e) {
  $('#view').innerHTML = '<p class="notice">Open this dashboard from the Cornerwork extension (toolbar icon) or from your magic link. ' + esc(e.message) + '</p>';
  throw e;
}

const state = { view: 'inbox', brief: { classId: null, date: null } };
const ctx = { adapter, brief: state.brief, refresh: () => show(), notify: msg => { $('#status').textContent = msg; },
              drills: () => adapter.api('GET', '/api/drills').catch(() => []) };
const hashParams = () => new URLSearchParams((location.hash.split('?')[1] || ''));

async function fetchView(view) {
  if (view === 'inbox') {
    const p = hashParams();  // #inbox?athlete=<id> (click-in) or #inbox?member=<gymdesk id>
    const scope = p.get('athlete') ? '?athlete=' + encodeURIComponent(p.get('athlete')) : p.get('member') ? '?member=' + encodeURIComponent(p.get('member')) : '';
    return adapter.api('GET', '/api/inbox' + scope);
  }
  if (view === 'owner') return adapter.api('GET', '/api/owner/summary');
  if (view === 'athletes') return adapter.api('GET', '/api/athletes');
  if (view === 'drills') return adapter.api('GET', '/api/drills');
  if (view === 'member') {  // #member?member=<gymdesk id> (Gymdesk member page) or #member?athlete=<id>
    const p = hashParams();
    const path = p.get('athlete') ? `/api/athletes/${encodeURIComponent(p.get('athlete'))}` : `/api/members/${encodeURIComponent(p.get('member') || '')}`;
    try { return await adapter.api('GET', path); } catch (e) { if (e.status === 404) return null; throw e; }
  }
  const classes = await adapter.api('GET', '/api/classes');
  const cls = classes.find(c => c.id === state.brief.classId) || classes[0];
  if (!cls) return { classes, brief: null };
  if (cls.id !== state.brief.classId) { state.brief.classId = cls.id; state.brief.date = cls.next_date || localToday(); }
  return { classes, brief: await adapter.api('GET', `/api/brief/${cls.id}/${state.brief.date}`) };
}

const localToday = () => { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };

function render(root, data) {
  ({ inbox: renderInbox, brief: renderBrief, owner: renderOwner, athletes: renderAthletes, drills: renderDrills, member: renderMember })[state.view](root, data, ctx);
}

async function refreshBadge(data) {
  try {
    const logs = data?.logs && !hashParams().get('athlete') && !hashParams().get('member') ? data.logs : (await adapter.api('GET', '/api/inbox')).logs;
    const open = logs.filter(l => !l.reply).length;
    const badge = $('#inbox-badge');
    badge.textContent = open;
    badge.classList.toggle('zero', open === 0);
  } catch { /* offline: keep the last badge */ }
}

async function show() {
  const view = (location.hash.slice(1) || 'inbox').split('?')[0];
  state.view = VIEWS.includes(view) ? view : 'inbox';
  document.body.classList.toggle('solo', state.view === 'member');  // member page: one person, no app chrome
  document.querySelectorAll('nav a').forEach(a => a.setAttribute('aria-current', a.dataset.view === state.view ? 'page' : 'false'));
  const root = $('#view'), stale = $('#stale');
  stale.hidden = true;
  if (state.view === 'settings') { refreshBadge(); return renderSettings(root, ctx); }
  try {
    const data = await fetchView(state.view);
    await adapter.cache.set(state.view, { data, at: Date.now() });
    render(root, data);
    refreshBadge(state.view === 'inbox' ? data : null);
  } catch (e) {
    const cached = await adapter.cache.get(state.view);
    if (cached) {
      render(root, cached.data);
      stale.textContent = `Stale · last synced ${ago(cached.at)} · ${e.message}`;
      stale.hidden = false;
    } else {
      root.innerHTML = `<p class="notice">Not connected: ${esc(e.message)}. ` +
        (adapter.container === 'extension' ? '<a href="#settings">Open Settings</a> to set the backend URL and gym token.' : 'Check your link.') + '</p>';
    }
  }
}

window.addEventListener('hashchange', show);
adapter.onChange(show);
show();
