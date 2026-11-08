"""Build review packet and findings for Batch 51: Assistant LO General English Paper-II (100 MCQs)."""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

def parse_path(path_str):
    if not path_str:
        return {"subject_id": "english", "topic_id": None, "subtopic_id": None}
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

# Map Q1..100 to target path, topic label, and rationale
def get_proposal_info(qnum, stem):
    if 1 <= qnum <= 10:
        path = "english/grammar/tenses"
        label = "Tenses & Verb Forms"
        if qnum == 1:
            rat = "Selects simple past tense 'lost' indicating completed action during past summer."
        elif qnum == 2:
            rat = "Selects present perfect continuous tense 'has been waiting' with time preposition 'since'."
        elif qnum == 3:
            rat = "Selects simple present tense 'wants' for non-continuous perception/mental state verb with singular subject."
        elif qnum == 4:
            rat = "Selects past continuous tense 'was driving' for action in progress interrupted by past event."
        elif qnum == 5:
            rat = "Selects future simple tense 'will call' in main clause with present tense conditional/time clause."
        elif qnum == 6:
            rat = "Selects past perfect tense 'had written' indicating completion prior to specific past milestone."
        elif qnum == 7:
            rat = "Selects simple present tense 'revolves' expressing universal scientific fact/general truth."
        elif qnum == 8:
            rat = "Selects future perfect tense 'will have finished' expressing completion before future arrival."
        elif qnum == 9:
            rat = "Selects past participle 'broken' completing present perfect question construction."
        else: # 10
            rat = "Selects base verb form 'run' following auxiliary 'Did'."
    elif 11 <= qnum <= 20:
        path = "english/grammar/prepositions"
        label = "Prepositions"
        if qnum == 11:
            rat = "Selects spatial preposition 'above' denoting higher vertical level in building."
        elif qnum == 12:
            rat = "Selects temporal preposition 'till' marking terminal point of duration."
        elif qnum == 13:
            rat = "Selects preposition 'in' completing dependent phrase 'keen interest in'."
        elif qnum == 14:
            rat = "Selects preposition 'for' completing complement of noun 'respect for'."
        elif qnum == 15:
            rat = "Selects preposition 'over' completing dependent phrase 'control over'."
        elif qnum == 16:
            rat = "Selects directional preposition of motion into interior container 'into'."
        elif qnum == 17:
            rat = "Selects spatial proximity preposition 'beside' denoting location at the side of road."
        elif qnum == 18:
            rat = "Selects dependent preposition 'of' following adjective 'worthy of'."
        elif qnum == 19:
            rat = "Selects spatial preposition 'beyond' indicating location farther past boundary."
        else: # 20
            rat = "Selects dependent preposition 'on' following verb 'congratulated on'."
    elif 21 <= qnum <= 30:
        path = "english/grammar/parts-of-speech"
        label = "Conjunctions"
        if qnum == 21:
            rat = "Selects illative coordinating conjunction 'therefore' expressing causal consequence."
        elif qnum == 22:
            rat = "Selects contrastive subordinating conjunction 'whereas' expressing direct opposition."
        elif qnum == 23:
            rat = "Selects final subordinating conjunction 'so that' expressing purpose."
        elif qnum == 24:
            rat = "Selects adversative conjunction 'yet' completing concessive clause initiated by 'Though'."
        elif qnum == 25:
            rat = "Selects conditional subordinating conjunction 'unless' denoting negative condition."
        elif qnum == 26:
            rat = "Selects parenthetical cumulative phrase 'as well as' connecting compound subjects."
        elif qnum == 27:
            rat = "Selects negative purpose subordinating conjunction 'lest' governing auxiliary 'should'."
        elif qnum == 28:
            rat = "Selects correlative conjunction 'but also' paired with 'Not only'."
        elif qnum == 29:
            rat = "Selects temporal/contrastive conjunction 'while' denoting simultaneous contrasting actions."
        else: # 30
            rat = "Selects concessive subordinating conjunction 'although' introducing contrastive clause."
    elif 31 <= qnum <= 40:
        path = "english/grammar/parts-of-speech"
        label = "Adjectives & Adverbs"
        if qnum == 31:
            rat = "Selects superlative adjective 'worst' following definite article within whole team scope."
        elif qnum == 32:
            rat = "Selects manner adverb 'slowly' modifying verb phrase 'was able to walk'."
        elif qnum == 33:
            rat = "Selects spatial/temporal adverb 'near' modifying continuous verbal motion."
        elif qnum == 34:
            rat = "Selects quantifier determiner 'much' modifying uncountable mass noun 'work'."
        elif qnum == 35:
            rat = "Selects partitive quantifier 'little' in phrase 'a little' modifying non-count noun 'water'."
        elif qnum == 36:
            rat = "Selects idiomatic adverbial phrase 'well in the test' modifying verb 'performed'."
        elif qnum == 37:
            rat = "Selects sentence adverb 'Fortunately' modifying entire matrix clause."
        elif qnum == 38:
            rat = "Selects superlative adjective 'largest' with definite article 'the'."
        elif qnum == 39:
            rat = "Selects affirmative partitive determiner 'some' modifying mass noun 'money' in polite request."
        else: # 40
            rat = "Selects degree adverb 'too' / 'so' in negative equative/degree construction."
    elif 41 <= qnum <= 50:
        path = "english/grammar"
        label = "Sentence Conversion (Simple, Complex, Compound)"
        if qnum == 41:
            rat = "Converts complex temporal sentence to simple sentence using participial non-finite clause 'Closing the door'."
        elif qnum == 42:
            rat = "Converts compound sentence into complex sentence with noun clause introduced by 'whether'."
        elif qnum == 43:
            rat = "Converts complex sentence with relative clause to simple sentence."
        elif qnum == 44:
            rat = "Converts simple sentence with infinitive into complex sentence using 'so... that' subordinate clause of result."
        elif qnum == 45:
            rat = "Converts complex conditional sentence into compound imperative/coordination."
        elif qnum == 46:
            rat = "Converts simple sentence into compound sentence using coordinating conjunction 'and'."
        elif qnum == 47:
            rat = "Converts simple sentence into complex sentence with noun clause 'that he is innocent'."
        elif qnum == 48:
            rat = "Converts simple sentence with infinitive into complex sentence with content clause 'that she would be successful'."
        elif qnum == 49:
            rat = "Converts complex conditional sentence into compound sentence using alternative coordinator 'otherwise'."
        else: # 50
            rat = "Converts compound sentence into complex sentence with subordinate temporal clause introduced by 'when'."
    elif 51 <= qnum <= 60:
        path = "english/grammar"
        label = "Sentence Transformation"
        if qnum == 51:
            rat = "Transforms manner adverb 'bravely' into prepositional noun phrase 'with bravery' without semantic loss."
        elif qnum == 52:
            rat = "Removes intensive adverb 'too' by transforming into subordinate clause of negative result 'so... that he cannot be taken seriously'."
        elif qnum == 53:
            rat = "Transforms positive degree comparison into negative comparative degree preserving semantic equivalence."
        elif qnum == 54:
            rat = "Transforms superlative degree into positive degree construction using 'as... as'."
        elif qnum == 55:
            rat = "Transforms affirmative assertion into negative equivalent using litotes 'did not fail to attend'."
        elif qnum == 56:
            rat = "Transforms exclamatory/optative sentence into assertive statement of wish/longing."
        elif qnum == 57:
            rat = "Transforms affirmative assertion into rhetorical interrogative question."
        elif qnum == 58:
            rat = "Replaces adjective predicate 'made strong' with active verbal predicate 'strengthened'."
        elif qnum == 59:
            rat = "Transforms result clause 'so urgent that it cannot be postponed' into simple sentence with 'too... to be postponed'."
        else: # 60
            rat = "Transforms negative assertion into affirmative assertive sentence 'I was doubtful of the answer'."
    elif 61 <= qnum <= 70:
        path = "english/grammar"
        label = "Sentence Synthesis"
        if qnum == 61:
            rat = "Synthesises two simple sentences into complex conditional sentence introduced by 'If'."
        elif qnum == 62:
            rat = "Synthesises two sentences using infinitive of purpose 'to start a business'."
        elif qnum == 63:
            rat = "Synthesises two sentences using noun phrase in apposition ', a wealthy and generous doctor in our locality,'."
        elif qnum == 64:
            rat = "Synthesises two sentences by condensing second predication into manner adverb 'diligently'."
        elif qnum == 65:
            rat = "Synthesises two consecutive actions into simple sentence using participial phrase 'Finishing my breakfast'."
        elif qnum == 66:
            rat = "Synthesises clauses into complex sentence using adverbial clause of time introduced by 'until'."
        elif qnum == 67:
            rat = "Synthesises coordinated clauses using cumulative conjunction 'as well as'."
        elif qnum == 68:
            rat = "Synthesises fact and predication into complex sentence with subject noun clause 'That the earth revolves around the sun'."
        elif qnum == 69:
            rat = "Synthesises two clauses into complex sentence using relative adjective clause introduced by 'which'."
        else: # 70
            rat = "Synthesises cause-result sentences into simple sentence using 'too... to' construction."
    elif 71 <= qnum <= 80:
        path = "english/vocabulary/idioms-and-phrases"
        label = "Idioms & Phrases"
        if qnum == 71:
            rat = "Identifies meaning of idiom 'kicked the bucket' denoting death ('to die')."
        elif qnum == 72:
            rat = "Identifies meaning of idiom 'when pigs fly' denoting an impossibility ('something that will not happen')."
        elif qnum == 73:
            rat = "Identifies meaning of idiom 'set the bar' denoting establishing a standard of excellence ('to set the highest standard')."
        elif qnum == 74:
            rat = "Identifies meaning of idiom 'paid lip service' denoting insincere verbal agreement ('to agree by word of mouth only')."
        elif qnum == 75:
            rat = "Identifies meaning of idiom 'old school' denoting adherence to traditional/conservative views ('conservative')."
        elif qnum == 76:
            rat = "Identifies meaning of idiom 'keep in the loop' denoting being informed ('to have information')."
        elif qnum == 77:
            rat = "Identifies meaning of idiom 'make light of' denoting treating something as unimportant ('not to take something seriously')."
        elif qnum == 78:
            rat = "Identifies meaning of idiom 'at odds' denoting conflict or disagreement ('to disagree')."
        elif qnum == 79:
            rat = "Identifies meaning of idiom 'light years away' denoting great temporal distance or improbability ('unlikely to happen')."
        else: # 80
            rat = "Identifies meaning of idiom 'wet blanket' denoting a person who discourages enjoyment ('to spoil other people\\'s fun')."
    elif 81 <= qnum <= 85:
        path = "english/vocabulary/synonyms"
        label = "Synonyms"
        if qnum == 81:
            rat = "Identifies closest synonym of 'penitent' as 'repentant'."
        elif qnum == 82:
            rat = "Identifies closest synonym of 'vengeance' as 'revenge'."
        elif qnum == 83:
            rat = "Identifies closest synonym of 'revelry' as 'celebration'."
        elif qnum == 84:
            rat = "Identifies closest synonym of 'succulent' as 'juicy'."
        else: # 85
            rat = "Identifies closest synonym of 'drowsy' as 'sleepy'."
    elif 86 <= qnum <= 90:
        path = "english/vocabulary/antonyms"
        label = "Antonyms"
        if qnum == 86:
            rat = "Identifies direct antonym of 'Fragrant' as 'smelly'."
        elif qnum == 87:
            rat = "Identifies direct antonym of 'Perpetual' as 'temporary'."
        elif qnum == 88:
            rat = "Identifies direct antonym of 'Retreat' as 'advance'."
        elif qnum == 89:
            rat = "Identifies direct antonym of 'Sensible' as 'foolish'."
        else: # 90
            rat = "Identifies direct antonym of 'Gratify' as 'displease'."
    else: # 91 <= qnum <= 100
        path = "english/vocabulary/one-word-substitution"
        label = "One-Word Substitution"
        if qnum == 91:
            rat = "Identifies one-word equivalent of 'insolent' as 'ill-mannered'."
        elif qnum == 92:
            rat = "Identifies definition of 'calligraphy' as 'beautiful handwriting'."
        elif qnum == 93:
            rat = "Identifies definition of 'philanderer' as 'chasing after women'."
        elif qnum == 94:
            rat = "Identifies definition of 'zenith' as 'the highest point'."
        elif qnum == 95:
            rat = "Identifies definition of 'inexorable' as 'unstoppable'."
        elif qnum == 96:
            rat = "Identifies definition of 'animated' as 'lively'."
        elif qnum == 97:
            rat = "Identifies definition of 'avarice' as 'love of money'."
        elif qnum == 98:
            rat = "Identifies definition of 'posthumously' as 'after her death'."
        elif qnum == 99:
            rat = "Identifies definition of 'obsolete' as 'outdated'."
        else: # 100
            rat = "Identifies definition of 'invincible' as 'cannot be conquered'."
    return path, label, rat

