(() => {
if(document.querySelector('#cornerwork-embedded'))return;
const path=location.pathname;
const member=/\/members\/[^/]+\/id\/(\d+)/.exec(path);
const context=member?(member[1]==='12672454'?'member':'unsupported'):(path.includes('/schedule')?'schedule':'queue');
const host=document.createElement('div');host.id='cornerwork-embedded';
const shadow=host.attachShadow({mode:'closed'});
const style=document.createElement('style');style.textContent=`:host{all:initial}button{position:fixed;right:24px;bottom:24px;z-index:2147483646;background:#234d40;color:white;border:0;border-radius:24px;padding:14px 22px;font:600 15px system-ui;cursor:pointer;box-shadow:0 3px 16px #0003}section{position:fixed;right:24px;bottom:80px;width:min(440px,calc(100vw - 32px));height:min(740px,calc(100vh - 110px));z-index:2147483646;background:#fafaf5;border:1px solid #cbd5c7;border-radius:14px;box-shadow:0 6px 32px #0004;overflow:hidden}section[hidden]{display:none}iframe{width:100%;height:100%;border:0}`;
const toggle=document.createElement('button');toggle.textContent='Cornerwork';toggle.setAttribute('aria-expanded','false');
const section=document.createElement('section');section.hidden=true;section.setAttribute('aria-label','Cornerwork coaching');
const frame=document.createElement('iframe');frame.title='Cornerwork coaching';frame.src=chrome.runtime.getURL('embedded.html')+'?context='+context;
section.append(frame);shadow.append(style,toggle,section);document.body.append(host);
function open(value){section.hidden=!value;toggle.setAttribute('aria-expanded',String(value));toggle.textContent=value?'Close Cornerwork':'Cornerwork';}
toggle.onclick=()=>open(section.hidden);
shadow.addEventListener('keydown',e=>{if(e.key==='Escape'){open(false);toggle.focus();}});
chrome.runtime.onMessage.addListener(message=>{if(message.type==='openCornerwork')open(true);});
})();
