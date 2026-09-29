// Dashboard shell: hash router + fetch/cache/stale handling. Components never see chrome.*.
import { renderInbox } from './components/inbox.js';
import { renderBrief } from './components/brief.js';
import { renderOwner } from './components/owner.js';
import { renderSettings } from './components/settings.js';
import { esc, ago } from './components/util.js';

const $ = s => document.querySelector(s);
const VIEWS = ['inbox', 'brief', 'owner', 'settings'];
const localToday = () => { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };

let adapter;
try {
  adapter = (await import('./adapter.js')).default;
} catch (e) {
  $('#view').innerHTML = '<p class="notice">Open this dashboard from the Cornerwork extension (toolbar icon) or from your magic link. ' + esc(e.message) + '</p>';
  throw e;
}

const state = { view: 'inbox', brief: { classId: null, date: localToday() } };
const ctx = { adapter, brief: state.brief, refresh: () => show(), notify: msg => { $('#status').textContent = msg; } };

const hashParams = () => new URLSearchParams((location.hash.split('?')[1] || ''));

async function fetchView(view) {
  if (view === 'inbox') {
    const p = hashParams();  // #inbox?athlete=<id> (click-in) or #inbox?member=<gymdesk id>
    const scope = p.get('athlete') ? '?athlete=' + encodeURIComponent(p.get('athlete')) : p.get('member') ? '?member=' + encodeURIComponent(p.get('member')) : '';
    return adapter.api('GET', '/api/inbox' + scope);
  }
  if (view === 'owner') return adapter.api('GET', '/api/owner/summary');
  const classes = await adapter.api('GET', '/api/classes');
  const cls = classes.find(c => c.id === state.brief.classId) || classes[0];
  if (!cls) return { classes, brief: null };
  state.brief.classId = cls.id;
  return { classes, brief: await adapter.api('GET', `/api/brief/${cls.id}/${state.brief.date}`) };
}

function render(root, data) {
  ({ inbox: renderInbox, brief: renderBrief, owner: renderOwner })[state.view](root, data, ctx);
}

async function show() {
  const view = (location.hash.slice(1) || 'inbox').split('?')[0];
  state.view = VIEWS.includes(view) ? view : 'inbox';
  document.querySelectorAll('nav a').forEach(a => a.setAttribute('aria-current', a.dataset.view === state.view ? 'page' : 'false'));
  const root = $('#view'), stale = $('#stale');
  stale.hidden = true;
  if (state.view === 'settings') return renderSettings(root, ctx);
  try {
    const data = await fetchView(state.view);
    await adapter.cache.set(state.view, { data, at: Date.now() });
    render(root, data);
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
