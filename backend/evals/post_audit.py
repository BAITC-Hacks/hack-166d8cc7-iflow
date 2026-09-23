"""Six public-API live checks (max twelve provider attempts), disposable state."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.live:
        parser.error('Pass --live to allow six requests with one timeout recovery each')
    fixture=ROOT/'tests/fixtures/jury_profiles'
    results=[]
    with tempfile.TemporaryDirectory() as directory:
        settings=Settings.from_env().model_copy(update={'state_path':Path(directory)/'state.json',
            'notifications_worker_enabled':False,'ai_auto_prepare':False,
            'dev_identities':Settings(dev_identities={'audit-local':{'role':'hr'}}).dev_identities})
        with TestClient(create_app(settings)) as client:
            client.headers['Authorization']='Bearer audit-local'
            response=client.post('/api/dataset/import',files={
                'employees':('employees.json',(fixture/'employees.json').read_bytes(),'application/json'),
                'history':('activity_history.csv',(fixture/'activity_history.csv').read_bytes(),'text/csv')})
            response.raise_for_status()
            for employee_id in ['JQA001','JQA004','JQA008','JQA012','JQA013','JQA022']:
                start=time.perf_counter()
                response=client.post(f'/api/employees/{employee_id}/recommendations')
                row={'employee_id':employee_id,'http_status':response.status_code,
                    'seconds':round(time.perf_counter()-start,3),'body':response.json()}
                results.append(row)
                print(json.dumps({k:v for k,v in row.items() if k!='body'}),flush=True)
            hr=client.get('/api/hr/dashboard').json()
            results.append({'hr_missing_count':len(hr['employees_without_recommendation']),
                'jury_catalog_gap':[g for g in hr['critical_catalog_gaps'] if g['employee_id']=='JQA022']})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    if any(r.get('http_status',200)!=200 for r in results):
        raise SystemExit(1)


if __name__=='__main__':
    main()
