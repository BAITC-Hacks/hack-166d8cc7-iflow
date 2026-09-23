"use client";
import {useEffect,useRef,useState} from "react";
import {useToken} from "@/components/session-provider";
import {StatusMessage} from "@/components/ui/status-message";
import {Trajectory} from "./trajectory";
import {getEmployee,getTrajectory,completeActivity,requestRecommendations} from "@/lib/api";
import type {EmployeeDetail,Trajectory as TrajectoryData,CompletionCommand} from "@/lib/types";
export function Profile({id}:{id:string}) {
 const token=useToken(); const [data,setData]=useState<EmployeeDetail>(); const [trajectory,setTrajectory]=useState<TrajectoryData>();
 const [error,setError]=useState("");const [notice,setNotice]=useState("");const [busy,setBusy]=useState(false);const [version,setVersion]=useState(0);
 const commands=useRef(new Map<string,CompletionCommand>());const active=useRef(true);const submitting=useRef(false);
 useEffect(()=>{active.current=true;return ()=>{active.current=false;};},[]);
 useEffect(()=>{const controller=new AbortController();Promise.all([getEmployee(id,token,controller.signal),getTrajectory(id,token,controller.signal)]).then(([e,t])=>{if(!controller.signal.aborted){setData(e);setTrajectory(t);setError("");}}).catch(e=>{if(!controller.signal.aborted)setError(e.message);});return ()=>controller.abort();},[id,token,version]);
 async function complete(eventId:string,source?:string,session?:string) {
   if(submitting.current)return;submitting.current=true;setBusy(true);setError("");
   const key=eventId+":"+(source??session??"new");
   const command=commands.current.get(key)??{command_id:crypto.randomUUID(),source_record_id:source??null,session_date:session??null};
   commands.current.set(key,command);
   try {const result=await completeActivity(id,eventId,command,token);if(active.current){setNotice(result.skill_changes.length?result.skill_changes.map(g=>`${g.skill_id}: ${g.before} → ${g.after}`).join("; "):"Activity completed. No additional skill gain.");setVersion(v=>v+1);}}
   catch(e){if(active.current)setError(e instanceof Error?e.message:"Completion failed");}
   finally{submitting.current=false;if(active.current)setBusy(false);}
 }
 if(!data||!trajectory)return <><StatusMessage error={error||undefined}/>{error&&<button onClick={()=>setVersion(v=>v+1)}>Retry loading</button>}</>;
 const ready=trajectory.candidates.filter(c=>!c.eligibility.next_session||c.eligibility.next_session<=data.as_of_date);
 return <><h2>{data.profile.full_name}</h2><p>{data.profile.role} · {data.profile.grade} · {data.profile.tenure_months} months</p>
 {error&&<StatusMessage error={error}/>} {notice&&<p role="status">{notice}</p>}
 <h3>Current skills</h3><table><thead><tr><th>Skill</th><th>Level</th></tr></thead><tbody>{Object.entries(data.current_skills).map(([k,v])=><tr key={k}><td>{k}</td><td>{v}/5</td></tr>)}</tbody></table>
 <Trajectory data={trajectory}/><button onClick={async()=>{try{await requestRecommendations(id,token);}catch(e){if(active.current)setNotice(e instanceof Error?e.message:"Recommendations unavailable");}}}>Request recommendations</button>
 <h2>Complete an activity</h2><p>Only the employee can complete their own activities. Future sessions are not completable.</p>
 {ready.map(c=><p key={c.event_id}><button disabled={busy} onClick={()=>complete(c.event_id,undefined,c.eligibility.next_session??undefined)}>Complete {c.title}</button></p>)}
 {!ready.length&&<p>No new activity is completable today. Existing assignments appear below.</p>}
 <h2>Participation history</h2><ul>{data.history.map((h,i)=><li key={h.source_record_id??i}>{h.event_id} · {h.date} · {h.status} {h.source_record_id&&["in_progress","overdue"].includes(h.status)&&<button disabled={busy} onClick={()=>complete(h.event_id,h.source_record_id!)}>Complete assignment {h.event_id}</button>}</li>)}</ul></>;
}
