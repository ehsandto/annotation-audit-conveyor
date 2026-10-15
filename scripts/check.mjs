import fs from 'node:fs';
import crypto from 'node:crypto';
import {createClient} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
export const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x).replace(/[\u007f-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0')):
 Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>canonical(k)+':'+canonical(x[k])).join(',')+'}';
export const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
export const digest=x=>sha(canonical(x));
export async function rpc(method,params){
 const r=await fetch('https://studio.genlayer.com/api',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method,params}),signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw Error('HTTP failure');const p=await r.json();if(p.error||p.result==null)throw Error('RPC failure');return p.result;
}
export const client=createClient({chain:studionet});
export const read=(address,functionName,args)=>client.readContract({address,functionName,args});
if(process.argv[1]?.endsWith('check.mjs'))try{
 const [mode,value,extra]=process.argv.slice(2);
 if(mode==='source'){
  const norm=x=>x.replace(/\r\n/g,'\n').trimEnd()+'\n';
  const actual=norm(Buffer.from(await rpc('gen_getContractCode',[value]),'base64').toString('utf8'));
  const local=norm(fs.readFileSync('contracts/AnnotationAuditConveyor.py','utf8'));
  console.log(JSON.stringify({address:value,source_matches:actual===local,source_sha256:sha(actual)}));if(actual!==local)process.exitCode=1;
 }else if(['success','error'].includes(mode)){
  let tx=await rpc('eth_getTransactionByHash',[value]);
  for(let i=0;tx.status!=='FINALIZED'&&i<15;i++){await new Promise(r=>setTimeout(r,2000));tx=await rpc('eth_getTransactionByHash',[value]);}
  const leader=tx.consensus_data?.leader_receipt?.find(x=>x.mode==='leader'),raw=leader?.genvm_result?.stderr||leader?.result;
  const decoded=typeof raw!=='string'?'':(/^[A-Za-z0-9+/]*={0,2}$/.test(raw)&&raw.length%4===0?Buffer.from(raw,'base64').toString('utf8'):raw);
  console.log(JSON.stringify({hash:value,address:tx.to_address??tx.to,status:tx.status,execution:leader?.execution_result,consensus:tx.result_name,...(extra?{expected_error_matched:decoded.includes(extra)}:{})}));
  if(tx.status!=='FINALIZED'||leader?.execution_result!==(mode==='error'?'ERROR':'SUCCESS')||tx.result_name!=='MAJORITY_AGREE'||(extra&&!decoded.includes(extra)))process.exitCode=1;
 }else if(mode==='state'){
  const run=await read(value,'get_run',[extra]),manifest=run.manifest_report,spec=manifest.binding.manifest,source=manifest.source;
  if(manifest.binding.run!==extra||manifest.binding.contract!==value||source.url!==spec.url||source.http!==200||source.status!=='OK'||sha(source.body)!==source.hash||source.hash!==spec.sha256)throw Error('Manifest binding/integrity');
  const rows=JSON.parse(source.body).items.map(item=>({id:item.id,statement:item.statement,annotation:item.annotation,
   source:{url:'https://raw.githubusercontent.com/'+item.source.owner+'/'+item.source.repo+'/'+item.source.commit+'/'+item.source.path,sha256:item.source.sha256}}));
  if(canonical(rows)!==canonical(run.rows)||digest({report:manifest,rows})!==run.frozen_root)throw Error('Frozen dataset root');
  let head=run.frozen_root,cursor=0,counts={MATCH:0,MISMATCH:0,UNRESOLVED:0};const batches=[];
  while(cursor<run.cursor){
   const b=await read(value,'get_batch',[extra,cursor]),{root,...body}=b,stop=Math.min(cursor+2,rows.length),binding=b.report.binding;
   if(digest(body)!==root||binding.run!==extra||binding.frozen_root!==run.frozen_root||binding.previous_head!==head||binding.start!==cursor||binding.stop!==stop||canonical(binding.counts_before)!==canonical(counts)||b.report.entries.length!==stop-cursor)throw Error('Batch chain/binding');
   const outcomes=[];
   for(let i=cursor;i<stop;i++){
    const e=b.report.entries[i-cursor],row=rows[i],s=e.source;
    if(e.index!==i||e.id!==row.id||s.url!==row.source.url||!['SUPPORT','REFUTE','UNKNOWN'].includes(e.observation)||(s.body&&sha(s.body)!==s.hash))throw Error('Entry binding');
    if(s.status==='OK'&&(s.http!==200||s.hash!==row.source.sha256))throw Error('Source commitment');
    if(s.status!=='OK'&&e.observation!=='UNKNOWN')throw Error('Bad source approved');
    const outcome=e.observation==='UNKNOWN'?'UNRESOLVED':e.observation===row.annotation?'MATCH':'MISMATCH';
    outcomes.push(outcome);counts[outcome]++;
   }
   if(canonical(outcomes)!==canonical(b.outcomes)||canonical(counts)!==canonical(b.counts_after))throw Error('Outcome conservation');
   batches.push({start:cursor,root,outcomes,observations:b.report.entries.map(e=>e.observation),source_statuses:b.report.entries.map(e=>e.source.status)});
   cursor=stop;head=root;
  }
  if(cursor!==run.cursor||head!==run.head||canonical(counts)!==canonical(run.counts)||run.status!==(cursor===rows.length?'COMPLETE':'OPEN'))throw Error('Final coverage mismatch');
  const summary=await read(value,'summary',[extra,head]),pending=rows.length-cursor;
  if(summary.total!==rows.length||summary.audited!==cursor||summary.pending!==pending||summary.head!==head||!summary.document_consistency_only||canonical(summary.counts)!==canonical(counts)||summary.error_lower.numerator!==counts.MISMATCH||summary.error_upper.numerator!==counts.MISMATCH+counts.UNRESOLVED+pending||summary.error_lower.denominator!==rows.length||summary.error_upper.denominator!==rows.length)throw Error('Coverage bounds mismatch');
  console.log(JSON.stringify({run:extra,frozen_root:run.frozen_root,head,verified:true,summary,batches}));
 }else throw Error('Unknown check mode');
}catch{console.error('Sanitized verification failure; inspect history before rebroadcast');process.exitCode=1;}
