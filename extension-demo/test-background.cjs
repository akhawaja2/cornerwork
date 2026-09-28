const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const events={},stored={},calls=[];
const snapshot={memberId:'12672454',memberName:'Sarah Demo',gym:'AKLabs MMA',records:[{id:'62252846',sessionId:'1832536',title:'Boxing',date:'09/28/2026',when:'Sep 28, 2026 7:00 AM',duration:'1h'}]};
let fail=false;
const context={console,CW:require('./core.js'),importScripts:()=>{},readGymdeskAttendance:()=>{},chrome:{
 runtime:{id:'test',onInstalled:{addListener:fn=>events.install=fn},onMessage:{addListener:fn=>events.message=fn}},
 sidePanel:{setPanelBehavior:async x=>calls.push(x),open:async x=>calls.push(x)},
 action:{onClicked:{addListener:fn=>events.click=fn}},
 tabs:{query:async()=>[{id:7,url:'https://app.gymdesk.com/manager/members/attendance/id/12672454'}]},
 scripting:{executeScript:async x=>{calls.push(x);if(fail)throw Error('Cannot access contents of the page');return [{result:snapshot}];}},
 storage:{local:{get:async()=>stored,set:async x=>Object.assign(stored,x)}}
}};
vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/background.js','utf8'),context);
(async()=>{
 const response=await new Promise(resolve=>{assert.equal(events.message({type:'readGymdesk'},{id:'test',url:'chrome-extension://test/index.html'},resolve),true)});
 assert.equal(response.ok,true);assert.equal(stored.gymdeskSnapshot,snapshot);assert.equal(calls[0].target.tabId,7);
 stored.coachingState=require('./core.js').apply(stored.coachingState,'note',{body:'Embedded reply test'});
 const reply=await new Promise(resolve=>events.message({type:'coachReply',id:1,body:'Review before class'},{id:'test',url:'chrome-extension://test/embedded.html'},resolve));
 assert.equal(reply.ok,true);assert.equal(stored.coachingState.sites.gymdeskLive.logs[0].reply,'Review before class');
 const duplicate=await new Promise(resolve=>events.message({type:'coachReply',id:1,body:'Duplicate'},{id:'test',url:'chrome-extension://test/embedded.html'},resolve));
 assert.equal(duplicate.ok,false);
 const read=await new Promise(resolve=>events.message({type:'coachState'},{id:'test',url:'chrome-extension://test/embedded.html'},resolve));
 assert.equal(read.state.sites.gymdeskLive.logs[0].body,'Embedded reply test');
 fail=true;
 const failure=await new Promise(resolve=>events.message({type:'readGymdesk'},{id:'test',url:'chrome-extension://test/panel.html'},resolve));
 assert.equal(failure.ok,false);assert.match(failure.error,/toolbar/);assert.equal(stored.gymdeskSnapshot,snapshot);
 assert.equal(events.message({type:'readGymdesk'},{id:'test',url:'https://app.gymdesk.com'},()=>{throw Error('untrusted sender')}),undefined);
 console.log('PASS: extension UI message routing, active-tab injection, stored capture, permission failure, stale snapshot preservation, content-page sender rejection.');
})().catch(e=>{console.error(e);process.exitCode=1});
