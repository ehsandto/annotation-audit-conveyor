import ast
import hashlib
import itertools
import json
import re
from pathlib import Path
from types import SimpleNamespace
import pytest

TREE=ast.parse(Path('contracts/AnnotationAuditConveyor.py').read_text())
NS={'hashlib':hashlib,'json':json,'re':re,'OBSERVATIONS':('SUPPORT','REFUTE','UNKNOWN')}
exec(compile(ast.Module(body=[n for n in TREE.body if isinstance(n,ast.FunctionDef)
    and n.name not in ('fail','fetch_source')],type_ignores=[]),'actual-helpers','exec'),NS)
DATA=Path('examples/dataset.json').read_bytes()
DOC=Path('examples/ingestion-reference.txt').read_bytes()


@pytest.fixture
def audit(direct_vm,direct_deploy,direct_alice):
    direct_vm.sender=direct_alice
    return direct_deploy('contracts/AnnotationAuditConveyor.py')


def start(audit,vm,nonce='demo',body=DATA,http=200,bad_hash=False):
    vm.clear_mocks()
    vm.mock_web(r'.*/dataset\.json',{'status':http,'body':body})
    return audit.start_run(nonce,'ehsandto','annotation-audit-conveyor','a'*40,'examples/dataset.json',
        'f'*64 if bad_hash else hashlib.sha256(body).hexdigest())


def step(audit,vm,rid,cursor,labels=None,http=200,body=DOC,raw=None):
    vm.clear_mocks()
    vm.mock_web(r'.*/ingestion-reference\.txt',{'status':http,'body':body})
    if raw is None:
        raw={'observations':[{'index':i,'label':v} for i,v in (labels or [])]}
    vm.mock_llm(r'(?s).*ANNOTATION AUDIT CONVEYOR.*',json.dumps(raw))
    audit.audit_next(rid,cursor)


def test_permissionless_full_coverage_and_exact_bounds(audit,direct_vm,direct_bob):
    rid=start(audit,direct_vm)
    run=audit.get_run(rid)
    assert run['frozen_root']==NS['digest']({'report':run['manifest_report'],'rows':run['rows']})
    summary=audit.summary(rid,run['head'])
    assert summary['error_lower']=={'numerator':0,'denominator':4}
    assert summary['error_upper']=={'numerator':4,'denominator':4}
    direct_vm.sender=direct_bob  # Creator has no veto over auditing.
    step(audit,direct_vm,rid,0,[(0,'REFUTE'),(1,'SUPPORT')])
    first=audit.get_batch(rid,0)
    assert first['outcomes']==['MISMATCH','MATCH']
    summary=audit.summary(rid,audit.get_run(rid)['head'])
    assert summary['pending']==2 and summary['error_lower']=={'numerator':1,'denominator':4}
    assert summary['error_upper']=={'numerator':3,'denominator':4}
    step(audit,direct_vm,rid,2,[(2,'SUPPORT')])
    run=audit.get_run(rid)
    assert run['status']=='COMPLETE' and run['cursor']==4
    assert run['counts']=={'MATCH':2,'MISMATCH':1,'UNRESOLVED':1}
    second=audit.get_batch(rid,2)
    assert second['report']['binding']['previous_head']==first['root']
    assert second['report']['entries'][1]['source']['status']=='HASH_MISMATCH'
    assert second['report']['entries'][1]['observation']=='UNKNOWN'
    summary=audit.summary(rid,run['head'])
    assert summary['error_lower']=={'numerator':1,'denominator':4}
    assert summary['error_upper']=={'numerator':2,'denominator':4}
    assert summary['document_consistency_only'] is True
    for batch in (first,second):
        b=dict(batch);root=b.pop('root');assert root==NS['digest'](b)
    assert audit.get_batch(rid,0)==first  # Immutable previous batch.
    with direct_vm.expect_revert('Audit run complete'):audit.audit_next(rid,4)


def test_no_skipping_replay_or_stale_head(audit,direct_vm):
    rid=start(audit,direct_vm)
    old=audit.get_run(rid)['head']
    with direct_vm.expect_revert('Audit cursor mismatch'):audit.audit_next(rid,2)
    step(audit,direct_vm,rid,0,[(0,'REFUTE'),(1,'SUPPORT')])
    with direct_vm.expect_revert('Audit cursor mismatch'):audit.audit_next(rid,0)
    with direct_vm.expect_revert('Audit head mismatch'):audit.summary(rid,old)
    with direct_vm.expect_revert('No recorded batch'):audit.get_batch(rid,1)
    with direct_vm.expect_revert('Run nonce used'):start(audit,direct_vm)


