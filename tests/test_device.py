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
    assert 'About' in sim.info()['title']
    assert all(x['title']!='about' for x in sim.info()['library'])
