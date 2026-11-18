import {useSyncExternalStore} from 'react'
import type {Collection} from './api'
const KEY='finna-preferred-exam',EVENT='finna-exam-change'
function read(){try{return localStorage.getItem(KEY)||''}catch{return ''}}
function subscribe(callback:()=>void){window.addEventListener(EVENT,callback);window.addEventListener('storage',callback);return()=>{window.removeEventListener(EVENT,callback);window.removeEventListener('storage',callback)}}
export function choosePreferredExam(id:string){try{localStorage.setItem(KEY,id)}catch{/* The exam can still be opened directly. */}window.dispatchEvent(new Event(EVENT))}
export function usePreferredExam(exams:Collection[]){const preferred=useSyncExternalStore(subscribe,read,()=>'' );return exams.find(e=>e.id===preferred)||exams.find(e=>e.id==='udc')||exams[0]||null}
