// Actual vocabulary, Today and Revise screens over one scheduled bank queue.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=process.cwd(),wr=require('node:module').createRequire(root+'/web/package.json'),React=wr('react'),ts=wr('typescript');
const rp=require.resolve('react',{paths:[process.argv[2]]});require.cache[rp]={id:rp,filename:rp,loaded:true,exports:React};
const {create,act}=require(require.resolve('react-test-renderer',{paths:[process.argv[2]]})),router=wr('react-router-dom');
const events=new Map(),calls=[];let account='u',pending=null,wordPending=null,gradePending=null,wordFixtures=false;const starts=[];
global.window={addEventListener(n,f){if(!events.has(n))events.set(n,new Set());events.get(n).add(f)},removeEventListener(n,f){events.get(n)?.delete(f)},dispatchEvent(){}};
const choices={items:[{id:'english/vocabulary/synonyms',label:'Synonyms',source:'bank',eligible:1,started:0,attempted:0,correct_latest:0,due:0,state:'exploring',rusty:false,last_activity:null},{id:'english/vocabulary/antonyms',label:'Antonyms',source:'bank',eligible:0,started:0,attempted:0,correct_latest:0,due:0,state:'exploring',rusty:false,last_activity:null}],basis:'Latest verified-key answers; not unique words mastered.',curated_available:false,curated_message:'Curated cards await review workflow.'};
const wordCard={language:'english',word:'<script>literal word</script>',meaning:'Synthetic meaning',usage:'Synthetic usage.',mizo_gloss:'',source_note:'Disposable fixture only.',recognition_options:['Right','Other'],cloze_sentence:'Use {{word}} here.',cloze_options:['word','other']};
const wordResult={correct:true,outcome:'correct',answer_text:'Right',answer_index:0,card:wordCard,next_due:null,stage:6,graduated:true,source:'reviewed-editorial',points:0,xp:0};
async function request(url,user,body){calls.push({url,user,body});
 if(url==='/curated/card'){if(wordPending)return new Promise(resolve=>wordPending.resolve=resolve);return {card:{id:'vp_'+user+'_'+body.mode,card_id:'vc_'+user,deck_id:'mat_words',deck_title:'PRIVATE_DECK_'+user,mode:body.mode,prompt:'PRIVATE_WORD_'+user+'_'+body.mode,options:['Right','Other'],expires_at:'2099-01-01',stage:1,seen:1,source:'reviewed-editorial'}}}
 if(url.startsWith('/curated/cards/')&&url.endsWith('/answer')){if(gradePending)return new Promise(resolve=>gradePending.resolve=resolve);return wordResult}
 if(url==='/decks'&&wordFixtures)return {...choices,curated_available:true,curated_practice_enabled:wordFixtures!=='paused',curated_known_total:0,curated_items:[{id:'mat_words',label:'PRIVATE_DECK_'+user,source:'curated',eligible_cards:8,eligible_words:8,started:8,due:8,attempted:0,correct_latest:0,known:0,state:'exploring',rusty:false,last_activity:null,modes:['recognition','cloze','mizo-to-english','english-to-mizo'],url:'/materials/mat_words'}]};if(url.startsWith('/overview'))return {eligible:1,started:0,due:0,retaining:0,graded:0,correct:0,new_daily_target:10};if(url==='/decks')return choices;if(url==='/card'){if(pending)return new Promise(resolve=>pending.resolve=resolve);return {card:{id:'vcr_test',question_id:'cq_synthetic',stage:0,seen:0,expires_at:'2099-01-01',question:{question:body.deck_id?'Synthetic synonym question':'Synthetic all-deck question',options:['A','B'],answer_source:'official',source_pdf_url:'https://example.test/synthetic.pdf',page:1}}}}if(url.endsWith('/answer'))return {correct:true,outcome:'correct',answer_text:'B',next_due:null,stage:6,graduated:true};throw Error('Unexpected URL '+url)}