candidates = []
findings = []

for item in packet["items"]:
    rec = item["snapshot"]["record"]
    aid = item["appearance_id"]
    cid = item["canonical_id"]
    qnum = int(rec["qnum"])
    stem = rec["question"]
    page = rec["page"]
    fingerprint = item["source_fingerprint"]
    
    path, label, rat = get_proposal_info(qnum, stem)
    parsed = parse_path(path)
    cur_tax = rec.get("classification") or {"subject_id": "english", "topic_id": None, "subtopic_id": None}
    action = "keep" if parsed == cur_tax else "retag"
    
    candidates.append({
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": "Old_Questions/Direct_2020-2021/Assistant LO General English Paper-II.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_tax,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rat,
        "batch_id": 51,
        "policy": "study-tagging-v1"
    })
    
    findings.append({
        "appearance_id": aid,
        "canonical_id": cid,
        "qnum": str(qnum),
        "page": page,
        "topic_label": label,
        "stem": stem,
        "options": rec.get("options") or [],
        "answer_index": rec.get("answerIndex"),
        "target_path": path,
        "action": action,
        "rationale": rat
    })

# Save candidate reviews
(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Preserved written intake: this booklet is 100% objective MCQs (0 descriptive tasks)
written_intake = []
(batch_dir / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")

# Summary stats
action_counts = {}
for c in candidates:
    action_counts[c["action"]] = action_counts.get(c["action"], 0) + 1

breakdown = {}
for c in candidates:
    prop = c["proposed_primary"]
    key = prop["subtopic_id"] or prop["topic_id"] or prop["subject_id"]
    breakdown[key] = breakdown.get(key, 0) + 1

summary = {
    "batch": 51,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2020-2021/Assistant LO General English Paper-II.pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Post of Assistant Labour Officer — General English Paper-II (March 2021)",
            "document_id": "doc_f614daf6ec16a2e1ba92bc19",
            "sha256": "518ac7a75827f5b66c20a1b66391b49c6cfe0be6a33969bc39215689cc00e0df",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Assistant Labour Officer General English Paper-II (100/100 MCQs)",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "conventional_marks_preserved": 0,
    "breakdown": breakdown,
    "source_defects": [
        "Q5: The original printed paper booklet omitted option (d), printing only options (a), (b), and (c). Preserved empty string in 4th option slot.",
        "Q61: Source paper printed stem with colloquial grammar: 'You do not hard work. You will fail the test. (Use ‘if’)'."
    ],
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted conventional items.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
