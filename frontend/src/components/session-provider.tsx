"use client";
import { createContext, useContext, useState, type ReactNode } from "react";
const Session = createContext("");
export const useToken = () => useContext(Session);
export function SessionProvider({children}: {children: ReactNode}) {
 const [token,setToken]=useState("");
 const [draft,setDraft]=useState("");
 return <><form className="session" onSubmit={e=>{e.preventDefault();setToken(draft.trim());}}>
 <label htmlFor="token">Development token</label>
 <input id="token" type="password" autoComplete="off" value={draft} onChange={e=>setDraft(e.target.value)}/>
 <button type="submit">Use identity</button><button type="button" onClick={()=>{setToken("");setDraft("");}}>Sign out</button>
 <small>Local demo only: demo-employee or demo-hr. Production authentication is not enabled.</small>
 </form><Session.Provider value={token}><div key={token}>{token?children:<p>Enter a development token to view authorized data.</p>}</div></Session.Provider></>;
}
