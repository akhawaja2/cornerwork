// Extension container. The only dashboard file besides background.js allowed to reference chrome.*.
if (!globalThis.chrome?.runtime?.id) throw new Error('Not running inside the Chrome extension.');

const send = message => new Promise((resolve, reject) => chrome.runtime.sendMessage(message, r => {
  if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
  if (r?.ok) return resolve(r.data);
  reject(Object.assign(new Error(r?.error || 'Extension error'), { status: r?.status }));
}));

export default {
  container: 'extension',
  api: (method, path, body) => send({ type: 'api', method, path, body }),
  config: () => send({ type: 'getConfig' }),
  setConfig: config => send({ type: 'setConfig', config }),
  importGymdesk: () => send({ type: 'readGymdesk' }),
  cache: {
    get: async key => (await chrome.storage.local.get('cwCache')).cwCache?.[key] ?? null,
    set: async (key, value) => {
      const { cwCache = {} } = await chrome.storage.local.get('cwCache');
      await chrome.storage.local.set({ cwCache: { ...cwCache, [key]: value } });
    },
  },
  openLink: url => chrome.tabs.create({ url }),
  onChange: cb => chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && (changes.gymdeskSync || changes.cwConfig)) cb();
  }),
};
