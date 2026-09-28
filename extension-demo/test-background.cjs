const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const events={},stored={},calls=[],fetches=[],tabsCreated=[];
const snapshot={memberId:'12672454',memberName:'Sarah Demo',gym:'AKLabs MMA',records:[{id:'62252846',sessionId:'1832536',title:'Boxing',date:'09/28/2026',when:'Sep 28, 2026 7:00 AM',duration:'1h'}]};
let fail=false,fetchResponse={ok:true,status:200,json:async()=>({logs:[]})};
const context={console,CW:require('./core.js'),importScripts:()=>{},readGymdeskAttendance:()=>{},
 fetch:async(url,init)=>{fetches.push({url,init});return fetchResponse;},
 chrome:{
 runtime:{id:'test',getURL:p=>'chrome-extension://test/'+p,onInstalled:{addListener:fn=>events.install=fn},onMessage:{addListener:fn=>events.message=fn}},
 sidePanel:{setPanelBehavior:async x=>calls.push(x),open:async x=>calls.push(x)},
 action:{onClicked:{addListener:fn=>events.click=fn}},
 tabs:{query:async()=>[{id:7,url:'https://app.gymdesk.com/manager/members/attendance/id/12672454'}],create:async x=>{tabsCreated.push(x);return x;}},
 scripting:{executeScript:async x=>{calls.push(x);if(fail)throw Error('Cannot access contents of the page');return [{result:snapshot}];}},
 storage:{local:{get:async()=>stored,set:async x=>Object.assign(stored,x)}}
}};
vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/background.js','utf8'),context);
const ui={id:'test',url:'chrome-extension://test/dashboard.html'};
const ask=(message,sender=ui)=>new Promise(resolve=>{assert.equal(events.message(message,sender,resolve),true)});
(async()=>{
 // Import without a token: snapshot stored, backend skipped with a clear error.
 const response=await ask({type:'readGymdesk'},{id:'test',url:'chrome-extension://test/index.html'});
 assert.equal(response.ok,true);assert.equal(stored.gymdeskSnapshot,snapshot);assert.equal(calls[0].target.tabId,7);
 assert.equal(response.data.backend,null);assert.match(response.data.backendError,/token/);assert.equal(fetches.length,0);
 // Embedded quick view still works.
 stored.coachingState=require('./core.js').apply(stored.coachingState,'note',{body:'Embedded reply test'});
 const reply=await ask({type:'coachReply',id:1,body:'Review before class'},{id:'test',url:'chrome-extension://test/embedded.html'});
 assert.equal(reply.ok,true);assert.equal(stored.coachingState.sites.gymdeskLive.logs[0].reply,'Review before class');
 const duplicate=await ask({type:'coachReply',id:1,body:'Duplicate'},{id:'test',url:'chrome-extension://test/embedded.html'});
 assert.equal(duplicate.ok,false);
 const read=await ask({type:'coachState'},{id:'test',url:'chrome-extension://test/embedded.html'});
 assert.equal(read.state.sites.gymdeskLive.logs[0].body,'Embedded reply test');
 // Config + API proxy.
 const noToken=await ask({type:'api',method:'GET',path:'/api/inbox'});
 assert.equal(noToken.ok,false);assert.equal(noToken.status,401);
 const badUrl=await ask({type:'setConfig',config:{backendUrl:'not-a-url',token:'t'}});
 assert.equal(badUrl.ok,false);
 const saved=await ask({type:'setConfig',config:{backendUrl:'http://127.0.0.1:8777/',token:' tok123 '}});
 assert.equal(JSON.stringify(saved.data),JSON.stringify({backendUrl:'http://127.0.0.1:8777',token:'tok123'})); // vm objects have a different prototype
 const cfg=await ask({type:'getConfig'});
 assert.equal(cfg.data.token,'tok123');assert.equal(cfg.data.container,'extension');
 const inbox=await ask({type:'api',method:'GET',path:'/api/inbox'});
 assert.equal(JSON.stringify(inbox),JSON.stringify({ok:true,data:{logs:[]}}));
 assert.equal(fetches[0].url,'http://127.0.0.1:8777/api/inbox');assert.equal(fetches[0].init.headers.Authorization,'Bearer tok123');
 const posted=await ask({type:'api',method:'POST',path:'/api/replies',body:{log_id:1,body:'Thanks!'}});
 assert.equal(posted.ok,true);assert.equal(fetches[1].init.body,'{"log_id":1,"body":"Thanks!"}');
 fetchResponse={ok:false,status:409,json:async()=>({detail:'This log already has a reply.'})};
 const conflict=await ask({type:'api',method:'POST',path:'/api/replies',body:{log_id:1,body:'Again'}});
 assert.equal(conflict.ok,false);assert.equal(conflict.status,409);assert.match(conflict.error,/already has a reply/);
 const outside=await ask({type:'api',method:'GET',path:'/health'});
 assert.equal(outside.ok,false);assert.match(outside.error,/Only \/api/);
 // Import with a token posts the snapshot to the backend.
 fetchResponse={ok:true,status:200,json:async()=>({athlete_id:1,records:1,created:0})};
 const synced=await ask({type:'readGymdesk'});
 assert.equal(synced.ok,true);assert.equal(synced.data.backend.created,0);assert.equal(fetches.at(-1).url,'http://127.0.0.1:8777/api/import/attendance');
 assert.equal(stored.gymdeskSync.records,1);
 // Permission failure keeps the last snapshot.
 fail=true;
 const failure=await ask({type:'readGymdesk'},{id:'test',url:'chrome-extension://test/panel.html'});
 assert.equal(failure.ok,false);assert.match(failure.error,/toolbar/);assert.equal(stored.gymdeskSnapshot,snapshot);
 assert.equal(events.message({type:'readGymdesk'},{id:'test',url:'https://app.gymdesk.com'},()=>{throw Error('untrusted sender')}),undefined);
 // Toolbar click outside Gymdesk opens the dashboard tab.
 await events.click({id:9,url:'https://example.com/'});
 assert.equal(tabsCreated[0].url,'chrome-extension://test/dashboard.html');
 console.log('PASS: extension UI message routing, active-tab injection, stored capture, config validation, backend proxy (auth header, JSON body, error mapping, /api-only), snapshot POST, permission failure, stale snapshot preservation, content-page sender rejection, toolbar opens dashboard.');
})().catch(e=>{console.error(e);process.exitCode=1});
