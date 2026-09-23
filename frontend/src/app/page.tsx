"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {useToken} from "@/components/session-provider";
import {StatusMessage} from "@/components/ui/status-message";
import {listEmployees} from "@/lib/api";
import type {EmployeeList} from "@/lib/types";
export default function Home() {
 const token=useToken();const [data,setData]=useState<EmployeeList>();const [error,setError]=useState("");
 useEffect(()=>{const controller=new AbortController();listEmployees(token,controller.signal).then(setData).catch(e=>{if(!controller.signal.aborted)setError(e.message);});return ()=>controller.abort();},[token]);
 if(error)return <StatusMessage error={error}/>; if(!data)return <StatusMessage/>;
 return <section><h2>Employee development</h2><p>Dataset date: {data.as_of_date}</p><ul>{data.items.map(e=><li key={e.employee_id}><Link href={`/employee/${e.employee_id}`}>{e.full_name}</Link> — {e.role}, {e.grade}</li>)}</ul></section>;
}
