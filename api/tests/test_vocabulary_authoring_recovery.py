"""Parser/static recovery retains0105 and every authored revision."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('authoring_deploy',ROOT/'scripts/deploy-finnaplan-v10-vocabulary-authoring.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
def test_authoring_recovery_refuses_drift_and_retains_shared_queue_and_word_history(tmp_path,monkeypatch):
    root,public,backup=[tmp_path/n for n in ('api','public','backup')]
    parser='app/services/content_studio.py';helper='app/services/curated_vocabulary.py';queue='app/services/review_queue.py';migration='migrations/0105_bank_vocabulary_scheduler.sql'
    for n in (parser,queue,migration):
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('prior '+n)
    prior={n:release.sha(root/n) for n in (parser,queue,migration)};prior[helper]=None
    saved=backup/'api'/parser;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_text('prior '+parser)
    (root/parser).write_text('candidate parser');(root/helper).write_text('candidate card helper')
    public.mkdir();(public/'index.html').write_text('prior web');(backup/'public').mkdir();(backup/'public/index.html').write_text('prior web');prior_web=release.inventory(public)
    (public/'index.html').write_text('candidate web');(public/'word.js').write_text('candidate chunk')
    history=root/'material-revisions';history.write_text('Every authored and reviewed word-card revision')
    scope={'prior_api':prior,'api':{n:release.sha(root/n) for n in (parser,helper)},'prior_web':prior_web,'served_web':release.inventory(public)}
    original=release.run;services=[]
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    (root/queue).write_text('later scheduler')
    with pytest.raises(AssertionError,match='drift'):release.restore_pair(backup,scope,root,public)
    (root/queue).write_text('prior '+queue);(public/'index.html').write_text('later web')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_pair(backup,scope,root,public)
    assert not services
    (public/'index.html').write_text('candidate web');release.restore_pair(backup,scope,root,public)
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    assert (root/parser).read_text()=='prior '+parser and not (root/helper).exists()
    assert release.sha(root/queue)==prior[queue] and release.sha(root/migration)==prior[migration]
    assert release.inventory(public)==prior_web and history.read_text()=='Every authored and reviewed word-card revision'