def test_cross_run_batches_cannot_be_reused(audit,direct_vm):
    one=start(audit,direct_vm,nonce='one')
    two=start(audit,direct_vm,nonce='two')
    step(audit,direct_vm,one,0,[(0,'REFUTE'),(1,'SUPPORT')])
    with direct_vm.expect_revert('No recorded batch'):audit.get_batch(two,0)
    assert audit.get_run(two)['cursor']==0


@pytest.mark.parametrize('kind',['http','encoding','oversize','hash'])
def test_bad_item_evidence_is_unresolved_not_correct(audit,direct_vm,kind):
    rid=start(audit,direct_vm)
    body=b'\xff' if kind=='encoding' else b'x'*4097 if kind=='oversize' else b'manipulated' if kind=='hash' else DOC
    step(audit,direct_vm,rid,0,http=503 if kind=='http' else 200,body=body)
    run=audit.get_run(rid)
    assert run['cursor']==2 and run['counts']=={'MATCH':0,'MISMATCH':0,'UNRESOLVED':2}
    assert audit.summary(rid,run['head'])['error_upper']['numerator']==4


@pytest.mark.parametrize('kind',['http','hash','schema','duplicate_id','duplicate_binding','bad_annotation','bad_source'])
def test_invalid_manifest_cannot_start(audit,direct_vm,kind):
    obj=json.loads(DATA)
    if kind=='schema':obj['schema']='wrong'
    if kind=='duplicate_id':obj['items'][1]['id']=obj['items'][0]['id']
    if kind=='duplicate_binding':
        obj['items'][1]=dict(obj['items'][0],id='DifferentID',annotation='REFUTE')
    if kind=='bad_annotation':obj['items'][0]['annotation']='CORRECT'
    if kind=='bad_source':obj['items'][0]['source']['path']='../private.txt'
    body=json.dumps(obj).encode()
    with direct_vm.expect_revert('Manifest acquisition or schema failed'):
        start(audit,direct_vm,body=body,http=503 if kind=='http' else 200,bad_hash=kind=='hash')


def test_failed_start_does_not_reserve_nonce(audit,direct_vm):
    with direct_vm.expect_revert('Manifest acquisition or schema failed'):start(audit,direct_vm,http=503)
    rid=start(audit,direct_vm)
    assert audit.get_run(rid)['cursor']==0


def test_last_odd_batch_has_exact_single_item_coverage(audit,direct_vm):
    obj=json.loads(DATA);obj['items']=obj['items'][:3]
    rid=start(audit,direct_vm,body=json.dumps(obj).encode())
    step(audit,direct_vm,rid,0,[(0,'REFUTE'),(1,'SUPPORT')])
    step(audit,direct_vm,rid,2,[(2,'SUPPORT')])
    run=audit.get_run(rid)
    assert run['cursor']==3 and run['status']=='COMPLETE'
    assert audit.summary(rid,run['head'])['counts']=={'MATCH':2,'MISMATCH':1,'UNRESOLVED':0}


@pytest.mark.parametrize('raw',[{}, {'observations':[]}, {'observations':[{'index':0,'label':'SUPPORT'}]},
    {'observations':[{'index':1,'label':'SUPPORT'},{'index':0,'label':'REFUTE'}]},
    {'observations':[{'index':False,'label':'SUPPORT'},{'index':1,'label':'SUPPORT'}]},
    {'observations':[{'index':0,'label':'YES'},{'index':1,'label':'SUPPORT'}]}])
def test_malformed_model_report_never_advances(audit,direct_vm,raw):
    rid=start(audit,direct_vm)
    with direct_vm.expect_revert('Invalid independent audit observations'):step(audit,direct_vm,rid,0,raw=raw)
    assert audit.get_run(rid)['cursor']==0


@pytest.mark.parametrize('field',['run','cursor','source','observation','entry_index'])
def test_post_consensus_substitutions_rejected(audit,direct_vm,monkeypatch,field):
    from genlayer import gl
    rid=start(audit,direct_vm)
    original=gl.vm.run_nondet_unsafe
    def forged(observe,validator):
        report=json.loads(json.dumps(original(observe,validator)))
        if field=='run':report['binding']['run']='other-run'
        elif field=='cursor':report['binding']['start']=False
        elif field=='source':report['entries'][0]['source']['body']='substitution'
        elif field=='observation':report['entries'][0]['observation']=False
        else:report['entries'][0]['index']=False
        return report
    monkeypatch.setattr(gl.vm,'run_nondet_unsafe',forged)
    with direct_vm.expect_revert('Invalid audit report'):step(audit,direct_vm,rid,0,[(0,'REFUTE'),(1,'SUPPORT')])
    assert audit.get_run(rid)['cursor']==0


