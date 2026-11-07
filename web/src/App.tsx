import { lazy, Suspense, useEffect, useState } from 'react'
const SharedTests=lazy(()=>import('./screens/SharedTests'))
const TestMaker=lazy(()=>import('./screens/TestMaker'))
const GoogleFinish=lazy(()=>import('./screens/GoogleFinish'))
const LearningCatalog=lazy(()=>import('./screens/LearningCatalog'))
const LearningCatalogAdmin=lazy(()=>import('./screens/LearningCatalogAdmin'))
const DiscoveryAdmin=lazy(()=>import('./screens/DiscoveryAdmin'))
const McqSolverReview=lazy(()=>import('./screens/McqSolverReview'))
const EditorialReview=lazy(()=>import('./screens/EditorialReview'))
import SessionNotice from './components/SessionNotice'
import MaterialReadingPanel from './components/MaterialReadingPanel'
import {routeModules,warmRoute} from './lib/routeModules'
import {RouteNavigation,RouteErrorBoundary,WorkspaceLoading} from './components/RouteWorkspace'
import {useExamScope,syncExamScope} from './lib/examScope'
import {hydrateDesk} from './lib/desk'
const DeskAdmin=lazy(()=>import('./screens/DeskAdmin'))
const DiscussionAdmin=lazy(()=>import('./screens/DiscussionAdmin'))
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import BottomBar from './components/BottomBar'
import Footer from './components/Footer'
import Header from './components/Header'
import { Card } from './components/ui'
const ResumedPractice=lazy(()=>import('./components/ResumedPractice'))
const DailyRevision=lazy(()=>import('./screens/DailyRevision'))
const Bank=lazy(routeModules.Bank)
const ExamPage=lazy(()=>import('./screens/ExamPage'))
const GroupBStudy=lazy(routeModules.GroupBStudy)
const Exams=lazy(routeModules.Exams)
const Mistakes=lazy(routeModules.Mistakes)
const MockRunner=lazy(routeModules.MockRunner)
const Results=lazy(routeModules.Results)
const Scoring=lazy(routeModules.Scoring)
const QuestionDetail=lazy(routeModules.QuestionDetail)
const StudyDesk=lazy(()=>import('./screens/StudyDesk'))
const Home=lazy(routeModules.Home)
const Feed=lazy(routeModules.Feed)
const StudyHome=lazy(routeModules.StudyHome)
const CreateHub=lazy(routeModules.CreateHub)
const Moderation=lazy(routeModules.Moderation)
const English=lazy(routeModules.English)
const Arithmetic=lazy(routeModules.Arithmetic)
const Library=lazy(routeModules.Library)
const LibrarySubject=lazy(routeModules.LibrarySubject)
const Atlas=lazy(()=>import('./screens/Atlas'))
const LibraryShelf=lazy(()=>import('./screens/LibraryShelf'))
const Mizo=lazy(routeModules.Mizo)
const Essay=lazy(routeModules.Essay)
const AccountRecovery=lazy(()=>import('./screens/AccountRecovery'))
const PaperWorkbench=lazy(()=>import('./screens/PaperWorkbench'))
const CurrentAffairsAdmin=lazy(()=>import('./screens/CurrentAffairsAdmin'))
const AccountSecurity=lazy(()=>import('./screens/AccountSecurity'))
const BankAdmin = lazy(() => import('./screens/BankAdmin'))
const Contribute = lazy(() => import('./screens/Contribute'))
const ContributionEditor = lazy(() => import('./screens/ContributionEditor'))
const ContributionDetail = lazy(() => import('./screens/ContributionDetail'))
const ContributorBoard = lazy(() => import('./screens/ContributorBoard'))
const ReviewNotifications = lazy(() => import('./screens/Inbox'))
const CommunityQuestions = lazy(() => import('./screens/CommunityQuestions'))
const Vocabulary=lazy(routeModules.Vocabulary)
const Profile=lazy(routeModules.Profile)
const TopicTrail=lazy(()=>import('./screens/TopicTrail'))
const TopicTrailAdmin=lazy(()=>import('./screens/TopicTrailAdmin'))
const More=lazy(()=>import('./screens/More'))
const Games=lazy(()=>import('./screens/Games'))
const GamePlayer=lazy(()=>import('./screens/Games').then(m=>({default:m.GamePlayer})))
const GlobalSearch=lazy(()=>import('./screens/GlobalSearch'))
const ExamCalendar=lazy(()=>import('./screens/ExamCalendar'))
const AvatarEditor=lazy(()=>import('./screens/AvatarEditor'))
const PaperViewer=lazy(routeModules.PaperViewer)
const AccountForm=lazy(routeModules.AccountForm)
const Billing=lazy(routeModules.Billing)
const Plans=lazy(routeModules.Plans)

