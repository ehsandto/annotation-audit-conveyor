// One documented write at a time. Unknown broadcasts never trigger automatic resend.
import fs from 'node:fs';
import {spawn} from 'node:child_process';
import {rpc} from './check.mjs';
const address='0xeACeD0F3067c02c545913c4658F61910544485B8',commit='da2e2739acaa3428c80314dc4e55950df4879db7';
const seed=[
 {step:'deploy',hash:'0xd6b5fbcd71c4406295dae9791a5339be34d494dc61929a364652d8c512769a94',status:'FINALIZED',execution:'SUCCESS',consensus:'MAJORITY_AGREE'},
 {step:'start',hash:'0xd7cb911dee6a38ba90c409ba43c9aa1c3fd92be4beeec436b795cecb773f7c43'}
];
const steps=['deploy','start','skip','first','replay','second','terminal'];
let ledger=fs.existsSync('PROOFS.json')?JSON.parse(fs.readFileSync('PROOFS.json','utf8')):{address,manifest_commit:commit,transactions:seed};
if(ledger.address!==address||ledger.manifest_commit!==commit)throw Error('Proof context mismatch');
const save=()=>fs.writeFileSync('PROOFS.json',JSON.stringify(ledger,null,2)+'\n');
function launch(step){return new Promise((resolve,reject)=>{
 const entry={step,status:'BROADCAST_UNKNOWN'};ledger.transactions.push(entry);save();
 const child=spawn(process.execPath,['--dns-result-order=ipv4first','scripts/demo.mjs',step,address,commit],{windowsHide:true,stdio:['ignore','pipe','pipe']});
 let carry='',known;
 child.stdout.on('data',chunk=>{
  carry+=chunk.toString();const lines=carry.split(/\r?\n/);carry=lines.pop();
  for(const line of lines){const m=line.match(/^BROADCAST_HASH (0x[0-9a-fA-F]{64})$/);
   if(m){if(known&&known!==m[1]){child.kill();reject(Error('Multiple hashes'));return;}
    known=m[1];Object.assign(entry,{hash:known,status:'SUBMITTED'});save();console.log(JSON.stringify({step,broadcast:known}));}
  }
 });
 child.stderr.resume();
 const timer=setTimeout(()=>{child.kill();reject(Error('Child timeout; inspect history'));},150000);
 child.on('error',()=>{clearTimeout(timer);reject(Error('Launch failure'));});
 child.on('close',()=>{clearTimeout(timer);if(!known)reject(Error('Uncertain broadcast; inspect sender history'));else resolve();});
});}
async function verify(entry){
 for(let i=0;i<30;i++){
  const tx=await rpc('eth_getTransactionByHash',[entry.hash]);
  if(tx.status==='FINALIZED'){
   const leader=tx.consensus_data?.leader_receipt?.find(x=>x.mode==='leader');
   const expected=['skip','replay'].includes(entry.step)?'Audit cursor mismatch':entry.step==='terminal'?'Audit run complete':null;
   const raw=leader?.genvm_result?.stderr||leader?.result;
   const decoded=typeof raw==='string'?(/^[A-Za-z0-9+/]*={0,2}$/.test(raw)&&raw.length%4===0?Buffer.from(raw,'base64').toString('utf8'):raw):'';
   if(leader?.execution_result!==(expected?'ERROR':'SUCCESS')||tx.result_name!=='MAJORITY_AGREE'||(expected&&!decoded.includes(expected)))throw Error('Unexpected execution');
   Object.assign(entry,{status:tx.status,execution:leader.execution_result,consensus:tx.result_name,...(expected?{expected_error:expected}:{})});save();console.log(JSON.stringify(entry));return;
  }
  await new Promise(r=>setTimeout(r,4000));
 }
 throw Error('Finalization pending; resume saved hash only');
}
let current;
try{
 save();
 for(const step of steps){
  current=step;let entry=ledger.transactions.find(x=>x.step===step);
  if(!entry){await launch(step);entry=ledger.transactions.find(x=>x.step===step);}
  if(!entry.hash)throw Error('Uncertain broadcast needs manual history check');
  if(entry.status==='FINALIZED'&&entry.execution)continue;
  await verify(entry);
 }
 console.log('All documented transactions finalized with expected execution outcomes.');
}catch{
 console.error(JSON.stringify({stopped_at:current,message:'Stopped safely. Inspect saved receipt/history. No automatic rebroadcast.'}));
 process.exitCode=1;
}
