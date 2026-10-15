import assert from 'node:assert/strict';
import {abi} from 'genlayer-js';
const h='a'.repeat(64);
for(const [method,args] of [['start_run',['n','ehsandto','annotation-audit-conveyor','a'.repeat(40),'examples/dataset.json',h]],
 ['audit_next',[h,0]],['get_run',[h]],['get_batch',[h,0]],['summary',[h,h]]]){
 const data=abi.calldata.encode(abi.calldata.makeCalldataObject(method,args,{}));
 assert.deepEqual(abi.calldata.encode(abi.calldata.decode(data)),data);
}
console.log('5 SDK calldata roundtrips passed');