/** Routes the shell links to but that are not built yet. Named explicitly
 *  rather than caught by `*`, so the page can say which phase owns it
 *  instead of pretending to be a 404. docs/PLAN.md has the order. */
const Rewards = lazy(()=>import('./screens/Rewards'))
const LearningBoard = lazy(()=>import('./screens/Rewards').then(m=>({default:m.LearningBoard})))

const CreatorProfile=lazy(()=>import('./screens/Creators'))
const CreatorDirectory=lazy(()=>import('./screens/Creators').then(m=>({default:m.CreatorDirectory})))
const CreatorSettings=lazy(()=>import('./screens/Creators').then(m=>({default:m.CreatorSettings})))
const Materials=lazy(()=>import('./screens/Materials'))
const MaterialReader=lazy(()=>import('./screens/Materials').then(m=>({default:m.MaterialReader})))
const CreatorHome=lazy(()=>import('./screens/ContentStudio').then(m=>({default:m.CreatorHome})))
const ContentEditor=lazy(()=>import('./screens/ContentStudio'))

const PLANNED: Record<string, { title: string; phase: string }> = {
}

function Planned() {
  const { pathname } = useLocation()
  const p = PLANNED[pathname]
  return (
    <div className="mx-auto max-w-shell px-6 py-16">
      <Card className="max-w-xl p-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
          {p ? p.phase : 'Not found'}
        </div>
        <h1 className="mt-2 font-display text-[28px] font-semibold">
          {p ? p.title : 'No such page'}
        </h1>
        <p className="mt-2 text-[15px] leading-relaxed text-secondary">
          {p
            ? 'Designed, not built yet. The build order is in docs/PLAN.md.'
            : 'That route does not exist.'}
        </p>
      </Card>
    </div>
  )
}

