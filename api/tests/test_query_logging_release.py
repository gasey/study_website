"""Only scoped settings may change; probes must prove duration and redaction."""
import importlib.util,json,re
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('query_logging_release',ROOT/'scripts/deploy-finnaplan-v12-query-logging.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_target_filter_preserves_unrelated_keys_and_comments():
    original="# existing configuration\nshared_buffers = '128MB'\nlog_min_duration_statement_other = 'protected'\n"
    changed=original+"log_min_duration_statement = '1000'\nlog_parameter_max_length = '0'\nlog_parameter_max_length_on_error = '0'\n"
    assert release.untargeted(original)==release.untargeted(changed)
    assert release.untargeted(changed.replace('128MB','256MB'))!=release.untargeted(original)


def test_recovery_refuses_drift_then_resets_only_scoped_keys(tmp_path,monkeypatch):
    config=tmp_path/'postgresql.auto.conf';original="# retained configuration\nshared_buffers = '128MB'\n"
    config.write_text(original);old_hash=release.sha(config)
    for key,value in release.SETTINGS.items():config.write_text(config.read_text()+key+" = '"+value+"'\n")
    expected=release.sha(config);calls=[]
    before=[{'name':k,'setting':'-1' if k!='log_parameter_max_length_on_error' else '0'} for k in release.SETTINGS]
    scope={'before':{'auto_conf_path':str(config),'auto_conf_sha256':old_hash,'settings':before}}
    def pg(query):
        calls.append(query)
        if query.startswith('ALTER SYSTEM RESET '):
            key=query.removeprefix('ALTER SYSTEM RESET ').rstrip(';')
            config.write_text(''.join(line for line in config.read_text().splitlines(keepends=True) if not line.startswith(key+' =')))
        return 't'
    monkeypatch.setattr(release,'pg',pg)
    monkeypatch.setattr(release,'wait_settings',lambda expected:{k:{'source':'default','sourcefile':None} for k in expected})
    config.write_text(config.read_text()+"work_mem = '16MB'\n")
    with pytest.raises(AssertionError,match='drift'):release.reset_keys(scope,expected)
    assert calls==[]
    config.write_text(config.read_text().replace("work_mem = '16MB'\n",''));release.reset_keys(scope,expected)
    assert config.read_text()==original
    assert calls==['ALTER SYSTEM RESET '+k+';' for k in reversed(release.SETTINGS)]+['SELECT pg_reload_conf()']


@pytest.mark.parametrize('leak,duration,accepted',[(False,1101.5,True),(True,1101.5,False),(False,10.0,False)])
def test_log_probe_requires_own_slow_statement_and_suppressed_bind(tmp_path,monkeypatch,leak,duration,accepted):
    log=tmp_path/'postgresql.log';log.write_text('existing private statements are not exported\n');log.chmod(0o640)
    scope={'before':{'logs':[{'path':str(log)}]}}
    def run(args,**kwargs):
        data=json.loads(kwargs['input'])
        with log.open('a') as out:
            out.write('duration: '+str(duration)+' ms execute <unnamed>: SELECT $1,pg_sleep(1.1) /* '+data['marker']+' */\n')
            if leak:out.write('DETAIL: parameters: $1 = '+data['canary']+'\n')
        return 'read-only application-role probe passed'
    monkeypatch.setattr(release,'run',run)
    if accepted:
        result=release.verify_probe(scope)
        assert result['bind_canary_absent'] and result['observed_probe_ms']==duration
        assert not result['raw_queries_or_bind_values_exported']
    else:
        with pytest.raises(AssertionError):release.verify_probe(scope)
