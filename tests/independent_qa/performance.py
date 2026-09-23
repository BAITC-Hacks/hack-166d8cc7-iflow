"""Independent sequential public API wall-clock timings, isolated state."""
import argparse,json,statistics,math,tempfile,time
from pathlib import Path
import run_audit as a
def run(live=False):
    a.registry.clear();a.timings['live_ai'].clear()
    main=json.loads((a.OUT/'evidence.json').read_text());sup=json.loads((a.OUT/'supplement.json').read_text())
    if main['live_calls']+sup['live_calls']+3>40:raise RuntimeError('Global 40 call cap')
    s=a.Settings.from_env().model_copy(update={'notifications_worker_enabled':False,'ai_auto_prepare':False,'application_date':None})
    ai=a.CountingAI(a.create_recommender(s)) if live else a.AdversarialAI();result={'responses':{},'timings':[]}
    with tempfile.TemporaryDirectory(prefix='jury-api-perf-') as tmp:
        s=s.model_copy(update={'state_path':Path(tmp)/'state.json','dev_identities':{'audit-hr':a.Principal(role='hr')}})
        with a.TestClient(a.create_app(s,ai_client=ai),raise_server_exceptions=False) as c:
            token=next(t for t,p in s.dev_identities.items() if p.role=='hr');c.headers['Authorization']='Bearer '+token
            assert c.post('/api/dataset/import',files={'employees':('employees.json',json.dumps(a.payload)),'history':('history.csv',a.csvbytes(a.rows))}).status_code==200
            r=c.get('/api/hr/dashboard',headers={'Authorization':'Bearer demo-hr'})
            a.record('SEC08','Public demo HR credential does not grant privileged data',r.status_code in [401,403],'Public login/source credential demo-hr returned '+str(r.status_code)+'; UI exposes HR role button; documented local-demo limitation','MEDIUM')
            for n in ([5,12,24] if live else []):
                t=time.perf_counter();r=c.post(f'/api/employees/JQA{n:03}/recommendations');elapsed=time.perf_counter()-t;result['timings'].append(elapsed);result['responses'][str(n)]={'http':r.status_code,'body':r.json()}
                a.record('PERF'+str(n),'Fresh recommendation API response under 10 seconds',elapsed<10,f'{elapsed:.6f} seconds, HTTP {r.status_code}','HIGH')
    if live:ai.delegate.close()
    vals=result['timings'];result.update(live_calls=ai.calls if live else 0,live_errors=ai.errors if live else [],registry=a.registry)
    if vals:result['statistics']={'n':len(vals),'min':min(vals),'avg':statistics.mean(vals),'p95':sorted(vals)[math.ceil(.95*len(vals))-1],'max':max(vals)}
    (a.OUT/'performance_api.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');run(p.parse_args().live)
