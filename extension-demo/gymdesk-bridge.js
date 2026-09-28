(() => {
const status=document.querySelector('#connection-status'),button=document.querySelector('#sync-gymdesk');
if(!globalThis.chrome?.runtime?.id||!chrome.storage){if(button)button.disabled=true;if(status)status.textContent='Live import works in the installed Chrome extension. This HTTP preview cannot access Gymdesk.';return;}
let ready=false;
const originalUpdate=CW.update;
CW.update=(action,payload)=>{
 if(!ready)throw Error('Coaching data is loading. Please try again.');
 const state=originalUpdate(action,payload);
 chrome.storage.local.set({coachingState:state}).catch(e=>{if(status)status.textContent=e.message;});return state;
};
function show(data){
 if(data.coachingState){CW.save(data.coachingState);window.dispatchEvent(new Event('cw-import'));}
 if(status&&data.gymdeskSnapshot){const s=data.gymdeskSnapshot;status.textContent='Last read: '+new Date(s.observedAt).toLocaleString()+' · '+s.records.length+' attendance record(s). Local demo prompt only; no SMS.';}
 if(status&&data.gymdeskError)status.textContent=data.gymdeskError+' Previous imported data is retained.';
}
(async()=>{
 try{
 const data=await chrome.storage.local.get(['coachingState','gymdeskSnapshot','gymdeskError']);
 const local=CW.read();
 // One-time migration of the pre-embedded extension's localStorage history.
 if(!localStorage.getItem('cornerwork-shared-migrated')){
  if(!data.coachingState)data.coachingState=local;
  else if(local.sites.gymdeskLive?.logs.length&&!data.coachingState.sites.gymdeskLive?.logs.length){
   data.coachingState.sites.gymdeskLive={...data.coachingState.sites.gymdeskLive,...local.sites.gymdeskLive};
  }
  await chrome.storage.local.set({coachingState:data.coachingState});
  localStorage.setItem('cornerwork-shared-migrated','1');
 }
 ready=true;show(data);
 }catch(e){if(status)status.textContent='Could not load coaching data: '+e.message;}
})();
chrome.storage.onChanged.addListener((changes,area)=>{
 if(area==='local'&&(changes.coachingState||changes.gymdeskSnapshot||changes.gymdeskError))chrome.storage.local.get(['coachingState','gymdeskSnapshot','gymdeskError']).then(show).catch(e=>{if(status)status.textContent=e.message;});
});
if(button)button.onclick=async()=>{
 button.disabled=true;
 try{const r=await chrome.runtime.sendMessage({type:'readGymdesk'});if(!r?.ok)throw Error(r?.error||'Could not read attendance.');}
 catch(e){if(status)status.textContent=e.message;}finally{button.disabled=false;}
};
})();
