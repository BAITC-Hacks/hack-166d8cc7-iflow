"use client";
import {useEffect,useState} from "react";
import {useToken} from "@/components/session-provider";
import {StatusMessage} from "@/components/ui/status-message";
import {Trajectory} from "./trajectory";
import {getEmployee,getTrajectory} from "@/lib/api";
import type {EmployeeDetail,Trajectory as TrajectoryData} from "@/lib/types";
export function Profile({id}:{id:string}) {
 const token=useToken(); const [data,setData]=useState<EmployeeDetail>(); const [trajectory,setTrajectory]=useState<TrajectoryData>();const [error,setError]=useState("");
 useEffect(()=>{const controller=new AbortController();Promise.all([getEmployee(id,token,controller.signal),getTrajectory(id,token,controller.signal)]).then(([e,t])=>{if(!controller.signal.aborted){setData(e);setTrajectory(t);}}).catch(e=>{if(!controller.signal.aborted)setError(e.message);});return ()=>controller.abort();},[id,token]);
 if(error)return <StatusMessage error={error}/>;if(!data||!trajectory)return <StatusMessage/>;
 return <><h2>{data.profile.full_name}</h2><p>{data.profile.role} · {data.profile.grade} · {data.profile.tenure_months} months</p>
 <h3>Current skills</h3><table><thead><tr><th>Skill</th><th>Level</th></tr></thead><tbody>{Object.entries(data.current_skills).map(([k,v])=><tr key={k}><td>{k}</td><td>{v}/5</td></tr>)}</tbody></table>
 <Trajectory data={trajectory}/><h2>Participation history</h2><ul>{data.history.map((h,i)=><li key={h.source_record_id??i}>{h.event_id} · {h.date} · {h.status}</li>)}</ul></>;
}
