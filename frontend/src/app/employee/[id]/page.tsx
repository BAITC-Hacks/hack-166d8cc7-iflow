"use client";
import {use} from "react";
import {Profile} from "@/components/employee/profile";
export default function EmployeePage({params}:{params:Promise<{id:string}>}) {const {id}=use(params);return <Profile key={id} id={id}/>;}
