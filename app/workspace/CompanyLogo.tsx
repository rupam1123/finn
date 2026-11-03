'use client';
import {useState} from 'react';import logos from './company-logos.json';
export default function CompanyLogo({symbol}:{symbol:string}){const [failed,setFailed]=useState(false),logo=(logos as Record<string,{path:string}>)[symbol];return <span className="company-logo" aria-hidden="true">{logo&&!failed?<img src={logo.path} width="45" height="45" loading="lazy" alt="" onError={()=>setFailed(true)}/>:<span>{symbol.slice(0,2)}</span>}</span>}
