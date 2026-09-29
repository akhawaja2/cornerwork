# Cornerwork extension — v0.4.0

The extension is the app for gym staff. One dashboard bundle (`dashboard.html` + `components/`) runs in three containers:

| Container | How it opens | Notes |
|---|---|---|
| Extension tab | Click the toolbar icon on any non-Gymdesk page, or right-click the icon > Options | Full inbox, brief, owner, settings |
| Inside Gymdesk (floating panel) | On any `app.gymdesk.com/manager/*` page: the floating **Cornerwork** button, or the toolbar icon | Schedule pages open the brief; other pages the inbox |
| Chrome side panel | Chrome's side panel menu > Cornerwork | `panel.html` redirects to the brief |
| Phone / any browser | `http://<backend>/c/<token>` | Same bundle served by the backend with the web adapter |

Components never touch `chrome.*`. `adapter.js` picks `adapter.extension.js` (runtime messaging to `background.js`, which holds the token and proxies `/api/*`) or `adapter.web.js` (fetch + localStorage). The backend is the store of record; Chrome storage holds config, the last Gymdesk snapshot and a render cache for the offline "stale" bar.

## Install / update

1. `chrome://extensions` > Load unpacked `extension-demo` (or **Reload** if installed). Chrome may ask to approve the new host permissions (`127.0.0.1`, `localhost`) and site access for `app.gymdesk.com`.
2. Start the backend (`..\start.ps1`), which prints and copies the gym token.
3. Click the toolbar icon > **Settings** > backend URL + token > **Save and test**.
4. Open Sarah Demo's attendance page in Gymdesk, then Settings > **Import attendance from the open Gymdesk tab**. The snapshot is stored locally and posted to `/api/import/attendance`.

## Gymdesk import

`gymdesk-reader.js` reads rendered, saved attendance rows for Sarah Demo (member 12672454) at AKLabs MMA using `activeTab` + `scripting`. No hidden requests, credentials, Gymdesk writes or background sync. Only rows loaded on the open page are read (max 100). Gymdesk markup changes may require updating the reader. Generalising to any member and to schedule/roster pages is Phase 6.

## Test harness

`index.html?harness=1` is the old member simulator (fixtures, voice recorder). It is not linked from the product and redirects to the dashboard without `?harness=1`. `start-preview.ps1` serves this folder on http://127.0.0.1:8766 for that harness only; the dashboard needs the extension or the backend `/c/<token>` route.

## Validation

- `node test-core.cjs`, `node test-gymdesk.cjs`: fixture state machine and reader validation.
- `node test-background.cjs`: worker routing, config validation, backend proxy (auth header, body, error mapping), snapshot POST, toolbar click. Chrome APIs are mocked; this does not prove installed-Chrome behaviour.
- Verified in a browser via `/c/<token>`: inbox, reply, brief, owner, stale bar with the backend down.
- **Not yet verified in installed Chrome after v0.4:** toolbar > dashboard tab, Settings > Save and test, floating panel on Gymdesk, side panel. Gymdesk's frame policy for the iframe is unchanged from v0.3 (same injection mechanism), but confirm it.

Chrome permission reference: https://developer.chrome.com/docs/extensions/develop/concepts/activeTab
