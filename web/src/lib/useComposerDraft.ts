import {useEffect,useRef,useState} from 'react'
import {reviewSession} from './review'
import {clearComposerDrafts,draftKey,emptyComposerFields,hasComposerDraft,readComposerDraft,writeComposerDraft,type ComposerFields} from './communityDrafts'
type Status='checking'|'ready'|'saved'|'restored'|'unavailable'
export function useComposerDraft(scope:string,enabled:boolean){
 const [fields,setFields]=useState<ComposerFields>(emptyComposerFields),[status,setStatus]=useState<Status>('checking')
 const value=useRef(fields),owner=useRef<string|null>(null),epoch=useRef(0),dirty=useRef(false),retry=useRef<{payload:string;key:string}>({payload:'',key:crypto.randomUUID()}),activeScope=useRef(scope)
 const persist=()=>{if(!owner.current)return;try{writeComposerDraft({version:1,owner:owner.current,scope,updated:Date.now(),fields:value.current,retry:retry.current});setStatus(hasComposerDraft(value.current)?'saved':'ready')}catch{setStatus('unavailable')}}
 useEffect(()=>{
  let active=true;const run=++epoch.current;owner.current=null;setStatus('checking')
  if(activeScope.current!==scope){activeScope.current=scope;dirty.current=false;value.current=emptyComposerFields();retry.current={payload:'',key:crypto.randomUUID()};setFields(value.current)}
  if(enabled)reviewSession().then(identity=>{
   if(!active||run!==epoch.current)return
   if(!identity.user_id)throw Error('Account identity is unavailable')
   owner.current=identity.user_id
   const saved=readComposerDraft(identity.user_id,scope)
   if(saved&&!dirty.current){value.current=saved.fields;retry.current=saved.retry;setFields(saved.fields);setStatus('restored')}
   else if(dirty.current)persist()
   else setStatus('ready')
  }).catch(()=>{if(active&&run===epoch.current)setStatus('unavailable')})
  const reset=()=>{++epoch.current;owner.current=null;dirty.current=false;value.current=emptyComposerFields();retry.current={payload:'',key:crypto.randomUUID()};setFields(value.current);setStatus('checking');clearComposerDrafts()}
  window.addEventListener('ism-auth-change',reset);window.addEventListener('ism-auth-expired',reset)
  return()=>{active=false;++epoch.current;owner.current=null;window.removeEventListener('ism-auth-change',reset);window.removeEventListener('ism-auth-expired',reset)}
 },[scope,enabled])
 function update(patch:Partial<ComposerFields>){dirty.current=true;value.current={...value.current,...patch};setFields(value.current);persist()}
 function clear(){dirty.current=false;value.current=emptyComposerFields();setFields(value.current);retry.current={payload:'',key:crypto.randomUUID()};try{if(owner.current)localStorage.removeItem(draftKey(owner.current,scope));setStatus('ready')}catch{setStatus('unavailable')}}
 function requestKey(payload:string){if(retry.current.payload!==payload){retry.current={payload,key:crypto.randomUUID()};persist()}return retry.current.key}
 return {fields,update,clear,requestKey,status}
}
