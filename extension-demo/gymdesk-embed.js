// Content script on https://app.gymdesk.com/manager/*. Mirrors Gymdesk's own hierarchy:
//   1. Left rail item "Cornerwork" (beside Dashboard, Members, Gym...) -> the whole app in the content area.
//   2. Member page tab "Cornerwork" (beside Profile, Messaging, Attendance) -> that one member's coaching page.
// Both swap Gymdesk's content for an iframe of dashboard.html kept inside a closed shadow root (an extension iframe in the
// light DOM gets dropped). Gymdesk's own links keep working as normal navigations. Nothing here reads or writes Gymdesk data.
(() => {
if(document.querySelector('#cornerwork-rail'))return;
const dashboard=chrome.runtime.getURL('dashboard.html');
const member=/\/manager\/members\/[^/]+\/id\/(\d+)/.exec(location.pathname)?.[1];
const path=location.pathname+location.search;
const ICON='data:image/svg+xml;utf8,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 21" fill="none" stroke="#eae6df" stroke-width="2.2" stroke-linecap="round"><path d="M15.5 6.2A6.5 6.5 0 1 0 15.5 14.8"/><path d="M6.5 10.5h5"/></svg>');

function frameSection(hash,height){
 const section=document.createElement('div');section.id='cornerwork-section';section.style.cssText='width:100%;padding:0';
 const frame=document.createElement('iframe');frame.title='Cornerwork';frame.src=dashboard+'#'+hash;
 frame.style.cssText='width:100%;height:'+height+';border:0;background:#f4f1ea;display:block';
 section.attachShadow({mode:'closed'}).append(frame);return section;
}

// --- 1. Left rail: the whole app --------------------------------------------------------------------
const rail=document.querySelector('#menu ul');
const body=document.querySelector('#body');
let appSection=null;
if(rail&&body){
 const li=document.createElement('li');const a=document.createElement('a');
 a.id='cornerwork-rail';a.className='cornerwork';a.href='#cornerwork';a.textContent='Cornerwork';
 a.style.cssText='background-image:url("'+ICON+'");background-repeat:no-repeat;background-position:50% 11px;background-size:20px 21px';
 li.append(a);
 const anchor=rail.querySelector('a.settings')?.parentElement;anchor?rail.insertBefore(li,anchor):rail.append(li);
 function openApp(){
  if(!appSection){appSection=frameSection('brief','calc(100vh - 8px)');body.append(appSection);}
  [...body.children].forEach(c=>{if(c!==appSection)c.style.display='none';});
  rail.querySelectorAll('a.selected').forEach(x=>x.classList.remove('selected'));a.classList.add('selected');
  history.replaceState(null,'',path+'#cornerwork');
 }
 a.onclick=e=>{e.preventDefault();openApp();};
 chrome.runtime.onMessage.addListener(message=>{if(message.type==='openCornerwork'&&!member)openApp();});
 if(location.hash==='#cornerwork'&&!member)openApp();
}

// --- 2. Member page tab: one person -------------------------------------------------------------------
const subnav=member&&document.querySelector('div.subnav ul');
if(subnav){
 const li=document.createElement('li');const tab=document.createElement('a');
 tab.href='#cornerwork';tab.textContent='Cornerwork';tab.id='cornerwork-tab';li.append(tab);subnav.append(li);
 const main=subnav.closest('div.main')||subnav.parentElement.parentElement;
 let section=null;
 function show(on){
  if(on&&!section){section=frameSection('member?member='+member,'calc(100vh - 180px)');section.className='profile-section';section.style.width='min(1100px,100%)';main.append(section);}
  [...main.children].forEach(c=>{if(c!==section&&!c.classList.contains('subnav'))c.style.display=on?'none':'';});
  if(section)section.hidden=!on;
  subnav.querySelectorAll('a').forEach(x=>x.classList.toggle('selected',on?x===tab:x.getAttribute('href')?.includes('/'+location.pathname.split('/')[3]+'/')));
  if(on)history.replaceState(null,'',path+'#cornerwork');
 }
 tab.onclick=e=>{e.preventDefault();show(true);};
 subnav.querySelectorAll('a:not(#cornerwork-tab)').forEach(x=>x.addEventListener('click',()=>show(false)));
 chrome.runtime.onMessage.addListener(message=>{if(message.type==='openCornerwork')show(true);});
 if(location.hash==='#cornerwork')show(true);
}
})();
