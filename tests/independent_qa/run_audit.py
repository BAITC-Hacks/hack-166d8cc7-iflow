"""Independent jury audit. Run from repository root; no production mutations.
python tests/independent_qa/run_audit.py [--live]
Only --live contacts configured OpenAI, at most 30 calls, no retries.
"""
import argparse, copy, csv, hashlib, io, json, math, os, statistics, sys, tempfile, time, uuid, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings
from app.core.auth import Principal
from app.ai.openai_provider import create_recommender
from app.schemas.recommendation import RecommendationResult

OUT=Path(os.environ.get('QA_OUTPUT_DIR',str(ROOT/'tests/independent_qa/results-latest'))); OUT.mkdir(parents=True,exist_ok=True)
FIX=ROOT/'tests/fixtures/jury_profiles'; FIX.mkdir(parents=True,exist_ok=True)
raw=ROOT/'data/raw'
original=json.loads((raw/'employees.json').read_text(encoding='utf-8'))
events=json.loads((raw/'events.json').read_text(encoding='utf-8'))['events']; ev={e['event_id']:e for e in events}
skills=json.loads((raw/'skills.json').read_text(encoding='utf-8'))
profiles=skills['role_profiles']; allskills={s['skill_id']:5 for s in skills['skills']}
rows=[]; employees=[]; descriptions={}; registry=[]; artifacts={}; timings={'profile':[],'trajectory':[],'hr':[],'live_ai':[],'recommendation_cached':[]}
def record(id, title, ok, detail='', severity=None):
    registry.append(dict(id=id,title=title,status='NOT VERIFIED' if ok is None else 'PASSED' if ok else 'FAILED',detail=detail,severity=severity if ok is False else None))
def employee(n,desc,levels=None,grade='Middle',goal='default'):
    p=dict(employee_id=f'JQA{n:03}',full_name='Synthetic Jury Profile',department='Backend Development',role='Backend Engineer',grade=grade,manager_id='E0050',hire_date='2024-10-01',tenure_months=24,work_format='hybrid',preferred_language='en',career_goal={'target_role':'Backend Engineer','target_grade':'Senior'} if goal=='default' else goal,skills={**allskills,**(levels or {})},last_review_date='2026-09-15')
    employees.append(p);descriptions[p['employee_id']]=desc
    history(n,'EV_004','completed','2024-10-10')
    return p
def history(n,event,status,date):
    rows.append(dict(record_id=f'JQR{len(rows)+1:05}',employee_id=f'JQA{n:03}',event_id=event,date=date,due_date='',status=status,completion_pct=100 if status=='completed' else 0,score='',feedback_rating='',assigned_by='manager' if status=='declined' else 'self'))