const cache=new Map();function load(file){file=path.resolve(file);if(cache.has(file))return cache.get(file);const mod={exports:{}};cache.set(file,mod.exports);const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}).outputText;new Function('module','exports','require',code)(mod,mod.exports,id=>{
 if(id.endsWith('/api'))return {getAccountSession:async()=>({authenticated:!!account}),getToday:async()=>({account:!!account,ist_date:'2026-11-18',exam:null,focus:{items:[],available:[],limit:5},due_count:7,scheduled_count:7,new_questions:null,quests:[],empty_reason:'Choose an exam.',vocabulary:account?{target:5,introduced:3,remaining:2,due:7,eligible:20,url:'/revise?tab=vocabulary&exam_scope=all'}:null,daily_five:{status:'not_started',url:'/games?mode=daily'}}),getReviewQueue:async()=>({due_count:9,scheduled_count:9,vocabulary_due_count:7,vocabulary_scheduled_count:7,items:[],has_more:false}),startSmartReview:async(...args)=>{starts.push(args);return {id:'synthetic_saved_session'}}};
 if(id.endsWith('/preferredExam'))return {choosePreferredExam:()=>{}};
 if(id.endsWith('/UdcStudySessions'))return {default:()=>null};
 if(id.endsWith('/review'))return {reviewSession:async()=>({user_id:account})};
 if(id.endsWith('/vocabulary'))return {vocabularyRequest:request};
 if(id.endsWith('/answerStatus'))return {learnerExplanation:x=>x};
 if(id.endsWith('/consolidation'))return {legacyRevisionLink:id=>'/revise?session='+id};
 if(id.endsWith('/examScope'))return {scopeLink:x=>x};
 if(id.endsWith('/SourceQuestionText'))return {SourceQuestionText:({text})=>React.createElement('span',null,text),SourceQuestionContext:()=>null};
 if(id.endsWith('/AnswerLayout'))return {AnswerLayoutControl:()=>null,AnswerOptions:({children})=>React.createElement('div',null,children)};
 if(id.startsWith('.')){const base=path.resolve(path.dirname(file),id);return load(base+(fs.existsSync(base+'.tsx')?'.tsx':'.ts'))}return wr(id)
 });return mod.exports}
