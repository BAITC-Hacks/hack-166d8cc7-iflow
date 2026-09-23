"""Additional independent boundary checks; consumes two real LLM calls only with --live."""
import argparse, copy, json, shutil, tempfile, time, uuid
from pathlib import Path
import run_audit as a

def run(live=False):
    saved=json.loads((a.OUT/'evidence.json').read_text(encoding='utf-8'))
    a.registry.clear();a.timings['live_ai'].clear()
    settings=a.Settings.from_env().model_copy(update={'notifications_worker_enabled':False,'ai_auto_prepare':False,'application_date':None})
    counter=a.CountingAI(a.create_recommender(settings)) if live else None
    if saved['live_calls']+2>40:raise RuntimeError('Total live-call budget exceeded')
    supplement={}
    with tempfile.TemporaryDirectory(prefix='jury-variants-') as tmp:
      root=Path(tmp)
      identities={'jury-hr':a.Principal(role='hr'),'JQA004':a.Principal(role='employee',employee_id='JQA004')}
      def app(variant,alter):
        dest=root/variant;shutil.copytree(a.raw,dest)
        alter(dest)
        return a.create_app(settings.model_copy(update={'raw_dir':dest,'state_path':root/(variant+'.json'),'dev_identities':identities}),ai_client=counter or a.AdversarialAI())
      def change_events(dest,kind):
        data=json.loads((dest/'events.json').read_text(encoding='utf-8'))
        for e in data['events']:
            if e['event_id']=='EV_006':
                if kind=='mandatory':e['mandatory']=True
                else:e['upcoming_sessions']=[]
        (dest/'events.json').write_text(json.dumps(data),encoding='utf-8')
      for variant in ['mandatory','no_sessions']:
        with a.TestClient(app(variant,lambda d:change_events(d,variant))) as c:
            c.headers['Authorization']='Bearer jury-hr'
            r=c.post('/api/dataset/import',files={'employees':('employees.json',json.dumps(a.payload)),'history':('history.csv',a.csvbytes(a.rows))})
            assert r.status_code==200,r.text
            result=c.get('/api/employees/JQA005/recommendations/context').json()
            supplement[variant]=result['excluded_events']
            actual=next(e['reasons'] for e in result['excluded_events'] if e['event_id']=='EV_006')
            a.record('Z01' if variant=='mandatory' else 'Z02','Attractive activity excluded when '+variant,('mandatory' if variant=='mandatory' else 'unavailable') in actual,str(actual),'HIGH')
      def flags(dest,flip):
        data=json.loads((dest/'skills.json').read_text(encoding='utf-8'))
        if flip:
            for p in data['role_profiles']:
                if p['role']=='Backend Engineer' and p['grade']=='Senior':p['critical_skills']=['SK_PUBLIC_SPEAKING','SK_API_DESIGN']
        (dest/'skills.json').write_text(json.dumps(data),encoding='utf-8')
      for flip in [False,True]:
        variant='critical_'+str(flip)
        with a.TestClient(app(variant,lambda d:flags(d,flip)),raise_server_exceptions=False) as c:
            c.headers['Authorization']='Bearer jury-hr'
            assert c.post('/api/dataset/import',files={'employees':('employees.json',json.dumps(a.payload)),'history':('history.csv',a.csvbytes(a.rows))}).status_code==200
            ctx=c.get('/api/employees/JQA004/recommendations/context').json();result={'context':ctx}
            if live:
                t=time.perf_counter();r=c.post('/api/employees/JQA004/recommendations');result.update(http=r.status_code,body=r.json(),elapsed=time.perf_counter()-t)
                a.record('Z03' if not flip else 'Z04','Critical-flag contrastive live recommendation '+str(flip),r.status_code==200,str(r.json()),'HIGH')
            supplement[variant]=result
      l=supplement['critical_False']['context'];r=supplement['critical_True']['context']
      a.record('Z05','Critical flags propagate independently of skill/role/grade/history',l['current_skills']==r['current_skills'] and l['employee']==r['employee'] and l['history']==r['history'] and l['candidates']!=r['candidates'],'Only Senior Backend critical_skills modified in temporary catalog; immutable source intact','HIGH')
      if live:
        one=supplement['critical_False']['body'].get('recommendations',[]);two=supplement['critical_True']['body'].get('recommendations',[])
        a.record('Z06','LLM selection responds to critical flag alone',bool(one) and bool(two) and one[0]['event_id'] in ['EV_006','EV_007'] and two[0]['event_id']=='EV_036',str([x['event_id'] for x in one])+' -> '+str([x['event_id'] for x in two]),'HIGH')
      # Test actual unknown imported identity with unmodified configured identities.
      defaults=settings.model_copy(update={'state_path':root/'default-auth.json'})
      with a.TestClient(a.create_app(defaults,ai_client=a.AdversarialAI()),raise_server_exceptions=False) as c:
        hr_token=next((t for t,p in defaults.dev_identities.items() if p.role=='hr'),None)
        if hr_token:
            c.headers['Authorization']='Bearer '+hr_token
            r=c.post('/api/dataset/import',files={'employees':('employees.json',json.dumps(a.payload)),'history':('history.csv',a.csvbytes(a.rows))})
            assert r.status_code==200,r.text
            results=[]
            for token in [hr_token,*[t for t,p in defaults.dev_identities.items() if p.role=='employee']]:
                rr=c.post('/api/employees/JQA019/activities/EV_012/complete',headers={'Authorization':'Bearer '+token},json={'command_id':str(uuid.uuid4())})
                results.append({'principal_role':defaults.dev_identities[token].role,'status':rr.status_code})
            supplement['imported_identity']=results
            documented='To add imported employee identities, set DEV_IDENTITIES_JSON' in (a.ROOT/'README.md').read_text(encoding='utf-8')
            a.record('Z07','New jury employee access requires documented self-identity provisioning',all(r['status']==403 for r in results) and documented,str(results)+'; correct refusal for foreign/HR principals; README documents DEV_IDENTITIES_JSON before startup; main I03-I07 verify provisioned self-token workflow','HIGH')
        else:a.record('Z07','New jury employee default access',None,'No configured HR principal')
      with a.TestClient(app('history_statuses',lambda d:None),raise_server_exceptions=False) as c:
        c.headers['Authorization']='Bearer jury-hr'
        assert c.post('/api/dataset/import',files={'employees':('employees.json',json.dumps(a.payload)),'history':('history.csv',a.csvbytes(a.rows))}).status_code==200
        for i,(status,pct,event) in enumerate([('in_progress',50,'EV_012'),('dropped',50,'EV_009'),('overdue',50,'EV_001')]):
            row={'record_id':'JQSTATUS'+str(i),'employee_id':'JQA004','event_id':event,'date':'2026-09-20','due_date':'2026-09-25' if status=='overdue' else '', 'status':status,'completion_pct':pct,'score':'','feedback_rating':'','assigned_by':'hr' if status=='overdue' else 'self'}
            rr=c.post('/api/dataset/import',files={'history':('history.csv',a.csvbytes([row]))})
            profile=c.get('/api/employees/JQA004').json()
            a.record('Z'+str(8+i).zfill(2),'Incomplete '+status+' does not increase skills',rr.status_code==200 and profile['current_skills']==a.employees[3]['skills'],str(rr.status_code),'HIGH')
        bad={'record_id':'JQSTATUSBAD','employee_id':'JQA004','event_id':'EV_012','date':'2026-09-21','due_date':'','status':'registered','completion_pct':0,'score':'','feedback_rating':'','assigned_by':'self'}
        rr=c.post('/api/dataset/import',files={'history':('history.csv',a.csvbytes([bad]))});a.record('Z11','Unknown registered status rejected (not in original schema)',rr.status_code==422,str(rr.status_code),'MEDIUM')
        bad['status']='completed';bad['completion_pct']=20
        rr=c.post('/api/dataset/import',files={'history':('history.csv',a.csvbytes([bad]))});a.record('Z12','Inconsistent completed percentage rejected',rr.status_code==422,str(rr.status_code),'MEDIUM')
        malformed=c.post('/api/employees/JQA004/activities/EV_012/complete',headers={'Authorization':'Bearer JQA004'},json={'command_id':'not-uuid'})
        a.record('Z13','Malformed completion command rejected',malformed.status_code==422,str(malformed.status_code),'MEDIUM')
    if counter:counter.delegate.close()
    supplement['live_calls']=counter.calls if counter else 0;supplement['live_errors']=counter.errors if counter else [];supplement['live_timings']=a.timings['live_ai'];supplement['registry']=a.registry
    (a.OUT/'supplement.json').write_text(json.dumps(supplement,indent=2),encoding='utf-8')
    print(json.dumps({'supplement_calls':supplement['live_calls'],'registry':a.registry},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');run(p.parse_args().live)
