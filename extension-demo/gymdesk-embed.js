// Content script on https://app.gymdesk.com/manager/*.
// 1. Member pages (/manager/members/<section>/id/<memberId>): adds a "Cornerwork" tab to Gymdesk's own sub-nav
//    (Profile · Messaging · Attendance · ...). Clicking it swaps the page section for the dashboard bundle, scoped
//    to that member (#inbox?member=<id>). Gymdesk's other tabs keep working as normal links.
// 2. Every manager page: a floating Cornerwork button that opens the same bundle in a small panel.
// Reads nothing from Gymdesk here and never modifies Gymdesk records.
(() => {
if(document.querySelector('#cornerwork-embedded'))return;
const dashboard=chrome.runtime.getURL('dashboard.html');
const member=/\/manager\/members\/[^/]+\/id\/(\d+)/.exec(location.pathname)?.[1];
const view=location.pathname.includes('/schedule')?'brief':'inbox';

// --- 1. Cornerwork tab in the member sub-nav --------------------------------------------------------
const subnav=member&&document.querySelector('div.subnav ul');
if(subnav){
 const li=document.createElement('li');const tab=document.createElement('a');
 tab.href='#cornerwork';tab.textContent='Cornerwork';tab.id='cornerwork-tab';li.append(tab);subnav.append(li);
 const main=subnav.closest('div.main')||subnav.parentElement.parentElement;
 const section=document.createElement('div');section.className='profile-section';section.id='cornerwork-section';section.hidden=true;
 section.style.cssText='width:min(1100px,100%);min-height:calc(100vh - 180px)';
 const frame=document.createElement('iframe');frame.title='Cornerwork';frame.style.cssText='width:100%;height:calc(100vh - 180px);border:0;background:#f4f3ed;border-radius:12px';
 section.append(frame);main.append(section);
 const others=[...main.children].filter(c=>c!==section&&!c.classList.contains('subnav'));
 function show(on){
  if(on&&!frame.src)frame.src=dashboard+'#'+view+'?member='+member;
  others.forEach(c=>c.style.display=on?'none':'');section.hidden=!on;
  subnav.querySelectorAll('a').forEach(a=>a.classList.toggle('selected',on?a===tab:a.getAttribute('href')?.includes('/'+location.pathname.split('/')[3]+'/')));
 }
 tab.onclick=e=>{e.preventDefault();history.replaceState(null,'','#cornerwork');show(true);};
 subnav.querySelectorAll('a:not(#cornerwork-tab)').forEach(a=>a.addEventListener('click',()=>show(false)));
 if(location.hash==='#cornerwork')show(true);
}

// --- 2. Floating panel ---------------------------------------------------------------------------
const host=document.createElement('div');host.id='cornerwork-embedded';
const shadow=host.attachShadow({mode:'closed'});
const style=document.createElement('style');style.textContent=`:host{all:initial}button{position:fixed;right:24px;bottom:24px;z-index:2147483646;background:#234d40;color:white;border:0;border-radius:24px;padding:14px 22px;font:600 15px system-ui;cursor:pointer;box-shadow:0 3px 16px #0003}section{position:fixed;right:24px;bottom:80px;width:min(460px,calc(100vw - 32px));height:min(760px,calc(100vh - 110px));z-index:2147483646;background:#f4f3ed;border:1px solid #cbd5c7;border-radius:14px;box-shadow:0 6px 32px #0004;overflow:hidden}section[hidden]{display:none}iframe{width:100%;height:100%;border:0}`;
const toggle=document.createElement('button');toggle.textContent='Cornerwork';toggle.setAttribute('aria-expanded','false');
const section=document.createElement('section');section.hidden=true;section.setAttribute('aria-label','Cornerwork coaching');
const frame=document.createElement('iframe');frame.title='Cornerwork coaching';
section.append(frame);shadow.append(style,toggle,section);document.body.append(host);
function open(value){
 if(value&&!frame.src)frame.src=dashboard+'#'+view+(member?'?member='+member:''); // load the bundle on first open only
 section.hidden=!value;toggle.setAttribute('aria-expanded',String(value));toggle.textContent=value?'Close Cornerwork':'Cornerwork';
}
toggle.onclick=()=>open(section.hidden);
shadow.addEventListener('keydown',e=>{if(e.key==='Escape'){open(false);toggle.focus();}});
chrome.runtime.onMessage.addListener(message=>{if(message.type==='openCornerwork')open(true);});
})();