export default function App() {
  const [accountEpoch,setAccountEpoch]=useState(0)
  useEffect(()=>{const refresh=()=>setAccountEpoch(n=>n+1);window.addEventListener('ism-auth-change',refresh);return()=>window.removeEventListener('ism-auth-change',refresh)},[])
  useEffect(()=>{void hydrateDesk();const changed=()=>void hydrateDesk(true);window.addEventListener("ism-avatar-change",changed);return()=>window.removeEventListener("ism-avatar-change",changed)},[])
  const { pathname,search } = useLocation()
  const examScope=useExamScope()
  useEffect(()=>syncExamScope(search),[search])
  const scopedWorkspace= (pathname==='/' || /^\/(bank|group-b|library|exams|english|mizo|arithmetic|vocabulary|search|feed|essay|scoring)(\/|$)/.test(pathname))&&!pathname.includes('/mock')
  const landing = pathname === '/'
  const adminWorkspace = pathname === '/admin' || pathname.startsWith('/admin/bank')
  return (
    <div className="flex min-h-screen flex-col" onPointerOver={event=>{if(event.pointerType==='mouse'){const link=(event.target as Element).closest('a[href]');if(link)warmRoute((link as HTMLAnchorElement).href)}}} onFocus={event=>{const link=(event.target as Element).closest('a[href]');if(link)warmRoute((link as HTMLAnchorElement).href)}}>
      {!landing && !adminWorkspace && <Header />}
      <SessionNotice/>
      <main id="main-content" tabIndex={-1} className="flex-1 scroll-mt-32">
        <RouteErrorBoundary key={pathname+examScope}><Suspense fallback={<WorkspaceLoading/>}>
        <RouteNavigation/>{new URLSearchParams(search).has('resume_question')&&!adminWorkspace&&<ResumedPractice/>}<div key={`${accountEpoch}:${scopedWorkspace?examScope:'stable'}`} className={scopedWorkspace?'scope-workspace':undefined}><Routes>
          <Route path="/" element={<Home />} />
          <Route path="/google/finish" element={<GoogleFinish/>}/><Route path="/account/recovery" element={<AccountRecovery/>}/>
          <Route path="/materials" element={<Materials/>}/><Route path="/materials/:id" element={<MaterialReader/>}/>
          <Route path="/studio" element={<CreatorHome/>}/><Route path="/studio/new" element={<ContentEditor/>}/><Route path="/studio/:id" element={<ContentEditor/>}/><Route path="/create" element={<CreateHub/>}/><Route path="/inbox" element={<ReviewNotifications/>}/>
          <Route path="/trail" element={<TopicTrail/>}/><Route path="/trail/:id" element={<TopicTrail/>}/><Route path="/admin/topic-trail" element={<TopicTrailAdmin/>}/><Route path="/more" element={<More/>}/><Route path="/games" element={<Games/>}/><Route path="/games/:id" element={<GamePlayer/>}/><Route path="/duel" element={<Navigate to="/games" replace/>}/><Route path="/search" element={<GlobalSearch/>}/><Route path="/feed" element={<StudyHome />} /><Route path="/community" element={<Feed/>}/><Route path="/calendar" element={<ExamCalendar/>}/><Route path="/news" element={<ExamCalendar notices/>}/>
          <Route path="/editorial" element={<EditorialReview />} />
          <Route path="/admin/discovery" element={<DiscoveryAdmin/>}/><Route path="/current-affairs/manage" element={<CurrentAffairsAdmin/>}/>
          <Route path="/admin/mcq-solver" element={<McqSolverReview/>}/>
          <Route path="/paper-workbench" element={<PaperWorkbench/>}/>
          <Route path="/admin" element={<Navigate to="/admin/bank" replace />} />
          <Route path="/admin/bank" element={<BankAdmin />} />
          <Route path="/review" element={<Navigate to="/admin/bank?tab=review" replace />} />
          <Route path="/contribute" element={<Contribute />} />
          <Route path="/contribute/new" element={<ContributionEditor />} />
          <Route path="/contribute/notifications" element={<ReviewNotifications />} />
          <Route path="/notifications" element={<ReviewNotifications/>}/>
          <Route path="/contributions/:id" element={<ContributionDetail />} />
          <Route path="/contributions/:id/edit" element={<ContributionEditor />} />
          <Route path="/community/contributors" element={<ContributorBoard />} />
          <Route path="/community/questions" element={<CommunityQuestions />} />
          <Route path="/website-bank" element={<CommunityQuestions />} />
          <Route path="/important-days" element={<LearningCatalog kind="day"/>} />
          <Route path="/practice-sets" element={<LearningCatalog kind="practice"/>} />
          <Route path="/learning/manage" element={<LearningCatalogAdmin/>} />
          <Route path="/admin/desks" element={<DeskAdmin />} />
          <Route path="/admin/discussions" element={<DiscussionAdmin />} />
          <Route path="/admin/moderation" element={<Moderation />} />
          <Route path="/bank" element={<Bank />} />
          <Route path="/bank/:id" element={<QuestionDetail />} />
          <Route path="/library" element={<Library />} />
          <Route path="/atlas" element={<Atlas />} />
          <Route path="/library/topics/:shelfId" element={<LibraryShelf />} />
          <Route path="/library/subjects/:subjectId" element={<LibrarySubject />} />
          <Route path="/mizo" element={<Mizo />} />
          <Route path="/essay" element={<Essay />} />
          <Route path="/group-b" element={<GroupBStudy />} />
          <Route path="/exams" element={<Exams />} />
          <Route path="/exams/:id" element={<ExamPage />} />
          <Route path="/exams/:id/paper" element={<PaperViewer />} />
          <Route path="/exams/:id/mock" element={<MockRunner />} />
          <Route path="/tests" element={<SharedTests/>}/><Route path="/tests/make" element={<TestMaker/>}/><Route path="/tests/:testId" element={<SharedTests/>}/><Route path="/tests/:testId/take" element={<MockRunner/>}/>
          <Route path="/results/:mockId" element={<Results />} />
          <Route path="/revision" element={<DailyRevision/>}/>
          <Route path="/mistakes" element={<Mistakes />} />
          <Route path="/desk" element={<StudyDesk />} />
          <Route path="/desk/:deskId" element={<StudyDesk />} />
          <Route path="/english" element={<English />} />
          <Route path="/arithmetic" element={<Arithmetic />} />
          <Route path="/vocabulary" element={<Vocabulary />} />
          <Route path="/account/security" element={<Suspense fallback={<p className="p-8">Loading security settings…</p>}><AccountSecurity/></Suspense>}/>
          <Route path="/rewards" element={<Rewards/>}/><Route path="/board" element={<LearningBoard/>}/>
          <Route path="/profile" element={<Profile />} /><Route path="/avatar" element={<AvatarEditor/>}/><Route path="/profile/avatar" element={<AvatarEditor/>}/>
          <Route path="/creators" element={<CreatorDirectory/>}/>
          <Route path="/creators/settings" element={<CreatorSettings/>}/>
          <Route path="/creators/:id" element={<CreatorProfile/>}/>
          <Route path="/login" element={<AccountForm mode="login" />} />
          <Route path="/join" element={<AccountForm mode="join" />} />
          <Route path="/plans" element={<Plans />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/scoring" element={<Scoring />} />
          <Route path="/exams/:id/*" element={<Planned />} />
          {Object.keys(PLANNED).map((path) => (
            <Route key={path} path={path} element={<Planned />} />
          ))}
          <Route path="*" element={<Planned />} />
        </Routes></div>
        </Suspense></RouteErrorBoundary>
      </main>
      {!adminWorkspace && <MaterialReadingPanel/>}
      {!landing && !adminWorkspace && <Footer />}
      {!landing && !adminWorkspace && <BottomBar />}
    </div>
  )
}
