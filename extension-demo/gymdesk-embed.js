// Content script on https://app.gymdesk.com/manager/*: a floating Cornerwork button that opens the shared dashboard
// bundle in an isolated iframe. Schedule pages open the brief; everything else opens the inbox. Reads nothing from
// Gymdesk itself (attendance import runs from Settings via the background worker) and never modifies Gymdesk records.
(() => {
if(document.querySelector('#cornerwork-embedded'))return;
const view=location.pathname.includes('/schedule')?'brief':'inbox';
const host=document.createElement('div');host.id='cornerwork-embedded';
const shadow=host.attachShadow({mode:'closed'});
const style=document.createElement('style');style.textContent=`:host{all:initial}button{position:fixed;right:24px;bottom:24px;z-index:2147483646;background:#234d40;color:white;border:0;border-radius:24px;padding:14px 22px;font:600 15px system-ui;cursor:pointer;box-shadow:0 3px 16px #0003}section{position:fixed;right:24px;bottom:80px;width:min(460px,calc(100vw - 32px));height:min(760px,calc(100vh - 110px));z-index:2147483646;background:#f4f3ed;border:1px solid #cbd5c7;border-radius:14px;box-shadow:0 6px 32px #0004;overflow:hidden}section[hidden]{display:none}iframe{width:100%;height:100%;border:0}`;
const toggle=document.createElement('button');toggle.textContent='Cornerwork';toggle.setAttribute('aria-expanded','false');
const section=document.createElement('section');section.hidden=true;section.setAttribute('aria-label','Cornerwork coaching');
const frame=document.createElement('iframe');frame.title='Cornerwork coaching';
section.append(frame);shadow.append(style,toggle,section);document.body.append(host);
function open(value){
 if(value&&!frame.src)frame.src=chrome.runtime.getURL('dashboard.html')+'#'+view; // load the bundle on first open only
 section.hidden=!value;toggle.setAttribute('aria-expanded',String(value));toggle.textContent=value?'Close Cornerwork':'Cornerwork';
}
toggle.onclick=()=>open(section.hidden);
shadow.addEventListener('keydown',e=>{if(e.key==='Escape'){open(false);toggle.focus();}});
chrome.runtime.onMessage.addListener(message=>{if(message.type==='openCornerwork')open(true);});
})();
