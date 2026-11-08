/** Shared destinations keep desktop and phone navigation consistent. */
export const PRIMARY_NAV = [
  {to:'/feed',label:'Home',icon:'home'},
  {to:'/exams',label:'Exams',icon:'exam'},
  {to:'/library',label:'Library',icon:'library'},
  {to:'/create',label:'Create',icon:'create'},
  {to:'/more',label:'More',icon:'more'},
] as const
export function primarySection(path:string){
  if(/^\/(feed|desk|revision|mistakes|results)(\/|$)/.test(path))return '/feed'
  if(/^\/(exams|group-b)(\/|$)/.test(path))return '/exams'
  if(/^\/(library|bank|website-bank|important-days|practice-sets|materials|atlas|english|mizo|arithmetic|vocabulary|essay|search)(\/|$)/.test(path)||path==='/community/questions')return '/library'
  if(/^\/(create|studio|contribute|contributions|learning\/manage)(\/|$)/.test(path))return '/create'
  return '/more'
}
export function focusedSession(path:string){return /^\/(games|trail)\/[^/]+$/.test(path)||/^\/exams\/[^/]+\/mock$/.test(path)}
