import { mobileScreen } from './lib/navigation'
import { adminTabHref } from './lib/adminNavigation'
import { lazy, Suspense, useEffect, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom'
import SessionNotice from './components/SessionNotice'
import SiteNotice from './components/SiteNotice'
import { AudienceNotice } from './components/AgeCategoryCheck'
import MaterialReadingPanel from './components/MaterialReadingPanel'
import SelectionTray from './components/SelectionTray'
import { routeModules, warmRoute } from './lib/routeModules'
import { RouteNavigation, RouteErrorBoundary, WorkspaceLoading } from './components/RouteWorkspace'
import { useExamScope, syncExamScope } from './lib/examScope'
import { hydrateDesk } from './lib/desk'
import BottomBar from './components/BottomBar'
import Footer from './components/Footer'
import Header from './components/Header'
import RouteBackBar from './components/RouteBackBar'
import HelpDrawer from './components/HelpDrawer'
import { Card } from './components/ui'

const ResumedPractice = lazy(() => import('./components/ResumedPractice'))
const SiteIndex = lazy(() => import('./screens/SiteIndex'))
const Guides = lazy(() => import('./screens/Guides'))
const PersonalVault = lazy(() => import('./screens/PersonalVault'))
const Practice = lazy(() => import('./screens/Practice'))
const SharedTests = lazy(() => import('./screens/SharedTests'))
const TestMaker = lazy(() => import('./screens/TestMaker'))
const GoogleFinish = lazy(() => import('./screens/GoogleFinish'))
const AccountHub = lazy(() => import('./screens/AccountHub'))
const PolicyPages = lazy(() => import('./screens/PolicyPages'))
const Bank = lazy(routeModules.Bank)
const ExamPage = lazy(() => import('./screens/ExamPage'))
const Exams = lazy(routeModules.Exams)
const Papers = lazy(() => import('./screens/Papers'))
const Chronicle = lazy(() => import('./screens/Chronicle'))
const Onboarding = lazy(() => import('./screens/Onboarding'))
const Revise = lazy(() => import('./screens/Revise'))
const MockRunner = lazy(routeModules.MockRunner)
const Results = lazy(routeModules.Results)
const QuestionDetail = lazy(routeModules.QuestionDetail)
const StudyDesk = lazy(() => import('./screens/StudyDesk'))
const Feed = lazy(routeModules.Feed)
const StudyHome = lazy(routeModules.StudyHome)
const CreateHub = lazy(routeModules.CreateHub)
const Library = lazy(routeModules.Library)
const LibrarySubject = lazy(routeModules.LibrarySubject)
const LibraryShelf = lazy(() => import('./screens/LibraryShelf'))
const Atlas = lazy(() => import('./screens/Atlas'))
const BankAdmin = lazy(() => import('./screens/BankAdmin'))
const ContributionEditor = lazy(() => import('./screens/ContributionEditor'))
const ContributionDetail = lazy(() => import('./screens/ContributionDetail'))
const Contribute = lazy(() => import('./screens/Contribute'))
const Inbox = lazy(() => import('./screens/Inbox'))
const CommunityQuestions = lazy(() => import('./screens/CommunityQuestions'))
const Profile = lazy(routeModules.Profile)
const Games = lazy(() => import('./screens/Games'))
const GamePlayer = lazy(() => import('./screens/Games').then((m) => ({ default: m.GamePlayer })))
const QuestGame = lazy(() => import('./screens/QuestGame'))
const BlockBlastGame = lazy(() => import('./screens/BlockBlastGame'))
const TopicTrail = lazy(() => import('./screens/TopicTrail'))
const Stats = lazy(() => import('./screens/Stats'))
const GlobalSearch = lazy(() => import('./screens/GlobalSearch'))
const ExamCalendar = lazy(() => import('./screens/ExamCalendar'))
const AvatarEditor = lazy(() => import('./screens/AvatarEditor'))
const PaperViewer = lazy(routeModules.PaperViewer)
const AccountForm = lazy(routeModules.AccountForm)
const Billing = lazy(routeModules.Billing)
const Plans = lazy(routeModules.Plans)
const Rewards = lazy(() => import('./screens/Rewards'))
const Leaderboard = lazy(() => import('./screens/Leaderboard'))
const CreatorProfile = lazy(() => import('./screens/Creators'))
const CreatorDirectory = lazy(() => import('./screens/Creators').then((m) => ({ default: m.CreatorDirectory })))
const CreatorSettings = lazy(() => import('./screens/Creators').then((m) => ({ default: m.CreatorSettings })))
const Materials = lazy(() => import('./screens/Materials'))
const MaterialReader = lazy(() => import('./screens/Materials').then((m) => ({ default: m.MaterialReader })))
const ContentEditor = lazy(() => import('./screens/ContentStudio'))
const CreatorHome = lazy(() => import('./screens/ContentStudio').then((m) => ({ default: m.CreatorHome })))
const Vocabulary = lazy(() => import('./screens/Vocabulary'))
const Essay = lazy(() => import('./screens/Essay'))
const ContributorBoard = lazy(() => import('./screens/ContributorBoard'))
const Arithmetic = lazy(() => import('./screens/Arithmetic'))
const English = lazy(() => import('./screens/English'))
const Mizo = lazy(() => import('./screens/Mizo'))
const GroupBStudy = lazy(() => import('./screens/GroupBStudy'))

function NotFound() {
  return (
    <div className="mx-auto max-w-[850px] px-6 py-16">
      <Card className="max-w-xl p-8">
        <div className="font-mono text-xs uppercase tracking-[0.1em] text-muted">404 · Not found</div>
        <h1 className="mt-2 text-xl font-bold text-ink">Page not found</h1>
        <p className="mt-2 text-base leading-relaxed text-secondary">
          That route does not exist or may have moved. Jump back to your study home or browse every active page.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link to="/home" className="finna-btn">
            Go to Study Home →
          </Link>
          <Link to="/index" className="finna-btn finna-btn-quiet">
            Browse all pages
          </Link>
        </div>
      </Card>
    </div>
  )
}

function PracticeRoute() {
  const { mode } = useParams()
  if (mode === 'build') return <TestMaker />
  if (!mode) return <Practice />
  return <NotFound />
}

function BankRoute() {
  const { id } = useParams()
  return id ? <QuestionDetail /> : <Bank />
}

function MaterialsRoute() {
  const { id } = useParams()
  return id ? <MaterialReader /> : <Materials />
}

/** `/news` was the notices view of the calendar. V.14 deleted that route, and
 *  `notices` is a prop nothing passed — so the notices view became unreachable
 *  rather than consolidated. It is now a query mode on `/calendar`. */
function CalendarRoute() {
  const { search } = useLocation()
  return <ExamCalendar notices={new URLSearchParams(search).get('view') === 'notices'} />
}

/** Topic Trail folded into the one Play hub (§0.12). Both `/games?mode=trail`
 *  (pack chooser) and `/games/:id?mode=trail` (active run) render TopicTrail. */
function GamesRoute() {
  const { id } = useParams()
  const { search } = useLocation()
  if (new URLSearchParams(search).get('mode') === 'trail') return <TopicTrail />
  if (!id) return <Games />
  return <GamePlayer />
}

function CreatorsRoute() {
  const { id } = useParams()
  if (!id) return <CreatorDirectory />
  if (id === 'settings') return <CreatorSettings />
  return <CreatorProfile />
}

function StudioRoute() {
  const { id } = useParams()
  return id ? <ContentEditor /> : <CreatorHome />
}

function CommunityRoute() {
  const { sub } = useParams()
  if (!sub) return <Feed />
  if (sub === 'questions') return <CommunityQuestions />
  if (sub === 'contributors') return <ContributorBoard />
  return <NotFound />
}

function ProfileRoute() {
  const { section } = useParams()
  if (!section) return <Profile />
  if (section === 'avatar') return <AvatarEditor />
  if (section === 'rewards') return <Rewards />
  return <NotFound />
}

function CreateRoute() {
  const { section } = useParams()
  if (!section) return <CreateHub />
  if (section === 'new') return <ContributionEditor />
  if (section === 'submissions') return <Contribute />
  return <NotFound />
}

function AuthRoute() {
  const { pathname } = useLocation()
  if (pathname === '/join') return <AccountForm mode="join" />
  if (pathname === '/google/finish') return <GoogleFinish />
  return <AccountForm mode="login" />
}

function BillingRoute() {
  const { pathname } = useLocation()
  return pathname === '/billing' ? <Billing /> : <Plans />
}

function AdminRoute() {
  const { section } = useParams()
  // One addressing scheme for the console (§VIII.6). `/admin/ops` and `/admin/users`
  // stay as redirects so existing bookmarks keep working, rather than remaining a
  // second way to address a section that every caller had to special-case.
  if (section === 'ops' || section === 'users') return <Navigate to={adminTabHref(section)} replace />
  if (section === 'bank') return <BankAdmin />
  return <NotFound />
}

function ContributionRoute() {
  const { id, action } = useParams()
  if (action === 'edit') return <ContributionEditor />
  if (!action && id) return <ContributionDetail />
  return <NotFound />
}

function LibraryScopeRoute() {
  const { kind } = useParams()
  if (kind === 'topics') return <LibraryShelf />
  if (kind === 'subjects') return <LibrarySubject />
  return <NotFound />
}

const SUBJECT_MODULE_SLUGS = new Set(['english', 'mathematics', 'reasoning', 'gk-gs', 'mizo'])

function ExamSubRoute({ subject = false }: { subject?: boolean }) {
  const { id = '', sub } = useParams()
  const { search } = useLocation()
  if (subject && !sub && !SUBJECT_MODULE_SLUGS.has(id.replace(/^subject-/, ''))) {
    return <Navigate to={{ pathname: `/library/subjects/${encodeURIComponent(id)}`, search }} replace />
  }
  if (sub === 'paper') return <PaperViewer />
  if (sub === 'mock') return <MockRunner />
  if (!sub) return <ExamPage isSubjectRoute={subject} />
  return <NotFound />
}

function TestsRoute() {
  const { testId, action } = useParams()
  const { search } = useLocation()
  if (testId === 'make') return <Navigate to={{ pathname: '/practice/build', search }} replace />
  if (action === 'take') return <MockRunner />
  if (!action) return <SharedTests />
  return <NotFound />
}

function TrailLegacyRedirect() {
  const { id } = useParams()
  return <Navigate to={id ? `/games/${encodeURIComponent(id)}?mode=trail` : '/games?mode=trail'} replace />
}

function ConsolidatedRedirect({ target }: { target: string }) {
  const { search, hash } = useLocation()
  const params = new URLSearchParams(search)
  if (target === '/revise?tab=queue') {
    params.set('tab', 'queue')
    return <Navigate to={{ pathname: '/revise', search: '?' + params.toString(), hash }} replace />
  }
  if (target === '/revise') {
    if (params.get('session')?.startsWith('rev_')) params.set('tab', 'legacy')
    else {
      params.delete('session')
      params.delete('tab')
    }
    return <Navigate to={{ pathname: '/revise', search: params.size ? '?' + params.toString() : '', hash }} replace />
  }
  if (target === '/chronicle?view=list') {
    if (!params.has('view')) params.set('view', 'list')
    return <Navigate to={{ pathname: '/chronicle', search: '?' + params.toString(), hash }} replace />
  }
  if (target === '/games?mode=duel') {
    params.set('mode', 'duel')
    return <Navigate to={{ pathname: '/games', search: '?' + params.toString(), hash }} replace />
  }
  return <Navigate to={{ pathname: target, search, hash }} replace />
}

export default function App() {
  const [accountEpoch, setAccountEpoch] = useState(0)
  useEffect(() => {
    const refresh = () => setAccountEpoch((n) => n + 1)
    window.addEventListener('ism-auth-change', refresh)
    return () => window.removeEventListener('ism-auth-change', refresh)
  }, [])
  useEffect(() => {
    void hydrateDesk()
    const changed = () => void hydrateDesk(true)
    window.addEventListener('ism-avatar-change', changed)
    return () => window.removeEventListener('ism-avatar-change', changed)
  }, [])
  const { pathname, search, hash } = useLocation()
  const examScope = useExamScope()
  useEffect(() => syncExamScope(search), [search])
  const scopedWorkspace =
    (pathname === '/' || /^\/(home|bank|past-papers|library|exams|practice|guides|search|vocabulary)(\/|$)/.test(pathname)) &&
    !pathname.includes('/mock')
  const adminWorkspace =
    pathname === '/admin/ops' || pathname === '/admin/users' || pathname.startsWith('/admin/bank')
  const authWorkspace = pathname === '/login' || pathname === '/join'
  const hideChrome = adminWorkspace || authWorkspace

  return (
    <div
      className="finna-app flex min-h-screen flex-col"
      data-mobile-screen={mobileScreen(pathname)}
      onPointerOver={(event) => {
        if (event.pointerType === 'mouse') {
          const link = (event.target as Element).closest('a[href]')
          if (link) warmRoute((link as HTMLAnchorElement).href)
        }
      }}
      onFocus={(event) => {
        const link = (event.target as Element).closest('a[href]')
        if (link) warmRoute((link as HTMLAnchorElement).href)
      }}
    >
      <SiteNotice />
      {!hideChrome && <Header />}
      {!hideChrome && <RouteBackBar />}
      <SessionNotice />
      {!authWorkspace && <AudienceNotice />}
      <main id="main-content" tabIndex={-1} className="flex-1 scroll-mt-32">
        <RouteErrorBoundary key={pathname + examScope}>
          <Suspense fallback={<WorkspaceLoading />}>
            <RouteNavigation />
            {new URLSearchParams(search).has('resume_question') && !adminWorkspace && <ResumedPractice />}
            <div
              key={`${accountEpoch}:${scopedWorkspace ? examScope : 'stable'}`}
              className={'finna-screen' + (scopedWorkspace ? ' scope-workspace' : '')}
            >
              {/* Consolidated route table (37 routes, <= 40 target, §VII.14 / Phase V.14). */}
              <Routes>
                <Route path="/" element={<Navigate to={{ pathname: '/home', search, hash }} replace />} />
                <Route path="/home" element={<StudyHome />} />
                <Route path="/index" element={<SiteIndex />} />
                <Route path="/guides/:slug?" element={<Guides />} />
                <Route path="/practice/:mode?" element={<PracticeRoute />} />
                <Route path="/bank/:id?" element={<BankRoute />} />
                <Route path="/past-papers" element={<Papers />} />
                <Route path="/exams" element={<Exams />} />
                <Route path="/exams/:id/:sub?" element={<ExamSubRoute />} />
                <Route path="/subjects/:id/:sub?" element={<ExamSubRoute subject />} />
                <Route path="/tests/:testId?/:action?" element={<TestsRoute />} />
                <Route path="/results/:mockId" element={<Results />} />
                <Route path="/library" element={<Library />} />
                <Route path="/library/:kind/:shelfId" element={<LibraryScopeRoute />} />
                <Route path="/vocabulary" element={<Vocabulary />} />
                <Route path="/essay" element={<Essay />} />
                <Route path="/english" element={<English />} />
                <Route path="/arithmetic" element={<Arithmetic />} />
                <Route path="/mizo" element={<Mizo />} />
                <Route path="/group-b" element={<GroupBStudy />} />
                <Route path="/revise" element={<Revise />} />
                <Route path="/atlas/:chapter?" element={<Atlas />} />
                <Route path="/chronicle" element={<Chronicle />} />
                {/* Stats routes its own sub-pages. §VII.14 proposed demoting it
                    to a Home view; V.14 removed the route without doing that,
                    leaving a live API and a shipping mobile section unreachable
                    from the web. Restored until the demotion is actually built. */}
                <Route path="/stats/*" element={<Stats />} />
                <Route path="/calendar" element={<CalendarRoute />} />
                <Route path="/desk/:deskId?" element={<StudyDesk />} />
                <Route path="/vault" element={<PersonalVault />} />
                <Route path="/vault/share/:token" element={<PersonalVault />} />
                <Route path="/games/quest" element={<QuestGame />} />
                <Route path="/games/blocks" element={<BlockBlastGame />} />
                <Route path="/games/:id?" element={<GamesRoute />} />
                <Route path="/search" element={<GlobalSearch />} />
                <Route path="/community/:sub?" element={<CommunityRoute />} />
                <Route path="/materials/:id?" element={<MaterialsRoute />} />
                <Route path="/studio/:id?" element={<StudioRoute />} />
                <Route path="/create/:section?" element={<CreateRoute />} />
                <Route path="/contributions/:id/:action?" element={<ContributionRoute />} />
                <Route path="/creators/:id?" element={<CreatorsRoute />} />
                <Route path="/inbox" element={<Inbox />} />
                <Route path="/profile/:section?" element={<ProfileRoute />} />
                <Route path="/account/:section?" element={<AccountHub />} />
                <Route path="/onboarding" element={<Onboarding />} />
                <Route path="/login" element={<AuthRoute />} />
                <Route path="/join" element={<AuthRoute />} />
                <Route path="/google/finish" element={<AuthRoute />} />
                <Route path="/plans" element={<BillingRoute />} />
                <Route path="/billing" element={<BillingRoute />} />
                <Route path="/policies/:page" element={<PolicyPages />} />
                <Route path="/admin/:section" element={<AdminRoute />} />
                {/* Consolidated legacy bookmarks — preserve parameters instead of 404ing */}
                <Route path="/mistakes" element={<ConsolidatedRedirect target="/revise?tab=queue" />} />
                <Route path="/revision" element={<ConsolidatedRedirect target="/revise" />} />
                <Route path="/important-days" element={<ConsolidatedRedirect target="/chronicle?view=list" />} />
                <Route path="/duel" element={<ConsolidatedRedirect target="/games?mode=duel" />} />
                <Route path="/trail/:id?" element={<TrailLegacyRedirect />} />
                <Route path="/rewards" element={<ConsolidatedRedirect target="/profile/rewards" />} />
                <Route path="/board" element={<Leaderboard />} />
                <Route path="/notifications" element={<ConsolidatedRedirect target="/inbox" />} />
                <Route path="/contribute" element={<ConsolidatedRedirect target="/create/submissions" />} />
                <Route path="/contribute/new" element={<ConsolidatedRedirect target="/create/new" />} />
                <Route path="/website-bank" element={<ConsolidatedRedirect target="/community/questions" />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </div>
          </Suspense>
        </RouteErrorBoundary>
      </main>
      {!hideChrome && <SelectionTray />}
      {!hideChrome && <MaterialReadingPanel />}
      {!hideChrome && <HelpDrawer />}
      {!hideChrome && <Footer />}
      {!hideChrome && <BottomBar />}
    </div>
  )
}
