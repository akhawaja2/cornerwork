importScripts('gymdesk-reader.js','core.js');
chrome.runtime.onInstalled.addListener(() => chrome.sidePanel.setPanelBehavior({openPanelOnActionClick:false}));
async function capture(tab) {
  if (!tab?.id || !tab.url?.startsWith('https://app.gymdesk.com/')) throw Error("Open Sarah Demo's Gymdesk Attendance page, then click the Cornerwork toolbar icon.");
  const results = await chrome.scripting.executeScript({target:{tabId:tab.id},func:readGymdeskAttendance});
  const snapshot = results[0]?.result;
  if (!snapshot) throw Error('No attendance could be read.');
  const saved=await chrome.storage.local.get('coachingState');
  const state=CW.apply(saved.coachingState||CW.seed(),'importGymdesk',{snapshot});
  await chrome.storage.local.set({gymdeskSnapshot:snapshot,gymdeskError:'',coachingState:state});
  return snapshot;
}
async function reportCapture(tab) {
  try { return {ok:true,snapshot:await capture(tab)}; }
  catch(error) {
    const message = error.message.includes('Cannot access') ? 'Click the Cornerwork toolbar icon on the Gymdesk page to grant temporary access.' : error.message;
    await chrome.storage.local.set({gymdeskError:message});
    return {ok:false,error:message};
  }
}
chrome.action.onClicked.addListener(async tab => {
 if(!tab.url?.startsWith('https://app.gymdesk.com/manager/')){chrome.sidePanel.open({windowId:tab.windowId}).catch(console.error);return;}
 try {
 await chrome.scripting.executeScript({target:{tabId:tab.id},files:['gymdesk-embed.js']});
 await chrome.tabs.sendMessage(tab.id,{type:'openCornerwork'});
 if(tab.url.includes('/members/attendance/id/12672454'))await reportCapture(tab);
 }catch(e){console.error(e);}
});
let work=Promise.resolve();
chrome.runtime.onMessage.addListener((message,sender,respond) => {
 if(sender.id!==chrome.runtime.id||!sender.url?.startsWith('chrome-extension://'+chrome.runtime.id+'/'))return;
 if(!['readGymdesk','coachState','coachReply'].includes(message?.type))return;
 work=work.catch(()=>{}).then(async()=>{
 if(message.type==='readGymdesk'){
 const tab=sender.tab|| (await chrome.tabs.query({active:true,currentWindow:true}))[0];return reportCapture(tab);
 }
 const saved=await chrome.storage.local.get('coachingState');
 if(message.type==='coachState')return {ok:true,state:saved.coachingState||null};
 if(!saved.coachingState?.sites?.gymdeskLive)throw Error('Import attendance first.');
 const selected=saved.coachingState.provider;
 const state=CW.apply({...saved.coachingState,provider:'gymdeskLive'},'reply',{id:message.id,body:message.body});state.provider=selected;
 await chrome.storage.local.set({coachingState:state});return {ok:true};
 });
 work.then(respond,e=>respond({ok:false,error:e.message}));return true;
});
