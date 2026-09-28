import { esc } from './util.js';

export async function renderSettings(root, ctx) {
  const a = ctx.adapter;
  const cfg = await a.config();
  if (a.container === 'web') {
    root.innerHTML = `<h2>Settings</h2><p class="card">You opened Cornerwork through a magic link on ${esc(cfg.backendUrl)}. Keep the link private; it is your login. Gymdesk import runs in the Chrome extension.</p>`;
    return;
  }
  root.innerHTML = `<h2>Settings</h2><form id="cfg" class="card"><label for="url">Backend URL</label>` +
    `<input id="url" name="backendUrl" type="url" value="${esc(cfg.backendUrl || 'http://127.0.0.1:8765')}" required>` +
    `<label for="tok">Gym API token</label><input id="tok" name="token" type="password" value="${esc(cfg.token || '')}" autocomplete="off" required>` +
    `<p class="muted">Get the token with <code>python scripts/issue_token.py</code> on the machine running the backend.</p><button>Save and test</button></form>` +
    `<section class="card"><h3>Gymdesk</h3><p>Open Sarah Demo's Attendance page in another tab, then:</p>` +
    `<button id="import" class="secondary">Import attendance from the open Gymdesk tab</button>` +
    `<p id="import-status" class="muted">${cfg.lastImport ? 'Last import: ' + esc(cfg.lastImport) : 'No import yet.'}</p></section>`;
  root.querySelector('#cfg').onsubmit = async e => {
    e.preventDefault();
    const f = e.target;
    try {
      await a.setConfig({ backendUrl: f.backendUrl.value.trim().replace(/\/$/, ''), token: f.token.value.trim() });
      await a.api('GET', '/api/owner/summary');
      ctx.notify('Connected to the backend.');
    } catch (err) {
      ctx.notify('Saved, but the backend said: ' + err.message);
    }
  };
  root.querySelector('#import').onclick = async () => {
    const p = root.querySelector('#import-status');
    p.textContent = 'Reading…';
    try {
      const r = await a.importGymdesk();
      p.textContent = `Read ${r.snapshot.records.length} attendance record(s). ` +
        (r.backend ? `Backend created ${r.backend.created} new booking(s).` : `Backend not updated: ${r.backendError || 'unknown error'}`);
    } catch (err) {
      p.textContent = err.message;
    }
  };
}
