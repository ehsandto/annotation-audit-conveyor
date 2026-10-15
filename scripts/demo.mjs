import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {digest,sha} from './check.mjs';
try{
 const [mode,address,commit]=process.argv.slice(2);
 if(!['start','skip','first','replay','second','terminal'].includes(mode)||!/^0x[0-9a-fA-F]{40}$/.test(address??'')||! /^[0-9a-f]{40}$/.test(commit??''))throw Error('Demo context');
 const run=digest({contract:address,creator:'0x7a413BB4AB62E31d62d4cD9efC8C8a8Dae37FB42',nonce:'demo-audit'});
 const args=mode==='start'?['start_run',['demo-audit','ehsandto','annotation-audit-conveyor',commit,'examples/dataset.json',sha(fs.readFileSync('examples/dataset.json'))]]:
  ['audit_next',[run,mode==='skip'||mode==='second'?2:mode==='terminal'?4:0]];
 console.log(JSON.stringify({mode,run_id:run}));
 const r=spawnSync(process.execPath,['scripts/run-cli.cjs','write',address,args[0],'--args',...args[1].map(String)],{windowsHide:true,stdio:'inherit'});
 process.exitCode=r.status??1;
}catch{console.error('Sanitized demo failure; inspect history before resending');process.exitCode=1;}
