import type { EmployeeList, EmployeeDetail, Trajectory } from "./types";
const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export class ApiError extends Error {
 constructor(public status: number, public error: {code: string; message: string; details: unknown[]}) { super(error.message); }
}
export async function request<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
 const headers = new Headers(init.headers);
 headers.set("Authorization", `Bearer ${token}`);
 const response = await fetch(`${base}${path}`, {...init, headers, cache: "no-store"});
 const body = await response.json();
 if (!response.ok) throw new ApiError(response.status, body.error ?? {code:"unexpected", message:"Request failed", details:[]});
 return body as T;
}
export const listEmployees = (token: string, signal?: AbortSignal) => request<EmployeeList>("/api/employees",token,{signal});
export const getEmployee = (id: string, token: string, signal?: AbortSignal) => request<EmployeeDetail>(`/api/employees/${encodeURIComponent(id)}`,token,{signal});
export const getTrajectory = (id: string, token: string, signal?: AbortSignal) => request<Trajectory>(`/api/employees/${encodeURIComponent(id)}/trajectory`,token,{signal});

import type {CompletionCommand,CompletionResult,ImportResult,HRDashboard} from "./types";
export const completeActivity = (id:string,eventId:string,command:CompletionCommand,token:string) => request<CompletionResult>(`/api/employees/${encodeURIComponent(id)}/activities/${encodeURIComponent(eventId)}/complete`,token,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(command)});
export const getHRDashboard = (token:string,signal?:AbortSignal) => request<HRDashboard>("/api/hr/dashboard",token,{signal});
export const requestRecommendations = (id:string,token:string) => request<never>(`/api/employees/${encodeURIComponent(id)}/recommendations`,token,{method:"POST"});
export function importDataset(files:{employees?:File;history?:File},token:string){
 const form=new FormData();
 if(files.employees)form.append("employees",files.employees);
 if(files.history)form.append("history",files.history);
 return request<ImportResult>("/api/dataset/import",token,{method:"POST",body:form});
}
