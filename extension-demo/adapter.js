// Picks the container. The backend injects window.CW_ADAPTER="web" on /c/<token>; the extension leaves it unset.
// Components import this file and never touch chrome.* themselves.
const mod = window.CW_ADAPTER === 'web' ? await import('./adapter.web.js') : await import('./adapter.extension.js');
export default mod.default;
