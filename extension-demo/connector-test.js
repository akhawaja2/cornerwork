document.querySelector('#test').onclick=()=>{
try{
 const doc=document.querySelector('#fixture').contentDocument;
 const url='https://app.gymdesk.com/manager/members/attendance/id/12672454';
 const snapshot=readGymdeskAttendance(doc,url);
 if(snapshot.records.length!==1||snapshot.records[0].id!=='62252846')throw Error('Real DOM fixture did not parse.');
 let blocked=false;try{readGymdeskAttendance(doc,'https://example.com/')}catch{blocked=true;}
 if(!blocked)throw Error('Wrong origin was accepted.');
 CW.update('importGymdesk',{snapshot});
 document.querySelector('#result').textContent='PASS: actual Gymdesk DOM fixture parsed; wrong origin rejected; Sarah attendance imported into the local demo. Open coaching flow to test voice and replies.';
}catch(e){document.querySelector('#result').textContent='FAIL: '+e.message;}
};