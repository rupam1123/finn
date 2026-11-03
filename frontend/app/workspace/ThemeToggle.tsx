'use client';
import {useEffect,useState} from 'react';
import {Moon,Sun} from 'lucide-react';
export type Theme='light'|'dark';
export const themeKey='finn.theme';
export function savedTheme(storage:Pick<Storage,'getItem'>):Theme|null{try{const value=JSON.parse(storage.getItem(themeKey)||'null');return value==='light'||value==='dark'?value:null}catch{return null}}
export function applyTheme(theme:Theme){document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme;document.querySelector('meta[name="theme-color"]')?.setAttribute('content',theme==='dark'?'#000000':'#ffffff')}
export default function ThemeToggle(){
 const [theme,setTheme]=useState<Theme>('light');
 useEffect(()=>{const media=window.matchMedia?.('(prefers-color-scheme: dark)');const sync=()=>{let preferred:Theme|null=null;try{preferred=savedTheme(localStorage)}catch{}const value=preferred||(media?.matches?'dark':'light');applyTheme(value);setTheme(value)};sync();media?.addEventListener('change',sync);window.addEventListener('storage',sync);window.addEventListener('finn:reset-preferences',sync);return()=>{media?.removeEventListener('change',sync);window.removeEventListener('storage',sync);window.removeEventListener('finn:reset-preferences',sync)}},[]);
 function toggle(){const next:Theme=theme==='light'?'dark':'light';setTheme(next);applyTheme(next);try{localStorage.setItem(themeKey,JSON.stringify(next))}catch{}}
 return <button className="icon-button theme-toggle" type="button" onClick={toggle} aria-label={`Switch to ${theme==='light'?'dark':'light'} theme`} aria-pressed={theme==='dark'} title={`${theme==='light'?'Dark':'Light'} appearance`}>{theme==='light'?<Moon size={18} strokeWidth={1.7}/>:<Sun size={19} strokeWidth={1.7}/>}</button>
}
