"""Single reproducible command for the independent automated audit suite."""
import argparse, json
import run_audit, supplement, performance
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');args=p.parse_args()
    run_audit.run(args.live)
    supplement.run(args.live)
    performance.run(args.live)
    rows=[]
    for filename in ['evidence.json','supplement.json','performance_api.json']:
        rows.extend(json.loads((run_audit.OUT/filename).read_text(encoding='utf-8'))['registry'])
    totals={status:sum(r['status']==status for r in rows) for status in ['PASSED','FAILED','NOT VERIFIED']};totals['TOTAL']=len(rows)
    (run_audit.OUT/'automated_registry.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print('AUTOMATED TOTALS',json.dumps(totals))
    print('Manual explanation review in TEST_AUDIT.md is a dated observation; reassess new live responses after reruns.')
    raise SystemExit(1 if totals['FAILED'] else 0)
