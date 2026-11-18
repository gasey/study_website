"""Bounded API/static recovery removes the new reader and preserves all history."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('vocabulary_release',ROOT/'scripts/deploy-finnaplan-v10-vocabulary.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
def test_vocabulary_recovery_refuses_drift_and_preserves_history(tmp_path,monkeypatch):
    root,public,backup=[tmp_path/n for n in ('api','public','backup')]
    router='app/routers/vocabulary.py';helper='app/services/vocabulary_decks.py';unchanged='app/services/games.py'
    for n in (router,unchanged):
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('prior '+n)
    prior={n:release.sha(root/n) for n in (router,unchanged)};prior[helper]=None
    saved=backup/'api'/router;saved.parent.mkdir(parents=True);saved.write_text('prior '+router)
    (root/router).write_text('released router');(root/helper).write_text('released helper')
    public.mkdir();(public/'index.html').write_text('prior web');(backup/'public').mkdir();(backup/'public/index.html').write_text('prior web')
    prior_web=release.inventory(public);(public/'index.html').write_text('released web');(public/'tracker.js').write_text('released tracker')
    history=root/'learner-history';history.write_text('All learner, tier and review history')
    scope={'prior_api':prior,'api':{n:release.sha(root/n) for n in (router,helper)},'prior_web':prior_web,'served_web':release.inventory(public)}
    original=release.run;services=[]
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    (root/unchanged).write_text('later games writer')
    with pytest.raises(AssertionError,match='drift'):release.restore_pair(backup,scope,root,public)
    (root/unchanged).write_text('prior '+unchanged);(public/'index.html').write_text('later web')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_pair(backup,scope,root,public)
    assert not services
    (public/'index.html').write_text('released web');release.restore_pair(backup,scope,root,public)
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    assert (root/router).read_text()=='prior '+router and not (root/helper).exists()
    assert release.inventory(public)==prior_web and history.read_text()=='All learner, tier and review history'