base={'SK_SYSTEM_DESIGN':3,'SK_PUBLIC_SPEAKING':1}
employee(1,'Lowest skill trap',base)
for d in ['2026-06-01','2026-07-01','2026-08-01']:history(1,'EV_036','no_show',d)
employee(2,'History pair A: completed workshop/club',base);history(2,'EV_036','completed','2026-07-01')
employee(3,'History pair B: repeated noncompletion',base)
for d,s in [('2026-06-01','no_show'),('2026-07-01','declined'),('2026-08-01','no_show')]:history(3,'EV_036',s,d)
employee(4,'Critical gap 1 versus noncritical gap 2',{'SK_SYSTEM_DESIGN':3,'SK_PUBLIC_SPEAKING':0})
employee(5,'Completion pair A: no completed design activity',{'SK_SYSTEM_DESIGN':3})
employee(6,'Completion pair B: EV_006 already completed',{'SK_SYSTEM_DESIGN':3});history(6,'EV_006','completed','2026-08-01')
employee(7,'Cap trap: fundamentals cannot raise design 3 to 4',{'SK_SYSTEM_DESIGN':3})
employee(8,'Prerequisite trap: design 1 excludes advanced activities',{'SK_SYSTEM_DESIGN':1})
employee(9,'Role trap: frontend goal with backend current role',{'SK_WEB_PERFORMANCE':1,'SK_TYPESCRIPT':3},goal={'target_role':'Frontend Engineer','target_grade':'Senior'})
employee(10,'Grade pair A Junior',{'SK_SYSTEM_DESIGN':3},grade='Junior')
employee(11,'Career pair A backend goal',{'SK_SYSTEM_DESIGN':3,'SK_DATA_MODELING':1})
employee(12,'Career pair B analyst goal',{'SK_SYSTEM_DESIGN':3,'SK_DATA_MODELING':1},goal={'target_role':'Data Analyst','target_grade':'Senior'})
employee(13,'No explicit goal',{'SK_SYSTEM_DESIGN':3},goal=None)
employee(14,'No valid activity for sole critical design gap',{'SK_SYSTEM_DESIGN':3})
history(14,'EV_006','completed','2026-07-01');history(14,'EV_007','completed','2026-08-01')
employee(15,'All skills 5, maximum grade',grade='Lead',goal=None)
employee(16,'Same-day review boundary',{'SK_SYSTEM_DESIGN':2});history(16,'EV_005','completed','2026-09-15')
employee(17,'Before review boundary',{'SK_SYSTEM_DESIGN':2});history(17,'EV_005','completed','2026-09-14')
employee(18,'After review boundary and multi-skill gain',{'SK_SYSTEM_DESIGN':2,'SK_API_DESIGN':2});history(18,'EV_005','completed','2026-09-16')
employee(19,'Self-paced completion workflow',{'SK_PYTHON':3})
employee(20,'Missed then completed recurring club',base);history(20,'EV_036','no_show','2026-06-01');history(20,'EV_036','completed','2026-07-01')
employee(21,'No history',{'SK_SYSTEM_DESIGN':3});rows[:]=[r for r in rows if r['employee_id']!='JQA021']
employee(22,'Critical design gap unfillable while optional speaking remains',base);history(22,'EV_006','completed','2026-07-01');history(22,'EV_007','completed','2026-08-01')
employee(23,'Cap saturation completion must never lower existing skills',{'SK_PYTHON':5});history(23,'EV_012','completed','2026-09-16')
employee(24,'Multi-skill self paced partial capped gain',{'SK_CLOUD':2,'SK_CICD':5})
rows.sort(key=lambda r:(r['date'],r['employee_id'],r['event_id']))
payload={'meta':original['meta'],'employees':employees}
(FIX/'employees.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
cols=['record_id','employee_id','event_id','date','due_date','status','completion_pct','score','feedback_rating','assigned_by']
def csvbytes(rs):
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=cols);w.writeheader();w.writerows(rs);return s.getvalue().encode()
(FIX/'activity_history.csv').write_bytes(csvbytes(rows))
(FIX/'manifest.json').write_text(json.dumps(descriptions,indent=2),encoding='utf-8')

class CountingAI:
    def __init__(self,delegate):self.delegate=delegate;self.calls=0;self.errors=[];self.cache_key='independent-live-audit'
    def refine(self,c):
        if self.calls>=30:raise RuntimeError('Independent audit hard limit')
        self.calls+=1;t=time.perf_counter()
        try:return self.delegate.refine(c)
        except Exception as e:self.errors.append({'call':self.calls,'employee_id':c.employee_id,'type':type(e).__name__});raise
        finally:timings['live_ai'].append(time.perf_counter()-t)
class AdversarialAI:
    def __init__(self):self.mode='EV_FAKE';self.cache_key='red-team'
    def refine(self,c):
        cand=c.candidates[0]; evidence=[]
        for kind in ['current_grade','skill_levels','attainable_gain']:
            evidence.append(next(f for f in cand.factors if f.kind==kind))
        return RecommendationResult(status='success',employee_id=c.employee_id,revision=c.revision,as_of_date=c.as_of_date,recommendations=[dict(event_id=cand.event_id if self.mode=='prose' else self.mode,explanation='You completed 99 workshops because your manager forced you. This activity raises System Design to 99. Your goal is CEO. Take the invented Galactic Leadership Course.',evidence=evidence)])
def oracle_skills(p):
    cur=p['skills'].copy()
    for r in rows:
        if r['employee_id']==p['employee_id'] and r['status']=='completed' and r['date']>p['last_review_date']:
            for g in ev[r['event_id']]['develops_skills']:
                k=g['skill_id'];cur[k]=max(cur.get(k,0),min(cur.get(k,0)+g['gain'],g['max_level']))
    return cur
