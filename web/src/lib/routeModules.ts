/** Shared route loaders let keyboard/pointer intent warm code, never user data. */
export const routeModules={
  GroupBStudy:()=>import('../screens/GroupBStudy'),
  Bank:()=>import('../screens/Bank'),Exams:()=>import('../screens/Exams'),ExamPage:()=>import('../screens/ExamPage'),
  Mistakes:()=>import('../screens/Mistakes'),MockRunner:()=>import('../screens/MockRunner'),Results:()=>import('../screens/Results'),
  Scoring:()=>import('../screens/Scoring'),QuestionDetail:()=>import('../screens/QuestionDetail'),Home:()=>import('../screens/Home'),
  Feed:()=>import('../screens/Feed'),Moderation:()=>import('../screens/Moderation'),English:()=>import('../screens/English'),
  Arithmetic:()=>import('../screens/Arithmetic'),Library:()=>import('../screens/Library'),LibrarySubject:()=>import('../screens/LibrarySubject'),
  Mizo:()=>import('../screens/Mizo'),Essay:()=>import('../screens/Essay'),Vocabulary:()=>import('../screens/Vocabulary'),
  Profile:()=>import('../screens/Profile'),PaperViewer:()=>import('../screens/PaperViewer'),
  AccountForm:()=>import('../screens/Account').then(m=>({default:m.AccountForm})),
  Billing:()=>import('../screens/Account').then(m=>({default:m.Billing})),
  Plans:()=>import('../screens/Account').then(m=>({default:m.Plans})),
  StudyDesk:()=>import('../screens/StudyDesk'),Games:()=>import('../screens/Games'),
  GlobalSearch:()=>import('../screens/GlobalSearch'),LibraryShelf:()=>import('../screens/LibraryShelf'),
}
const warmed=new Set<string>()
export function routeModule(path:string):keyof typeof routeModules|null {
  if(path==='/')return 'Home'
  if(/^\/bank\/[^/]+$/.test(path))return 'QuestionDetail'
  if(/^\/exams\/[^/]+\/mock$/.test(path))return 'MockRunner'
  if(/^\/exams\/[^/]+\/paper(?:\/|$)/.test(path))return 'PaperViewer'
  if(/^\/results\/[^/]+$/.test(path))return 'Results'
  if(/^\/exams\/[^/]+$/.test(path))return 'ExamPage'
  if(/^\/library\/topics\/[^/]+$/.test(path))return 'LibraryShelf'
  if(/^\/library\/subjects\//.test(path))return 'LibrarySubject'
  const routes:Record<string,keyof typeof routeModules>={'/group-b':'GroupBStudy','/bank':'Bank','/exams':'Exams','/library':'Library','/english':'English','/mizo':'Mizo','/essay':'Essay','/arithmetic':'Arithmetic','/feed':'Feed','/desk':'StudyDesk','/profile':'Profile','/games':'Games','/vocabulary':'Vocabulary','/search':'GlobalSearch','/login':'AccountForm','/join':'AccountForm','/plans':'Plans','/billing':'Billing','/mistakes':'Mistakes','/scoring':'Scoring'}
  return routes[path]||null
}
export function warmRoute(href:string) {
  const connection=(navigator as Navigator&{connection?:{saveData?:boolean;effectiveType?:string}}).connection
  if(connection?.saveData||/^(slow-)?2g$/.test(connection?.effectiveType||''))return
  let url:URL;try{url=new URL(href,window.location.href)}catch{return}
  if(url.origin!==window.location.origin)return
  const name=routeModule(url.pathname)
  if(!name||warmed.has(name))return
  warmed.add(name)
  void routeModules[name]().catch(()=>warmed.delete(name))
}
