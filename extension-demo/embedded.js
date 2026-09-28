const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const context=new URLSearchParams(location.search).get('context');let view=context==='schedule'?'brief':'queue';
$('#context').textContent=context==='member'?'Sarah Demo · coaching history':context==='schedule'?'Sarah Demo · preparation for the next class':'Sarah Demo pilot queue';
async function render(){
try{
if(context==='unsupported'){$('#screen').textContent='This member is not connected to the pilot. Sarah’s feedback is not shown on other member profiles.';$('#refresh').hidden=true;return;}
const response=await chrome.runtime.sendMessage({type:'coachState'});if(!response.ok)throw Error(response.error);
const x=response.state?.sites?.gymdeskLive;
$('#queue').setAttribute('aria-pressed',view==='queue');$('#brief').setAttribute('aria-pressed',view==='brief');
$('#screen').innerHTML=(view==='queue'?'<h2>'+((x?.logs||[]).filter(l=>!l.reply).length)+' awaiting reply</h2>':'<h2>Sarah’s coaching brief</h2>')+(!x?'<p>Open the member test page once after updating to bring your existing coaching history into this panel. Then import Sarah’s attendance if needed.</p>':!(x.logs||[]).length?'<p>No member questions yet.</p>':x.logs.slice().reverse().map(l=>'<article class="card"><h3>Sarah Demo</h3><small>'+esc(l.attendanceTitle||'Member feedback')+'</small><p>'+esc(l.body||'Voice note')+'</p>'+(l.audio?'<audio controls preload="metadata" src="'+esc(l.audio)+'"></audio>':'')+(l.reply?'<strong>Coach reply</strong><p>'+esc(l.reply)+'</p>':view==='brief'?'<p>Awaiting coach reply</p>':'<form data-id="'+l.id+'"><label>Your reply<textarea required maxlength="2000"></textarea></label><button>Save reply</button></form>')+'</article>').join(''));
document.querySelectorAll('form').forEach(form=>form.onsubmit=async e=>{e.preventDefault();const button=form.querySelector('button');button.disabled=true;try{const r=await chrome.runtime.sendMessage({type:'coachReply',id:Number(form.dataset.id),body:form.querySelector('textarea').value});if(!r.ok)throw Error(r.error);await render();$('#status').textContent='Reply saved to Cornerwork.';}catch(e){$('#status').textContent=e.message;button.disabled=false;}});
}catch(e){$('#status').textContent=e.message;}}
$('#queue').onclick=()=>{view='queue';render()};$('#brief').onclick=()=>{view='brief';render()};
$('#refresh').onclick=async()=>{try{const r=await chrome.runtime.sendMessage({type:'readGymdesk'});if(!r.ok)throw Error(r.error);$('#status').textContent='Attendance imported.';await render();}catch(e){$('#status').textContent=e.message;}};
chrome.storage.onChanged.addListener((changes,area)=>{if(area==='local'&&changes.coachingState)render()});render();
