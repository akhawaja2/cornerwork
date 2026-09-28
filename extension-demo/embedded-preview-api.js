window.chrome={runtime:{sendMessage:async m=>{
if(m.type==='coachState')return {ok:true,state:CW.read()};
if(m.type==='coachReply'){try{const state=CW.read();const provider=state.provider;state.provider='gymdeskLive';const next=CW.apply(state,'reply',m);next.provider=provider;CW.save(next);return {ok:true};}catch(e){return {ok:false,error:e.message}}}
return {ok:false,error:'Preview only. Import attendance in the installed extension.'};
}},storage:{onChanged:{addListener:fn=>window.addEventListener('storage',()=>fn({coachingState:true},'local'))}}};
