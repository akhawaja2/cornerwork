(function(root){
const KEY='cornerwork-extension-fictional-v1';
function seed(){return {provider:'gymdesk',sites:{gymdesk:{attended:false,ping:false,logs:[]},mindbody:{attended:false,ping:false,logs:[]}}};}
function read(){try{return JSON.parse(localStorage.getItem(KEY))||seed()}catch{return seed()}}
function save(s){localStorage.setItem(KEY,JSON.stringify(s));return s}
function apply(s,action,payload={}){s=JSON.parse(JSON.stringify(s));const site=s.sites[s.provider];
if(action==='importGymdesk'){return importGymdesk(s,payload);}
if(action==='provider'){if(!['gymdesk','mindbody','gymdeskLive'].includes(payload.provider))throw Error('Unknown fixture');s.provider=payload.provider;if(!s.sites[s.provider])s.sites[s.provider]={attended:false,ping:false,logs:[]};}
else if(action==='attend'){if(s.provider==='gymdeskLive')throw Error('Read attendance from Gymdesk instead.');site.attended=true;}
else if(action==='ping'){if(s.provider==='gymdeskLive')throw Error('The local prompt unlocks after the imported session ends.');if(!site.attended)throw Error('Check in the fictional member first.');site.ping=true;}
else if(action==='note'){if(!site.ping)throw Error('Run the post-class ping first.');const body=(payload.body||'').trim();const audio=payload.audio||'';if(audio && (!/^data:audio\/(webm|ogg|mp4|mpeg|wav|x-wav)(;codecs=[^;,]+)?;base64,[A-Za-z0-9+/=]+$/.test(audio)||audio.length>1100000))throw Error('Use a supported audio clip smaller than 800 KB.');if(!body&&!audio)throw Error('Record a voice note or enter a message.');if(body.length>2000)throw Error('Keep the transcript under 2,000 characters.');site.logs.push({attendanceId:site.currentAttendance?.id||null,attendanceTitle:site.currentAttendance?.title||'',id:site.logs.length+1,body,audio,reply:'',at:new Date().toISOString()});}
else if(action==='reply'){const log=site.logs.find(x=>x.id===payload.id);if(!log)throw Error('Message not found.');if(log.reply)throw Error('Already replied.');const body=(payload.body||'').trim();if(!body)throw Error('Enter a reply.');if(body.length>2000)throw Error('Keep replies under 2,000 characters.');log.reply=body;}
else if(action==='reset')s.sites[s.provider]={attended:false,ping:false,logs:[]};
else throw Error('Unknown action');return s;}
function update(action,payload){return save(apply(read(),action,payload))}
function name(provider){return provider==='gymdeskLive'?'Gymdesk attendance import':provider==='mindbody'?'Mindbody':'Gymdesk'}
function importGymdesk(s,payload){
const {snapshot,now=Date.now()}=payload;
if(!snapshot||snapshot.memberId!=='12672454'||snapshot.memberName!=='Sarah Demo'||snapshot.gym!=='AKLabs MMA'||!Array.isArray(snapshot.records))throw Error('Unexpected Gymdesk source.');
const records=snapshot.records.map(r=>{
const date=/^(\d{2})\/(\d{2})\/(\d{4})$/.exec(r.date||'');
const time=/ (\d{1,2}):(\d{2}) (AM|PM)$/.exec(r.when||'');
const duration=/^(?:(\d+(?:\.\d+)?)h)?\s*(?:(\d+)m)?$/.exec(r.duration||'');
if(!date||!time||!duration||(!duration[1]&&!duration[2])||!/^\d+$/.test(r.id)||!/^\d+$/.test(r.sessionId)||!r.title)throw Error('Unsupported Gymdesk attendance format.');
const hour=Number(time[1])%12+(time[3]==='PM'?12:0);
const start=new Date(+date[3],+date[1]-1,+date[2],hour,+time[2]).getTime();
const parsed=new Date(start);
if(+time[1]<1||+time[1]>12||+time[2]>59||parsed.getFullYear()!==+date[3]||parsed.getMonth()!==+date[1]-1||parsed.getDate()!==+date[2])throw Error('Invalid class date.');
const minutes=Number(duration[1]||0)*60+Number(duration[2]||0);
if(!Number.isFinite(start)||minutes<=0||minutes>1440)throw Error('Invalid class time.');
return {...r,end:start+minutes*60000,start};
});
const x=s.sites.gymdeskLive||{attended:false,ping:false,logs:[]};
const ended=records.filter(r=>r.end<=now).sort((a,b)=>b.end-a.end);
x.attended=records.some(r=>r.start<=now);x.ping=ended.length>0;
x.currentAttendance=ended[0]||null;x.source=snapshot;
x.pingIds=[...new Set([...(x.pingIds||[]),...ended.map(r=>r.id)])];
s.sites.gymdeskLive=x;s.provider='gymdeskLive';return s;
}
root.CW={KEY,seed,read,save,apply,update,name};
if(typeof module!=='undefined')module.exports=root.CW;
})(globalThis);