// Offline UI regression: source scope, tab compatibility and guarded answer context.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const root = process.cwd(), wr = require('node:module').createRequire(root + '/web/package.json');
const React = wr('react'), ts = wr('typescript');
const rendererRoot = process.argv[2] || root + '/../india-study-map/web';
const reactPath = require.resolve('react', { paths: [rendererRoot] });
require.cache[reactPath] = { id: reactPath, filename: reactPath, loaded: true, exports: React };
const { act, create } = require(require.resolve('react-test-renderer', { paths: [rendererRoot] }));
let params = new URLSearchParams(), tree, requests = [], answers = [], defer = false, pending = [];
const cache = new Map(), listeners = new Set(), storage = new Map();
let identity = { userId: 'test-account' };
const identityListeners = new Set();
const events = new EventTarget();
global.window = { setTimeout, clearTimeout, addEventListener: (...args) => events.addEventListener(...args), removeEventListener: (...args) => events.removeEventListener(...args), dispatchEvent: event => events.dispatchEvent(event) };
global.localStorage = { getItem: k => storage.get(k) ?? null, setItem: (k, v) => storage.set(k, v) };
function change(next) { params = new URLSearchParams(typeof next === 'function' ? next(params) : next); for (const fn of listeners) fn(); }
const question = { id: 'test-question', question: 'Source-bound question', type: 'mcq', answer_source: 'official' };
const page = { items: [question], total: 50, limit: 25, offset: 0 };
const catalogCollections = Array.from({length:8}, (_,i)=>({id:i?'exam-'+i:'ldc',title:i?'Other exam '+i:'Lower Division Clerk (LDC)',kind:'exam',visibility:'public',questions:100,scorable:80}));
const api = {
 listTaxonomy: async () => [
  {subject_id:'english',subject:'English',topic_id:'english:usage',topic:'Usage',questions:10},
  {subject_id:'computer-science',subject:'Computer Science',topic_id:'computer-science:algorithms',topic:'Algorithms',questions:10},
 ],
 listCollections: async () => catalogCollections,
 isLaterExamCollection: () => false,
 getExamBookmarks: async () => ({collection_ids:['ldc']}),
 getExamProgress: async () => [],
 listQuestions: async p => { requests.push(p); return defer ? new Promise(resolve => pending.push(resolve)) : page; },
 submitAnswer: async (...p) => { answers.push(p); return { correct: true }; },
};
function load(file) {
 file = path.resolve(file); if (cache.has(file)) return cache.get(file);
 if (file.endsWith('.json')) return JSON.parse(fs.readFileSync(file, 'utf8'));
 const mod = { exports: {} }; cache.set(file, mod.exports);
 const source = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2020 } }).outputText;
 new Function('module', 'exports', 'require', source)(mod, mod.exports, id => {
  if (id === 'react-router-dom') return {
   Link: ({ children, to, ...props }) => React.createElement('a', { ...props, href: to, onClick: () => change(to.replace(/^\?/, '')) }, children),
   useSearchParams: () => { React.useSyncExternalStore(fn => { listeners.add(fn); return () => listeners.delete(fn); }, () => params.toString()); return [params, change]; },
  };
  if (id.endsWith('/desk')) return { getDeskSync: () => identity, subscribeDesk: fn => { identityListeners.add(fn); return () => identityListeners.delete(fn); } };
  if (id.endsWith('/api')) return api;
  if (id.endsWith('/StudyQuestionCard')) return { default: props => React.createElement('article', { 'data-question': props.q.id }, React.createElement('button', { onClick: () => props.onPick(2) }, 'Answer fixture')) };
  if (id.endsWith('/Pagination')) return { default: () => null };
  if (id.endsWith('.css')) return {};
  if (id.startsWith('.') || id.startsWith('@/')) {
   const base = id.startsWith('@/') ? path.join(root, 'web/src', id.slice(2)) : path.resolve(path.dirname(file), id);
   return load(['', '.tsx', '.ts'].map(ext => base + ext).find(p => fs.existsSync(p) && fs.statSync(p).isFile()));
  }
  return wr(id);
 }); cache.set(file, mod.exports); return mod.exports;
}
const guide = load(root + '/web/src/data/exam-guides/mes.json');
const { archiveFor, sourcePaperId } = load(root + '/web/src/lib/examGuides.ts');
const { ExamGuidePage } = load(root + '/web/src/components/exam-guide/ExamGuidePage.tsx');
const { GuideQuestionBrowser } = load(root + '/web/src/components/exam-guide/GuideQuestionBrowser.tsx');
const Exams = load(root + '/web/src/screens/Exams.tsx').default;
const sleep = () => new Promise(resolve => setTimeout(resolve, 15));
const output = () => JSON.stringify(tree.toJSON());
async function mount(component) { await act(async () => { tree?.unmount(); tree = create(component); await sleep(); }); }
async function update(next) { await act(async () => { change(next); await sleep(); }); }
(async () => {
 params = new URLSearchParams('scheme=regulations-2013&branch=computer&tab=Recall');
 await mount(React.createElement(ExamGuidePage, { guide }));
 assert.ok(output().includes('Show syllabus checklist'), 'Old Recall links remain recall prompts');
 const nav = tree.root.findByProps({ 'aria-label': guide.title + ' module views' });
 assert.deepEqual(nav.findAllByType('a').map(a => a.children.join('')), ['Overview', 'Browse', 'Subjects', 'Papers', 'Practice', 'Progress']);
 const header = tree.root.findByType('header');
 await act(async () => nav.findAllByType('a').find(a => a.children.join('') === 'Subjects').props.onClick());
 assert.equal(tree.root.findByType('header'), header, 'Tab changes preserve the header and selectors');
 const boxes = tree.root.findAllByProps({ type: 'checkbox' }); assert.ok(boxes.length > 0);
 await act(async () => boxes[0].props.onChange({ target: { checked: true } }));
 assert.ok([...storage.values()].some(v => v.includes('true')), 'Checklist persists for the active account');
 await act(async () => { identity = { userId: 'another-account' }; for (const fn of identityListeners) fn(); });
 assert.ok(tree.root.findAllByProps({ type: 'checkbox' }).every(b => !b.props.checked), 'Checklist does not leak between accounts');
 await act(async () => { identity = { userId: 'test-account' }; for (const fn of identityListeners) fn(); });
 assert.ok(tree.root.findAllByProps({ type: 'checkbox' })[0].props.checked, 'The first account restores its own revision');
 await update('scheme=regulations-2013&branch=civil&view=topics');
 assert.ok(tree.root.findAllByProps({ type: 'checkbox' }).every(b => !b.props.checked), 'Common-topic revision does not leak between branches');
 await update('scheme=regulations-2013&branch=computer&view=browse&paper=invalid&offset=75&q=old');
 await act(async () => tree.root.findByProps({ id: 'exam-scheme' }).props.onChange({ target: { value: 'legacy-2012' } }));
 assert.equal(params.get('branch'), 'mechanical'); assert.equal(params.get('view'), 'browse');
 for (const key of ['paper', 'offset', 'q', 'tab']) assert.equal(params.get(key), null, 'Changing scope clears ' + key);
 await update('scheme=regulations-2013&branch=computer&view=overview&paper_type=branch&paper_year=2023&subject_id=english');
 const browseLink = new URL(tree.root.findAllByType('a').find(a=>a.children.join('')==='Browse questions →').props.href,'https://test');
 for(const key of ['paper_type','paper_year','subject_id'])assert.equal(browseLink.searchParams.get(key),null,'Opening a card clears incompatible '+key);
 const computer = archiveFor(guide, 'regulations-2013', 'computer');
 const first = computer.find(p => p.branchId && sourcePaperId(p));
 const second = computer.find(p => p.branchId && sourcePaperId(p) && p.id !== first.id);
 requests = []; answers = []; params = new URLSearchParams('paper=' + first.id);
 await mount(React.createElement(GuideQuestionBrowser, { papers: computer, guideId: 'mes', practice: true }));
 assert.equal(requests.at(-1).paper_id, sourcePaperId(first)); assert.equal(requests.at(-1).pool, 'practice'); assert.equal(requests.at(-1).limit, 1);
 await act(async () => { tree.root.findByProps({ children: 'Answer fixture' }).props.onClick(); await sleep(); });
 assert.equal(answers.length, 1); assert.equal(answers[0][3], undefined, 'No unpublished collection is submitted'); assert.equal(answers[0][4], sourcePaperId(first));
 const pdfOnly = { ...first, id: 'pdf-only', readerUrl: null };
 params = new URLSearchParams('paper=pdf-only'); requests = [];
 await mount(React.createElement(GuideQuestionBrowser, { papers: [pdfOnly], guideId: 'mes' }));
 assert.equal(requests.length, 0, 'An unlinked PDF must never trigger an unscoped question query');
 assert.ok(output().includes('not linked to the question bank'));
 params = new URLSearchParams('paper=' + first.id); defer = true; pending = [];
 await mount(React.createElement(GuideQuestionBrowser, { papers: computer, guideId: 'mes' }));
 const stale = pending.shift();
 await update('paper=' + second.id);
 await act(async () => { stale({ ...page, items: [{ ...question, id: 'stale-question' }] }); await sleep(); });
 assert.ok(!output().includes('stale-question'), 'Late responses cannot replace a different selected source');
 await act(async () => { pending.shift()({ ...page, items: [{ ...question, id: 'current-question' }] }); await sleep(); });
 assert.ok(output().includes('current-question'));
 defer = false; requests = [];
 params = new URLSearchParams({scheme:'regulations-2013',branch:'computer',paper:first.id,subject_id:'english',topic_id:'english:usage',status:'answered',pool:'scorable',offset:'25'});
 await mount(React.createElement(GuideQuestionBrowser, {papers:computer,guideId:'mes'}));
 const select = name => tree.root.findAllByType('select').find(node => node.props['aria-label']===name);
 assert.deepEqual(['Paper type','Specific paper','Subject','Topic','Question status','Paper year','Answer pool'].filter(name => !!select(name)), ['Paper type','Specific paper','Subject','Topic','Question status','Paper year','Answer pool']);
 assert.equal(requests.at(-1).paper_id, sourcePaperId(first));
 assert.equal(requests.at(-1).subject_id,'english'); assert.equal(requests.at(-1).topic_id,'english:usage');
 assert.equal(requests.at(-1).study_status,'answered'); assert.equal(requests.at(-1).pool,'scorable');
 await act(async()=>{select('Subject').props.onChange({target:{value:'computer-science'}});await sleep();});
 assert.equal(params.get('topic_id'),null); assert.equal(params.get('offset'),null);
 assert.equal(requests.at(-1).subject_id,'computer-science'); assert.equal(requests.at(-1).paper_id,sourcePaperId(first));
 await act(async()=>{select('Question status').props.onChange({target:{value:'answer:official'}});await sleep();});
 assert.equal(params.get('status'),null); assert.equal(requests.at(-1).answer_status,'official'); assert.equal(requests.at(-1).pool,'all');
 await act(async()=>{select('Paper type').props.onChange({target:{value:'common:General English'}});await sleep();});
 assert.equal(params.get('subject_id'),null);
 assert.ok(select('Specific paper').findAllByType('option').every(option=>computer.some(p=>p.id===option.props.value&&p.subject==='General English'&&!p.branchId)));
 await act(async()=>{select('Paper year').props.onChange({target:{value:'2023'}});await sleep();});
 const scopedOptions=select('Specific paper').findAllByType('option');
 assert.ok(scopedOptions.length>0); assert.ok(scopedOptions.every(option=>computer.some(p=>p.id===option.props.value&&p.year===2023&&p.subject==='General English')));
 await act(async()=>{tree.root.findAllByType('button').find(b=>b.children.join('')==='Reset filters').props.onClick();await sleep();});
 assert.equal(params.get('scheme'),'regulations-2013'); assert.equal(params.get('branch'),'computer');
 for(const key of ['paper','paper_type','paper_year','subject_id','topic_id','status','answer_status','pool','offset'])assert.equal(params.get(key),null,'Reset clears '+key);
 assert.ok(requests.every(request=>request.paper_id), 'Every filtered question query stays source-bound');
 assert.ok(output().includes('Answer layout'));
 params = new URLSearchParams();
 await mount(React.createElement(Exams));
 const mesCard = () => tree.root.findByProps({'aria-label':'Mizoram Engineering Service (MES)'});
 const catalogGrid = () => { let node = mesCard().parent; while(node && node.props.className !== 'exam-catalog-results') node = node.parent; return node; };
 assert.equal(tree.root.findAllByType('article').length, 8, 'MES participates in the normal eight-card page');
 assert.ok(catalogGrid(), 'MES appears inside the main card grid');
 assert.equal(tree.root.findAllByType('article')[0], mesCard(), 'MES is visible on the first page');
 assert.ok(output().includes('9 available'), 'Catalog count includes MES once');
 assert.ok(!output().includes('MES preparation'), 'The detached banner is removed');
 const search = tree.root.findByProps({id:'exam-search'});
 await act(async () => search.props.onChange({target:{value:'MES'}}));
 assert.equal(tree.root.findAllByType('article').length, 1);
 assert.equal(mesCard().findAllByType('a').find(a=>a.props.className==='exam-choice-open').props.href,'/exams/mes');
 await act(async () => mesCard().findByType('button').props.onClick());
 assert.equal(params.get('exam_open'),'mes');
 assert.equal(tree.root.findByProps({id:'exam-options-mes'}).props.hidden,false);
 assert.ok(mesCard().findAllByType('a').some(a=>a.props.href==='/exams/mes?view=topics'));
 await update('exam_layout=list&q=engineering');
 assert.equal(catalogGrid().props['data-layout'],'list', 'MES also appears in list mode');
 await update('page=2');
 assert.equal(tree.root.findAllByType('article').length,1, 'Pagination includes the guide without duplicating it');
 assert.equal(tree.root.findAllByProps({'aria-label':'Mizoram Engineering Service (MES)'}).length,0);
 await update('exam_filter=saved');
 assert.equal(tree.root.findAllByType('article').length,1);
 assert.ok(output().includes('Lower Division Clerk'));
 assert.equal(tree.root.findAllByProps({'aria-label':'Mizoram Engineering Service (MES)'}).length,0, 'Saved remains limited to actual bookmarks');
 await update('q=no-such-exam');
 assert.ok(output().includes('No matching exams'));
 await act(async () => tree.unmount());
 console.log('MES module passed: shared tabs, legacy links, stable header, branch/account revision, scope resets, exact source queries, PDF-only gate, guarded answer context stale-response isolation, MES catalog grid/search/list/pagination, and source-bound Browse filters.');
})().catch(e => { console.error(e); process.exitCode = 1; });
