"use client";
import {useEffect,useRef,useState} from "react";
import Link from "next/link";
import {useToken} from "@/components/session-provider";
import {StatusMessage} from "@/components/ui/status-message";
import {getHRDashboard,importDataset} from "@/lib/api";
import type {HRDashboard} from "@/lib/types";
export function Dashboard(){
 const token=useToken();const [data,setData]=useState<HRDashboard>();const [error,setError]=useState("");const [notice,setNotice]=useState("");
 const [employees,setEmployees]=useState<File>();const [history,setHistory]=useState<File>();const [busy,setBusy]=useState(false);const [version,setVersion]=useState(0);
 const active=useRef(true);useEffect(()=>{active.current=true;return ()=>{active.current=false;};},[]);
 useEffect(()=>{const c=new AbortController();getHRDashboard(token,c.signal).then(d=>{if(!c.signal.aborted){setData(d);setError("");}}).catch(e=>{if(!c.signal.aborted)setError(e.message);});return ()=>c.abort();},[token,version]);
 async function upload(e:React.FormEvent){e.preventDefault();if(busy)return;setBusy(true);setError("");try{const r=await importDataset({employees,history},token);if(active.current){setNotice(`Imported ${r.added_employees} employees and ${r.added_history} history records; revision ${r.revision}.`);setVersion(v=>v+1);}}catch(e){if(active.current)setError(e instanceof Error?e.message:"Import failed");}finally{if(active.current)setBusy(false);}}
 if(!data)return <><StatusMessage error={error||undefined}/>{error&&<button onClick={()=>setVersion(v=>v+1)}>Retry</button>}</>;
 return <><h2>HR development overview</h2><p>Dataset date: {data.as_of_date} · Revision {data.revision}</p>{error&&<StatusMessage error={error}/>} {notice&&<p role="status">{notice}</p>}
 <h3>Skills below next-grade requirements</h3><table><thead><tr><th>Skill</th><th>Employees with gap</th></tr></thead><tbody>{data.skill_gap_counts.map(g=><tr key={g.skill_id}><td>{g.name}</td><td>{g.employee_count}</td></tr>)}</tbody></table>
 <h3>Employees without an eligible candidate</h3><p>Recommendation coverage is unavailable until the recommendation engine is implemented.</p>
 <ul>{data.employees_without_candidate.map(id=><li key={id}><Link href={`/employee/${id}`}>{id}</Link></li>)}</ul>
 <h3>Participation by activity</h3><table><thead><tr><th>Activity</th><th>Statuses</th></tr></thead><tbody>{data.participation_by_event.map(e=><tr key={e.event_id}><td>{e.title}</td><td>{Object.entries(e.status_counts).map(([s,n])=>`${s}: ${n}`).join(", ")||"No participation"}</td></tr>)}</tbody></table>
 <h3>Import jury profiles / history</h3><p>Original schema, up to 10 MiB total. Conflicting IDs reject the entire import; identical rows are unchanged.</p>
 <form onSubmit={upload}><p><label htmlFor="employees">employees.json</label> <input id="employees" type="file" accept=".json" onChange={e=>setEmployees(e.target.files?.[0])}/></p>
 <p><label htmlFor="history">activity_history.csv</label> <input id="history" type="file" accept=".csv" onChange={e=>setHistory(e.target.files?.[0])}/></p>
 <button disabled={busy||(!employees&&!history)}>{busy?"Importing…":"Validate and import"}</button></form></>;
}
