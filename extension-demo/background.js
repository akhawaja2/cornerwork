importScripts('gymdesk-reader.js','core.js');
chrome.runtime.onInstalled.addListener(() => chrome.sidePanel.setPanelBehavior({openPanelOnActionClick:false}));
const DASHBOARD='dashboard.html';
const DEFAULT_CONFIG={backendUrl:'http://127.0.0.1:8765',token:''};
async function config(){const {cwConfig}=await chrome.storage.local.get('cwConfig');return {...DEFAULT_CONFIG,...(cwConfig||{})};}
// Backend proxy: the only place the extension talks to the backend. Token never leaves chrome.storage.
async function api(method,path,body){
 const cfg=await config();
 if(!cfg.token)throw Object.assign(Error('No API token. Open Settings and paste the gym token.'),{status:401});
 if(!/^\/api\/[\w\-\/.?=&%]*$/.test(path))throw Error('Only /api paths are proxied.');
 const r=await fetch(cfg.backendUrl+path,{method,headers:{Authorization:'Bearer '+cfg.token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined});
 const data=await r.json().catch(()=>null);
 if(!r.ok)throw Object.assign(Error(typeof data?.detail==='string'?data.detail:(r.statusText||'HTTP '+r.status)),{status:r.status});
 return data;
}
async function capture(tab) {
  if (!tab?.id || !tab.url?.startsWith('https://app.gymdesk.com/')) throw Error("Open Sarah Demo's Gymdesk Attendance page, then click the Cornerwork toolbar icon.");
  const results = await chrome.scripting.executeScript({target:{tabId:tab.id},func:readGymdeskAttendance});
  const snapshot = results[0]?.result;
  if (!snapshot) throw Error('No attendance could be read.');
  const saved=await chrome.storage.local.get('coachingState');
  const state=CW.apply(saved.coachingState||CW.seed(),'importGymdesk',{snapshot});
  let backend=null,backendError='';
  try{backend=await api('POST','/api/import/attendance',snapshot);}catch(e){backendError=e.message;}
  const gymdeskSync={at:new Date().toISOString(),records:snapshot.records.length,backend,backendError};
  await chrome.storage.local.set({gymdeskSnapshot:snapshot,gymdeskError:'',coachingState:state,gymdeskSync});
  return {snapshot,backend,backendError};
}
async function reportCapture(tab) {
  try { const r=await capture(tab); return {ok:true,snapshot:r.snapshot,data:r}; }
  catch(error) {
    const message = error.message.includes('Cannot access') ? 'Click the Cornerwork toolbar icon on the Gymdesk page to grant temporary access.' : error.message;
    await chrome.storage.local.set({gymdeskError:message});
    return {ok:false,error:message};
  }
}
chrome.action.onClicked.addListener(async tab => {
 if(!tab.url?.startsWith('https://app.gymdesk.com/manager/')){chrome.tabs.create({url:chrome.runtime.getURL(DASHBOARD)}).catch(console.error);return;}
 try {
 await chrome.scripting.executeScript({target:{tabId:tab.id},files:['gymdesk-embed.js']});
 await chrome.tabs.sendMessage(tab.id,{type:'openCornerwork'});
 if(tab.url.includes('/members/attendance/id/12672454'))await reportCapture(tab);
 }catch(e){console.error(e);}
});
let work=Promise.resolve();
chrome.runtime.onMessage.addListener((message,sender,respond) => {
 if(sender.id!==chrome.runtime.id||!sender.url?.startsWith('chrome-extension://'+chrome.runtime.id+'/'))return;
 if(!['readGymdesk','api','getConfig','setConfig'].includes(message?.type))return;
 work=work.catch(()=>{}).then(async()=>{
 if(message.type==='readGymdesk'){
 const tab=sender.tab|| (await chrome.tabs.query({active:true,currentWindow:true}))[0];return reportCapture(tab);
 }
 if(message.type==='api')return {ok:true,data:await api(message.method,message.path,message.body)};
 if(message.type==='getConfig'){const c=await config();const {gymdeskSync}=await chrome.storage.local.get('gymdeskSync');return {ok:true,data:{...c,container:'extension',lastImport:gymdeskSync?.at||''}};}
 const c={backendUrl:String(message.config?.backendUrl||'').trim().replace(/\/$/,''),token:String(message.config?.token||'').trim()};
 if(!/^https?:\/\/[^\s/]+$/.test(c.backendUrl))throw Error('Backend URL must look like http://127.0.0.1:8765 with no path.');
 await chrome.storage.local.set({cwConfig:c});return {ok:true,data:c};
 });
 work.then(respond,e=>respond({ok:false,error:e.message,status:e.status}));return true;
});