def assert_candidates(p,ctx):
    cur=oracle_skills(p);errors=[]
    for c in ctx['candidates']:
        e=ev[c['event_id']]
        if e['mandatory'] or p['role'] not in e['target_roles'] or p['grade'] not in e['target_grades']:errors.append(e['event_id']+' audience/mandatory')
        if any(cur.get(k,0)<v for k,v in e['prerequisites'].items()):errors.append(e['event_id']+' prerequisites')
        if e['format']!='self_paced' and not any(d>='2026-10-01' for d in e['upcoming_sessions']):errors.append(e['event_id']+' unavailable')
        if e['event_id']!='EV_036' and any(r['employee_id']==p['employee_id'] and r['event_id']==e['event_id'] and r['status']=='completed' for r in rows):errors.append(e['event_id']+' completed')
        gains={g['skill_id']:max(0,min(cur.get(g['skill_id'],0)+g['gain'],g['max_level'])-cur.get(g['skill_id'],0)) for g in e['develops_skills']}
        if c['possible_skill_gains']!=gains:errors.append(e['event_id']+' gain')
    return errors
def request(c,method,url,group=None,**kwargs):
    t=time.perf_counter();r=getattr(c,method)(url,**kwargs)
    if group:timings[group].append(time.perf_counter()-t)
    return r
