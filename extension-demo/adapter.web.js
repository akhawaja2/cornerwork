// Web container: the same bundle served by the backend at /c/<token>. Token lives in the URL only.
const token = decodeURIComponent((location.pathname.split('/c/')[1] || '').split('/')[0]);

async function api(method, path, body) {
  const r = await fetch(path, {
    method,
    headers: { Authorization: 'Bearer ' + token, ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => null);
  if (!r.ok) throw Object.assign(new Error(data?.detail?.toString?.() || r.statusText || 'HTTP ' + r.status), { status: r.status });
  return data;
}

export default {
  container: 'web',
  api,
  config: async () => ({ backendUrl: location.origin, token: token ? 'set-by-link' : '', container: 'web', lastImport: '' }),
  setConfig: async () => { throw new Error('Settings come from the magic link on the web.'); },
  importGymdesk: async () => { throw new Error('Gymdesk import runs in the Chrome extension.'); },
  cache: {
    get: async key => { try { return JSON.parse(localStorage.getItem('cw:' + key) || 'null'); } catch { return null; } },
    set: async (key, value) => { try { localStorage.setItem('cw:' + key, JSON.stringify(value)); } catch {} },
  },
  openLink: url => window.open(url, '_blank', 'noopener'),
  onChange: () => {},
};
