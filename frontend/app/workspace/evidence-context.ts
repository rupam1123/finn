'use client';
import {createContext} from 'react';import type {Citation} from '../EvidenceButton';
export type EvidenceOpen={citation:Citation;visual:boolean;tab:string};
export const EvidenceContext=createContext<((value:EvidenceOpen)=>void)|null>(null);
