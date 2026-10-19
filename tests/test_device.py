from pathlib import Path
import pytest
from reader.web import Simulator
from reader.security import Security
from reader.documents import identity

@pytest.fixture
def sim(tmp_path):
    return Simulator([Path('fixtures/formatting.md')],tmp_path/'state')

def setup_codes(sim):
    sim.action({'action':'set_code','kind':'unlock','code':'UUDDLRLR'})
    sim.action({'action':'set_code','kind':'duress','code':'DDUURLRL'})

def enter(sim,code):
    for arrow in code: result=sim.action({'action':'arrow','arrow':arrow})
    return result

def test_lock_blocks_api_and_persists(sim):
    setup_codes(sim); sim.action({'action':'lock'})
    assert sim.info()['library']==[]
    for action in ('next','open','about','mark','import_state','set_code'):
        with pytest.raises(PermissionError):sim.action({'action':action})
    again=Simulator(sim.paths,sim.store.root)
    assert again.info()['security']['locked']
    assert enter(again,'RRRRRRRR')['security']['locked']
    assert not enter(again,'UUDDLRLR')['security']['locked']

def test_duress_no_confirmation_safe_reset(sim):
    paths=list(sim.paths);before=[p.read_bytes() for p in paths]
    setup_codes(sim);sim.action({'action':'mark','name':'private'})
    sim.action({'action':'lock'}); result=enter(sim,'DDUURLRL')
    assert result['security']=={'locked':False,'unlock_set':False,'duress_set':False,'purged':True,'code_length':0}
    assert result['library']==[] and sim.store.data['books']=={}
    assert all(p.read_bytes()==b for p,b in zip(paths,before))
    again=Simulator(paths,sim.store.root)
    assert again.info()['library']==[]
    again.action({'action':'reset_simulator'})
    assert len(again.info()['library'])==1 and not again.info()['security']['purged']
    assert not again.info()['bookmarks']

def test_codes_cannot_overlap_or_unlock_early(sim):
    with pytest.raises(ValueError):sim.action({'action':'set_code','kind':'duress','code':'UUUU'})
    setup_codes(sim)
    for code in ('UUDDLRLR','UUUU','X'*8):
        with pytest.raises(ValueError):sim.action({'action':'set_code','kind':'duress','code':code})

def test_completion_sticky_and_about(sim):
    sim.current.turn(9999)
    assert sim.info()['read'] and sim.info()['progress']==100
    sim.current.turn(-9999)
    assert sim.info()['read'] and sim.info()['progress']==0
    sim.action({'action':'read_status','read':False})
    assert not sim.info()['read']
    sim.action({'action':'about'})
    assert 'file_id.diz' in sim.info()['title']
    assert all(x['title']!='about' for x in sim.info()['library'])


def test_salted_verifiers_and_legacy_migration(tmp_path):
    import json
    from reader.security import matches, ITERATIONS
    code='UUDDLRLR'
    legacy={'unlock':code,'duress':'DDUURLRL','locked':True,'purged':False}
    path=tmp_path/'device.json';path.write_text(json.dumps(legacy))
    s=Security(tmp_path)
    stored=json.loads(path.read_text())
    assert code not in path.read_text() and legacy['duress'] not in path.read_text()
    assert stored['unlock']['iterations']==ITERATIONS
    assert matches(stored['unlock'],code) and not matches(stored['unlock'],'R'*8)
    assert s.public()['locked'] and s.public()['code_length']==8
    for arrow in code:result=s.arrow(arrow)
    assert result=='unlock'
    other=tmp_path/'other';other.mkdir();second=Security(other);second.configure('unlock',code)
    assert second.data['unlock']['salt']!=stored['unlock']['salt']
    assert second.data['unlock']['hash']!=stored['unlock']['hash']
    assert Security(tmp_path).data==stored


def test_verifier_corruption_fails_closed(tmp_path):
    import json
    s=Security(tmp_path);s.configure('unlock','UUDD')
    for field,value in [('version',9),('iterations',1),('length',0),('salt','bad'),('hash','0'*63)]:
        bad=json.loads(json.dumps(s.data));bad['unlock'][field]=value
        (tmp_path/'device.json').write_text(json.dumps(bad))
        with pytest.raises(ValueError):Security(tmp_path)


def test_pbkdf2_known_answer_and_failed_save(tmp_path,monkeypatch):
    from reader.security import matches
    # Independent reference generated with OpenSSL-compatible PBKDF2-HMAC-SHA256.
    r={'version':2,'iterations':100000,'length':4,'salt':'00'*16,
       'hash':'cd58ec3de8ebd51869c32c2defa1027e47f78c953015fb2f3d807dc3bca795f4'}
    assert matches(r,'UUDD') and not matches(r,'DDUU')
    s=Security(tmp_path);s.configure('unlock','UUDD');before=s.path.read_bytes();record=s.data['unlock']
    def fail():raise OSError('simulated disk full')
    monkeypatch.setattr(s,'save',fail)
    with pytest.raises(OSError):s.configure('unlock','DDUU')
    assert s.data['unlock']==record and s.path.read_bytes()==before
