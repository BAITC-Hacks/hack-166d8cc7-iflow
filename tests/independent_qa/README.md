# Independent Career Quest audit

Run from repository root, with the backend dependencies installed:

```powershell
python tests/independent_qa/run_all.py --live
```

Omit `--live` for the deterministic/fake-provider suite. Fake provider output is never evidence of model reasoning. The live command reads the existing `.env` through project settings without printing credentials. It disables the notification worker and automatic preparation, uses disposable state directories, imports synthetic profiles via the real multipart API, and makes at most 35 provider calls (main hard limit 30, two contrastive variants, three timing samples), no retries. The recorded audit used 21 calls. No emails are sent. Run in one process at a time; results are overwritten.

`run_audit.py` generates 24 synthetic profiles and 41 history records under `tests/fixtures/jury_profiles`. Each profile uses the original JSON schema. Most skills are deliberately 5 to isolate the remaining gaps. `JQA021` intentionally omits history as an explicit edge case; other profiles include onboarding. Profile identities differ for import but do not encode intended recommendations.

`supplement.py` creates temporary copies of the original catalog to test mandatory exclusion, no upcoming sessions, and the effect of changing only critical flags. These are schema-valid controlled variants, not claims about the unchanged original catalog. It also tests configured authentication without preprovisioning jury tokens.

The public HTTP API is exercised using FastAPI/Starlette TestClient (in-process ASGI). Browser rendering, TCP/reverse-proxy latency, concurrent load and deployment infrastructure are not covered. The fixture-auth run explicitly preprovisions own employee test tokens to isolate completion logic; a separate test demonstrates that the shipped configured identities cannot complete newly imported jury employees.

`results/evidence.json`, `supplement.json`, and `performance_api.json` contain actual responses, timing and test assertions. `registry-final.json` and `manual_review.json` are the recorded audit snapshot, including human factual review of each real recommendation. `run_all.py` prints new automated totals; it cannot automatically reproduce human semantic review. Manual review is bound to SHA-256 hashes of recorded evidence and must be redone after a new live run. The summary report is `TEST_AUDIT.md` in the repository root. This suite does not edit production code or datasets.