def test_annotations_not_sent_to_semantic_judge():
    material=[{'index':0,'statement':'An independent statement','document':'Published source contents'}]
    prompt=NS['audit_prompt'](material)
    data=prompt.split('DATA=',1)[1]
    assert json.loads(data)==material and 'annotation' not in data


def test_exhaustive_bounds_and_conservation():
    cases=0
    for total in range(1,17):
        for cursor in range(total+1):
            for matches in range(cursor+1):
                for errors in range(cursor-matches+1):
                    unresolved=cursor-matches-errors
                    counts={'MATCH':matches,'MISMATCH':errors,'UNRESOLVED':unresolved}
                    result=NS['bounds'](total,cursor,counts)
                    lo,hi=result['error_lower']['numerator'],result['error_upper']['numerator']
                    assert 0<=lo<=hi<=total and hi==total-matches
                    assert lo==errors and result['pending']+sum(counts.values())==total
                    if cursor==total and unresolved==0:assert lo==hi
                    cases+=1
    assert cases==4844


@pytest.mark.parametrize('annotation,observation',list(itertools.product(('SUPPORT','REFUTE'),NS['OBSERVATIONS'])))
def test_exact_label_comparison(annotation,observation):
    expected='UNRESOLVED' if observation=='UNKNOWN' else 'MATCH' if annotation==observation else 'MISMATCH'
    assert NS['verdict'](annotation,observation)==expected


def test_actual_independent_validator_rejects_substantive_changes():
    cls=next(n for n in TREE.body if isinstance(n,ast.ClassDef))
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='audit_next')
    fn=next(n for n in method.body if isinstance(n,ast.FunctionDef) and n.name=='validator')
    class Return:
        def __init__(self,data):self.calldata=data
    expected={'binding':{'run':'r','start':0},'entries':[{'index':0,'observation':'REFUTE','source':{'body':'real'}}]}
    calls=[]
    def observe():calls.append(1);return expected
    ns=dict(NS,gl=SimpleNamespace(vm=SimpleNamespace(Return=Return)),observe=observe)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-validator','exec'),ns)
    assert ns['validator'](Return(expected)) and calls==[1]
    for change in [{'binding':{'run':'other','start':0}}, {'binding':{'run':'r','start':False}},
                   {'entries':[{'index':0,'observation':'SUPPORT','source':{'body':'real'}}]},
                   {'entries':[{'index':0,'observation':'REFUTE','source':{'body':'fake'}}]}]:
        assert not ns['validator'](Return(dict(expected,**change)))
    assert not ns['validator'](object())


def test_failed_evidence_cannot_be_promoted_after_consensus(audit,direct_vm,monkeypatch):
    from genlayer import gl
    rid=start(audit,direct_vm)
    step(audit,direct_vm,rid,0,[(0,'REFUTE'),(1,'SUPPORT')])
    original=gl.vm.run_nondet_unsafe
    def forged(observe,validator):
        report=json.loads(json.dumps(original(observe,validator)))
        report['entries'][1]['observation']='REFUTE'  # Would match A4, but its hash failed.
        return report
    monkeypatch.setattr(gl.vm,'run_nondet_unsafe',forged)
    with direct_vm.expect_revert('Invalid audit report'):step(audit,direct_vm,rid,2,[(2,'SUPPORT')])
    assert audit.get_run(rid)['cursor']==2


def test_maximum_dataset_all_unavailable_never_claims_quality(audit,direct_vm):
    obj=json.loads(DATA)
    obj['items']=[dict(obj['items'][0],id='item'+str(i),statement='A distinct hypothetical statement number '+str(i)+'.') for i in range(16)]
    rid=start(audit,direct_vm,body=json.dumps(obj).encode())
    for cursor in range(0,16,2):step(audit,direct_vm,rid,cursor,http=503)
    run=audit.get_run(rid)
    assert run['status']=='COMPLETE' and run['counts']=={'MATCH':0,'MISMATCH':0,'UNRESOLVED':16}
    summary=audit.summary(rid,run['head'])
    assert summary['error_lower']=={'numerator':0,'denominator':16}
    assert summary['error_upper']=={'numerator':16,'denominator':16}
