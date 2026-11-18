/** Destinations and the phone hierarchy come from Finna Mobile.dc.html. */
export const PRIMARY_NAV = [
 {to:'/feed',label:'Home',icon:'home'},
 {to:'/exams',label:'Exams',icon:'exam'},
 {to:'/library',label:'Library',icon:'library'},
 {to:'/desk',label:'Desk',icon:'desk'},
 {to:'/profile',label:'Me',icon:'profile'},
] as const
export function primarySection(path:string){
 if(/^\/desk(\/|$)/.test(path))return '/desk'
 if(/^\/(feed|community)(\/|$)/.test(path)&&path!=='/community/questions')return '/feed'
 if(path==='/onboarding')return '/exams'
 if(/^\/(exams|group-b)(\/|$)/.test(path))return '/exams'
 if(/^\/(library|bank|past-papers|website-bank|important-days|practice-sets|materials|atlas|chronicle|stats|english|mizo|arithmetic|vocabulary|revise|revision|mistakes|essay|search)(\/|$)/.test(path)||path==='/community/questions')return '/library'
 return '/profile'
}
export function focusedSession(path:string,search=""){return (path==="/revise"||path==="/onboarding")&&new URLSearchParams(search).has("session")|| /^\/(games|trail)\/[^/]+$/.test(path)||/^\/exams\/[^/]+\/mock$/.test(path)||/^\/tests\/[^/]+\/take$/.test(path)}
export function mobileScreen(path:string){
 if(path==='/feed')return 'home'
 if(path==='/community')return 'feed'
 if(/^\/exams\/[^/]+\/mock$|^\/tests\/[^/]+\/take$/.test(path))return 'mock-player'
 if(path.startsWith('/results/'))return 'mock-result'
 if(path==='/tests/make')return 'mock-builder'
 if(path.startsWith('/exams/')||path==='/group-b')return 'exam-detail'
 if(path==='/exams')return 'exams'
 if(path==='/library')return 'library'
 if(/^\/(english|arithmetic|mizo|vocabulary|essay|library\/)/.test(path))return 'module'
 if(path==='/bank')return 'practice'
 if(path.startsWith('/bank/'))return 'question'
 if(path.startsWith('/desk'))return 'desk'
 if(path==='/inbox')return 'inbox'
 if(path.startsWith('/creators/'))return 'creator'
 if(path.startsWith('/games/'))return 'game-player'
 if(path==='/games')return 'games'
 if(path==='/profile')return 'me'
 if(path.startsWith('/account/'))return 'settings'
 if(path==='/login'||path==='/join'||path==='/google/finish')return 'sign-in'
 if(path==='/onboarding')return 'check-in'
 if(path==='/revise')return 'revise'
 if(path==='/revision'||path==='/mistakes')return 'saved'
 return path.split('/')[1]||'landing'
}
export function mobileTitle(path:string){return ({'check-in':'Exam check-in',home:'My exam',feed:'Feed',exams:'Exams',library:'Library',module:'Modules','exam-detail':'Your exam',practice:'Practice',question:'Question detail',desk:'Study desk',inbox:'Inbox',creator:'Creator profile',games:'Play','game-player':'Game',me:'Me',settings:'Settings','sign-in':'Sign in',saved:'Saved',revise:'Revise','mock-builder':'Mock tests','mock-player':'Mock test','mock-result':'Your result',atlas:'Atlas',chronicle:'Chronicle',stats:'Stats',create:'Create',more:'More','past-papers':'Past papers',rewards:'Rewards',tests:'Mock tests'} as Record<string,string>)[mobileScreen(path)]||'Finna'}
