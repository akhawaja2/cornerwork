import { esc } from './util.js';

export function renderDrills(root, drills, ctx) {
  root.innerHTML = `<div class="mono">Coach library</div><h1>Drill library</h1><p class="muted">Attach a drill to a reply; the athlete gets the title and link in the text.</p>` +
    `<div class="cols"><section class="card">` + (drills.length ? drills.map(d =>
      `<div class="person"><div class="body"><h3>${esc(d.title)}</h3><p>${d.url ? `<a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.url)}</a>` : '<span class="muted">no link</span>'} ${(d.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join('')}</p></div>` +
      `<button class="ghost" data-del="${d.id}">Remove</button></div>`).join('') : '<p class="muted">No drills yet. Add the first one on the right.</p>') +
    `</section><section class="card"><h2>Add a drill</h2><form id="drill"><label for="t">Title</label><input id="t" name="title" required maxlength="120" placeholder="Jab + pivot exit">` +
    `<label for="u">Link (video or doc, optional)</label><input id="u" name="url" type="url" placeholder="https://">` +
    `<label for="g">Tags (comma separated)</label><input id="g" name="tags" placeholder="jab, footwork"><p></p><button>Add drill</button></form></section></div>`;
  root.querySelector('#drill').onsubmit = async e => {
    e.preventDefault();
    const f = e.target;
    try {
      await ctx.adapter.api('POST', '/api/drills', { title: f.title.value, url: f.url.value || null, tags: f.tags.value.split(',').map(t => t.trim()).filter(Boolean) });
      ctx.notify('Drill added.');
      ctx.refresh();
    } catch (err) { ctx.notify(err.message); }
  };
  root.querySelectorAll('button[data-del]').forEach(b => b.onclick = async () => {
    try { await ctx.adapter.api('DELETE', `/api/drills/${b.dataset.del}`); ctx.refresh(); } catch (err) { ctx.notify(err.message); }
  });
}