def run(live):
    archive=Path.home()/'Downloads/career_quest_dataset.zip'
    if archive.exists():
        with zipfile.ZipFile(archive) as z:
            mismatches=[f for f in ['employees.json','events.json','skills.json','activity_history.csv','README.md'] if z.read('case_1/career_quest_dataset/'+f)!=(raw/f).read_bytes()]
        record('D01','Original archive integrity',not mismatches,str(mismatches))
    else:
        record('D01','Original archive integrity',None,'Original archive not available on this host')
    record('D02','24 distinct schema-preserving synthetic profiles',len(employees)==24 and len({e['employee_id'] for e in employees})==24,'Full validity additionally checked by public import')
    settings=Settings.from_env(); settings=settings.model_copy(update={'notifications_worker_enabled':False,'ai_auto_prepare':False,'application_date':None})
    identities={'jury-hr':Principal(role='hr'),**{p['employee_id']:Principal(role='employee',employee_id=p['employee_id']) for p in employees}}
    settings=settings.model_copy(update={'dev_identities':identities})
    fake=AdversarialAI();counter=CountingAI(create_recommender(settings)) if live else None
    artifacts['environment']={'python':sys.version.split()[0],'model':settings.openai_model,'provider':settings.ai_provider,'live_requested':live,'snapshot':'2026-10-01','notifications_worker':False,'network_retries':0}
    with tempfile.TemporaryDirectory(prefix='career-jury-') as tmp:
      settings=settings.model_copy(update={'state_path':Path(tmp)/'state.json'})
      with TestClient(create_app(settings,ai_client=counter or fake),raise_server_exceptions=False) as c:
        c.headers['Authorization']='Bearer jury-hr'
        files={'employees':('employees.json',json.dumps(payload).encode(),'application/json'),'history':('activity_history.csv',csvbytes(rows),'text/csv')}
        r=c.post('/api/dataset/import',files=files);artifacts['import']=r.json();record('I01','Public multipart import of new employees and history',r.status_code==200 and r.json().get('added_employees')==24,str(r.json()),'CRITICAL')
        if r.status_code!=200:raise RuntimeError('Fixture import rejected: '+str(r.json()))
        r=c.post('/api/dataset/import',files=files);record('I02','Reimport is idempotent',r.status_code==200 and r.json().get('added_history')==0,str(r.json()),'HIGH')
        contexts={};details={};trajectories={}
        for p in employees:
            id=p['employee_id'];r=request(c,'get',f'/api/employees/{id}','profile');details[id]=r.json()
            record('P'+id[3:],'Imported profile current skills match independent dataset oracle',r.status_code==200 and r.json().get('current_skills')==oracle_skills(p),id,'CRITICAL')
            ctx=c.get(f'/api/employees/{id}/recommendations/context').json();contexts[id]=ctx
            tr=request(c,'get',f'/api/employees/{id}/trajectory','trajectory').json();trajectories[id]=tr
            errs=assert_candidates(p,ctx);record('E'+id[3:],'All candidate eligibility and gains satisfy original catalog',not errs,str(errs),'CRITICAL')
        artifacts.update(contexts=contexts,profiles=details,trajectories=trajectories)
        ids=lambda n:{x['event_id'] for x in contexts[f'JQA{n:03}']['candidates']}
        checks=[('B01','Completed EV_006 excluded; EV_007 remains', 'EV_006' not in ids(6) and 'EV_007' in ids(6)),('B02','Cap 3 course excluded for sole design 3-to-4 gap','EV_005' not in ids(7)),('B03','Missing design prerequisite excludes EV_006 and EV_007',not ids(8)&{'EV_006','EV_007'}),('B04','Frontend-only events excluded for backend career switch',not ids(9)&{'EV_014','EV_015'}),('B05','Junior cannot access advanced Middle design',not ids(10)&{'EV_006','EV_007'}),('B06','No valid activity returns empty candidate catalog',not ids(14)),('B07','Recurring completed speaking club remains eligible','EV_036' in ids(2)),('B08','No goal defaults to next grade without inventing explicit goal',trajectories['JQA013']['next_grade']=='Senior' and trajectories['JQA013']['career_goal_analysis'] is None),('B09','Maximum grade with all skills 5 has no fabricated next grade',trajectories['JQA015']['next_grade'] is None),('B10','After review activity adds both capped gains',details['JQA018']['current_skills']['SK_SYSTEM_DESIGN']==3 and details['JQA018']['current_skills']['SK_API_DESIGN']==3),('B11','Before review no double gain',details['JQA017']['current_skills']['SK_SYSTEM_DESIGN']==2),('B12','Skill above cap never decreases',details['JQA023']['current_skills']['SK_PYTHON']==5),('B13','Self-paced empty upcoming sessions eligible','EV_012' in ids(19)),('B14','Multi-skill cap preserves 5 while allowing cloud gain',next(x for x in contexts['JQA024']['candidates'] if x['event_id']=='EV_009')['possible_skill_gains']=={'SK_CLOUD':1,'SK_CICD':0})]
        for id,title,ok in checks:record(id,title,ok,'See contexts/profiles in evidence.json','HIGH')
        record('B15','Same-day review interpretation',None,'Observed design level '+str(details['JQA016']['current_skills']['SK_SYSTEM_DESIGN'])+'; README says after review but lacks intraday ordering. Strict > is defensible, cannot prove whether same-day completion was assessed.')
        for label,a,b,factor in [('A',2,3,'history'),('B',11,12,'career_goal'),('C',5,6,'completed history'),('E',5,10,'grade')]:
            pa=copy.deepcopy(employees[a-1]);pb=copy.deepcopy(employees[b-1]);pa.pop('employee_id');pb.pop('employee_id')
            diffs=[k for k in pa if pa[k]!=pb[k]]
            artifacts.setdefault('contrastive',{})[label]={'a':a,'b':b,'factor':factor,'profile_differences':diffs,'candidates_a':sorted(ids(a)),'candidates_b':sorted(ids(b))}
        record('C01','History pair equal role/grade/skills/goal',not artifacts['contrastive']['A']['profile_differences'],'Only identity and history differ')
        record('C02','Career goal changes target analysis and candidate pool',contexts['JQA011']['targets']!=contexts['JQA012']['targets'] and ids(11)!=ids(12),'Pair B','HIGH')
        record('C03','Completed event changes eligible alternatives',ids(5)!=ids(6),'Pair C','HIGH')
        record('C04','Grade changes eligible alternatives',ids(5)!=ids(10),'Pair E','HIGH')
        record('C05','Critical flags alone under modified target requirements',None,'Original role requirements immutable in public import. Separate isolated catalog sensitivity test required; not conflated with goal change.')
        for name,url,expected in [('unknown employee','/api/employees/DOES_NOT_EXIST',404),('anonymous profile','/api/employees/JQA001',401)]:
            r=c.get(url,headers={'Authorization':''} if name.startswith('anonymous') else {});record('S01' if name.startswith('unknown') else 'S02',name,r.status_code==expected,str(r.status_code),'HIGH')
        for ix,url in enumerate(['/api/hr/dashboard','/api/employees/JQA002','/api/employees/JQA002/recommendations/context']):
            r=c.get(url,headers={'Authorization':'Bearer JQA001'});record(f'S{ix+3:02}','Employee cannot read another employee or HR',r.status_code==403,url+': '+str(r.status_code),'CRITICAL')
        r=c.get('/api/employees',headers={'Authorization':'Bearer JQA001'});record('S06','Employee list includes only self',[x['employee_id'] for x in r.json()['items']]==['JQA001'],'','CRITICAL')
        r=c.post('/api/dataset/import',files=files,headers={'Authorization':'Bearer JQA001'});record('S07','Employee cannot import',r.status_code==403,str(r.status_code),'HIGH')
        invalid=copy.deepcopy(payload);invalid['employees']=[copy.deepcopy(employees[0])];invalid['employees'][0]['employee_id']='JQABAD';invalid['employees'][0]['skills']['SK_UNKNOWN']=1
        r=c.post('/api/dataset/import',files={'employees':('employees.json',json.dumps(invalid))});record('V01','Unknown skill rejected on public import',r.status_code==422,str(r.status_code),'HIGH')
        r=c.post('/api/dataset/import',files={'employees':('employees.json','{broken')});record('V02','Malformed JSON rejected',r.status_code==422,str(r.status_code),'HIGH')
        r=c.post('/api/dataset/import',files={'history':('history.csv',csvbytes([rows[0],rows[0]]))});record('V03','Duplicate history ID in upload rejected',r.status_code==422,str(r.status_code),'HIGH')
        r=request(c,'get','/api/hr/dashboard','hr');hr=r.json();artifacts['hr']=hr
        record('H01','HR finds employee with no candidates','JQA014' in hr['employees_without_candidate'],'','HIGH')
        record('H02','HR reports employees without actual recommendation',hr.get('employees_without_recommendation') is not None,str({k:hr[k] for k in ['recommendation_status','employees_without_recommendation']}),'HIGH')
        record('H03','HR identifies specific employee with uncovered critical gap despite optional candidate',any(g['employee_id']=='JQA022' and g['skill_id']=='SK_SYSTEM_DESIGN' for g in hr.get('critical_catalog_gaps',[])),'JQA022 has unfillable critical design gap and optional speaking','HIGH')
        expected_counts={}
        grades=['Junior','Middle','Senior','Lead']
        allp=original['employees']+employees
        # Independent aggregation uses API current skill values for original staff, independent role requirements.
        for p in allp:
            if p['grade']=='Lead':continue
            levels=oracle_skills(p) if p['employee_id'].startswith('JQA') else c.get('/api/employees/'+p['employee_id']).json()['current_skills']
            target=next(x for x in profiles if x['role']==p['role'] and x['grade']==grades[grades.index(p['grade'])+1])
            for sk,level in target['required_skills'].items():
                if levels.get(sk,0)<level:expected_counts[sk]=expected_counts.get(sk,0)+1
        record('H04','HR gap aggregation matches independent requirements',{x['skill_id']:x['employee_count'] for x in hr['skill_gap_counts']}==expected_counts,'224 employees; source projections checked separately','HIGH')
        expected_history=list(csv.DictReader(io.StringIO((raw/'activity_history.csv').read_text(encoding='utf-8-sig'))))+rows
        counts={}
        for row in expected_history:counts.setdefault(row['event_id'],{});counts[row['event_id']][row['status']]=counts[row['event_id']].get(row['status'],0)+1
        record('H05','HR participation counts match original plus imported history',all(x['status_counts']==counts.get(x['event_id'],{}) for x in hr['participation_by_event']),'','HIGH')
        live_results={}
        for n in ([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,19,20,21,22,24] if live else [14,15]):
            id=f'JQA{n:03}';r=request(c,'post',f'/api/employees/{id}/recommendations');live_results[id]={'http':r.status_code,'body':r.json()};artifacts['live_results']=live_results
            record('L'+str(n).zfill(3),'Public recommendation '+id,r.status_code==200,str(r.status_code)+' '+str(r.json().get('status',r.json().get('error',{}))),'HIGH')
            (OUT/'evidence.partial.json').write_text(json.dumps(artifacts,indent=2),encoding='utf-8')
            print('Recommendation',id,r.status_code,flush=True)
        if live:
            for n in [1,4]:
                data=live_results[f'JQA{n:03}']; recs=data['body'].get('recommendations',[])
                record(f'M{n:02}','Critical design wins over lower/larger public-speaking gap',None if data['http']!=200 else bool(recs) and recs[0]['event_id'] in ['EV_006','EV_007'],str([x['event_id'] for x in recs])+'; response unavailable means selection not verified','HIGH')
            for label,a,b in [('A',2,3),('B',11,12),('C',5,6),('E',5,10)]:
                aa=live_results[f'JQA{a:03}'];bb=live_results[f'JQA{b:03}'];artifacts['contrastive'][label].update(output_a=aa,output_b=bb)
            r=request(c,'post','/api/employees/JQA001/recommendations','recommendation_cached');record('R01','Repeated recommendation succeeds and preserves result',r.status_code==200 and r.json()==live_results['JQA001']['body'],'Cached repeat is not independent LLM reasoning','MEDIUM')
        else:record('L000','Live multi-factor reasoning',None,'Run with --live; fake boundary tests are not reasoning evidence')
        command={'command_id':str(uuid.uuid4())};head={'Authorization':'Bearer JQA019'}
        before=c.get('/api/employees/JQA019/trajectory').json();r=c.post('/api/employees/JQA019/activities/EV_012/complete',json=command,headers=head);artifacts['completion']=r.json()
        record('I03','Imported employee completes eligible self-paced activity',r.status_code==200 and r.json().get('skill_changes')==[{'skill_id':'SK_PYTHON','before':3,'after':4,'gain':1}],str(r.status_code),'CRITICAL')
        r2=c.post('/api/employees/JQA019/activities/EV_012/complete',json=command,headers=head);record('I04','Same completion command is idempotent',r2.json()==r.json(),'','HIGH')
        r3=c.post('/api/employees/JQA019/activities/EV_012/complete',json={'command_id':str(uuid.uuid4())},headers=head);record('I05','Second complete with fresh command rejected',r3.status_code==409,str(r3.status_code),'HIGH')
        after=c.get('/api/employees/JQA019/trajectory').json();record('I06','Trajectory improves after completion',after['requirement_coverage']>before['requirement_coverage'] and not after['candidates'],'','CRITICAL')
        rr=c.post('/api/employees/JQA019/recommendations');record('I07','Recommendation after complete no longer suggests completed course',rr.status_code==200 and rr.json().get('status')=='no_candidates',str(rr.json()),'HIGH')
        # Injection is explicitly local and deliberately separate from live reasoning.
        c.app.state.notifications.ai_client=fake;c.app.state.ai_client=fake
        for index,mode in enumerate(['EV_FAKE','EV_999','prose']):
            fake.mode=mode;fake.cache_key='red-team-'+mode
            r=c.post('/api/employees/JQA005/recommendations');artifacts.setdefault('injections',{})[mode]={'http':r.status_code,'body':r.json()}
            safe = r.status_code!=200 if mode!='prose' else r.status_code==200 and all(x not in r.text for x in ['Galactic','99 workshops','CEO','to 99'])
            record('X0'+str(index+1),'Block fabricated '+('free-text facts/course' if mode=='prose' else mode),safe,str(r.status_code)+' '+str(r.json()),'HIGH' if mode=='prose' else 'CRITICAL')
    if counter:counter.delegate.close();artifacts['live_calls']=counter.calls;artifacts['live_errors']=counter.errors
    else:artifacts['live_calls']=0;artifacts['live_errors']=[]
    for key,vals in timings.items():
        if vals:artifacts.setdefault('performance',{})[key]={'n':len(vals),'min':min(vals),'avg':statistics.mean(vals),'p95':sorted(vals)[math.ceil(.95*len(vals))-1],'max':max(vals)}
    record('T01','Profile/API responses below 2 seconds',max(timings['profile']+timings['trajectory'])<2,str(artifacts.get('performance',{})),'HIGH')
    record('T02','Live AI response below 10 seconds',max(timings['live_ai'])<10 if timings['live_ai'] else None,str(artifacts.get('performance',{}).get('live_ai')),'HIGH')
    record('T03','Browser rendered UI latency and full UI import click path',None,'ASGI public API exercised; no browser automation')
    artifacts['registry']=registry
    (OUT/'evidence.json').write_text(json.dumps(artifacts,indent=2),encoding='utf-8')
    (OUT/'registry.json').write_text(json.dumps(registry,indent=2),encoding='utf-8')
    totals={s:sum(x['status']==s for x in registry) for s in ['PASSED','FAILED','NOT VERIFIED']};totals['TOTAL']=len(registry)
    print(json.dumps({'totals':totals,'live_calls':artifacts['live_calls'],'live_errors':artifacts['live_errors'],'performance':artifacts.get('performance',{})},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--live',action='store_true');run(ap.parse_args().live)