const Vocabulary=load(root+'/web/src/screens/Vocabulary.tsx').default;let tree;const flatten=n=>typeof n==='string'?n:Array.isArray(n)?n.map(flatten).join(''):(n?.children||[]).map(flatten).join('');const json=()=>flatten(tree.toJSON());
(async()=>{
 await act(async()=>{tree=create(React.createElement(router.MemoryRouter,{initialEntries:['/revise?tab=vocabulary']},React.createElement(Vocabulary,{embedded:true}))) });
 assert.ok(json().includes('Choose a vocabulary deck')&&json().includes('0 of 0 answered')&&json().includes('not unique words mastered'));
 assert.equal(calls.find(c=>c.url==='/card').body.deck_id,null);
 await act(async()=>tree.root.findByType('select').props.onChange({target:{value:'english/vocabulary/synonyms'}}));
 assert.ok(calls.some(c=>c.url==='/card'&&c.body.deck_id==='english/vocabulary/synonyms'&&!c.body.resume_id));
 assert.ok(calls.some(c=>c.url==='/overview?deck_id=english%2Fvocabulary%2Fsynonyms'));
 assert.ok(json().includes('Synthetic synonym question')&&!json().includes('Synthetic all-deck question'));
 const plain=n=>typeof n==='string'?n:(n.children||[]).map(plain).join('');
 await act(async()=>tree.root.findAllByType('button').find(n=>plain(n)==='BB').props.onClick());
 assert.ok(json().includes('Graduated from your shared review queue')&&!json().includes('1970'));
 assert.ok(tree.root.findAllByType('a').some(n=>n.props.href==='/revise?item_type=vocab'));

 // Start another deck request and expire the account before its response.
 pending={};await act(async()=>tree.root.findByType('select').props.onChange({target:{value:'english/vocabulary/antonyms'}}));
 account='';await act(async()=>{for(const fn of events.get('ism-auth-expired'))fn()});
 assert.ok(!json().includes('Choose a vocabulary deck')&&!json().includes('Synthetic synonym question'));
 await act(async()=>pending.resolve({card:{question:{question:'STALE_PRIVATE_CARD'}}}));assert.ok(!json().includes('STALE_PRIVATE_CARD'));
 await act(async()=>tree.unmount());account='u';pending=null;
 const Today=load(root+'/web/src/components/TodayCard.tsx').default;
 await act(async()=>{tree=create(React.createElement(router.MemoryRouter,null,React.createElement(Today)))});
 assert.ok(json().includes('5 words a day')&&json().includes('7 vocabulary reviews due'));
 account='';await act(async()=>{for(const fn of events.get('ism-auth-expired'))fn()});assert.ok(!json().includes('5 words a day'));
 await act(async()=>tree.unmount());account='u';
 const Revise=load(root+'/web/src/screens/Revise.tsx').default;
 await act(async()=>{tree=create(React.createElement(router.MemoryRouter,{initialEntries:['/revise?item_type=vocab']},React.createElement(Revise)))});
 assert.ok(json().includes('7 vocabulary reviews due'));
 await act(async()=>tree.root.findAllByType('button').find(n=>plain(n)==='Start Smart Review →').props.onClick());
 assert.equal(starts.length,1);assert.equal(starts[0][3],'vocab');
 await act(async()=>tree.unmount());assert.ok([...events.values()].every(x=>!x.size));
 wordFixtures=true;account='u';
 await act(async()=>{tree=create(React.createElement(router.MemoryRouter,{initialEntries:['/revise?tab=vocabulary&curated_deck=mat_words']},React.createElement(Vocabulary,{embedded:true}))) });
 assert.ok(json().includes('PRIVATE_WORD_u_recognition')&&json().includes('Reviewed editorial card'));
 assert.ok(!json().includes('Official key'));
 assert.ok(tree.root.findAllByType('a').some(n=>n.props.href.includes('word_deck=mat_words')));
 wordPending={};await act(async()=>tree.root.findByProps({id:'word-mode'}).props.onChange({target:{value:'cloze'}}));
 account='';await act(async()=>{for(const fn of events.get('ism-auth-expired'))fn()});
 assert.ok(!json().includes('PRIVATE_WORD')&&!json().includes('PRIVATE_DECK'));
 await act(async()=>wordPending.resolve({card:{prompt:'STALE_PRIVATE_WORD'}}));assert.ok(!json().includes('STALE_PRIVATE_WORD'));
 wordPending=null;account='u2';await act(async()=>{for(const fn of events.get('ism-auth-change'))fn()});
 assert.ok(json().includes('PRIVATE_WORD_u2_cloze'));
 const choicesBox=()=>tree.root.findByProps({'aria-label':'Word choices'}),oldPick=choicesBox().findAllByType('button')[0].props.onClick;
 gradePending={};await act(async()=>oldPick());assert.ok(gradePending.resolve);
 account='u3';await act(async()=>{for(const fn of events.get('ism-auth-change'))fn()});assert.ok(json().includes('PRIVATE_WORD_u3_cloze'));
 await act(async()=>gradePending.resolve({...wordResult,card:{...wordCard,word:'OLD_PRIVATE_RESULT'}}));assert.ok(!json().includes('OLD_PRIVATE_RESULT'));
 gradePending=null;const before=calls.length;await act(async()=>oldPick());assert.equal(calls.length,before,'A stale button cannot grade after an account change');
 await act(async()=>choicesBox().findAllByType('button')[0].props.onClick());assert.ok(json().includes('Graduated from the shared review queue.')&&!json().includes('1970'));
 assert.equal(tree.root.findAllByType('script').length,0,'Editorial text is escaped');
 const requests=calls.filter(c=>c.url==='/curated/card').length;wordFixtures='paused';await act(async()=>{for(const fn of events.get('ism-community-change'))fn()});
 assert.ok(json().includes('Word practice is temporarily paused')&&!json().includes('PRIVATE_WORD'));
 assert.equal(calls.filter(c=>c.url==='/curated/card').length,requests);
 await act(async()=>tree.unmount());assert.ok([...events.values()].every(x=>!x.size));
 console.log('Curated vocabulary passed: legacy bank/Today/Revise flow, actual reviewed-word component, mode binding, saved-set link, graduation without a fake date, escaped editorial text, account-expiry clearing, stale response/button rejection and quarantined practice.');
})().catch(e=>{console.error(e);process.exitCode=1});
