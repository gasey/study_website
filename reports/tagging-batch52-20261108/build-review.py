"""Build review packet and findings for Batch 52: Informatics Officer General English Paper-II (100 MCQs)."""
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

def get_proposal_info(qnum, stem):
    if 1 <= qnum <= 10:
        path = "english/grammar/parts-of-speech"
        label = "Parts of Speech (Underlined Words)"
        if qnum == 1:
            rat = "Identifies grammatical function of 'any' modifying noun 'magazine' as adjective/determiner."
        elif qnum == 2:
            rat = "Identifies grammatical function of 'before' introducing subordinate temporal clause as conjunction."
        elif qnum == 3:
            rat = "Identifies grammatical function of 'even' modifying verb phrase as adverb."
        elif qnum == 4:
            rat = "Identifies grammatical function of 'by' introducing agent in passive construction as preposition."
        elif qnum == 5:
            rat = "Identifies grammatical function of 'master' modifying noun 'plan' as attributive adjective."
        elif qnum == 6:
            rat = "Identifies grammatical function of 'One' functioning as indefinite subject pronoun."
        elif qnum == 7:
            rat = "Identifies grammatical function of 'back' functioning as transitive verb ('back false friends')."
        elif qnum == 8:
            rat = "Identifies grammatical function of 'deep' functioning as nominal complement of preposition ('into the deep')."
        elif qnum == 9:
            rat = "Identifies grammatical function of 'than' introducing comparative clause as conjunction."
        else: # 10
            rat = "Identifies grammatical function of 'fix' functioning as noun governed by adjective 'terrible'."
    elif 11 <= qnum <= 20:
        path = "english/grammar/prepositions"
        label = "Prepositions"
        if qnum == 11:
            rat = "Selects spatial preposition 'at' for specific junction/point location ('at the roundabout')."
        elif qnum == 12:
            rat = "Selects spatial directional preposition 'on' for road orientation ('drive on the left')."
        elif qnum == 13:
            rat = "Selects preposition of transition/transfer 'into' following verb 'change into'."
        elif qnum == 14:
            rat = "Selects preposition of exclusion 'except' following negative pronoun 'nothing'."
        elif qnum == 15:
            rat = "Selects vertical/superiority preposition 'above' denoting moral elevation over corruption."
        elif qnum == 16:
            rat = "Selects transverse motion preposition 'across' for crossing a road."
        elif qnum == 17:
            rat = "Selects preposition 'over' governing duration of period ('over the years')."
        elif qnum == 18:
            rat = "Selects preposition of passage/medium 'through' ('through the back door')."
        elif qnum == 19:
            rat = "Selects temporal point preposition 'at' for precise age milestone ('at the age of')."
        else: # 20
            rat = "Selects preposition of subordination/obligation 'under' ('under the agreement')."
    elif 21 <= qnum <= 30:
        path = "english/grammar"
        label = "Mood of Verbs"
        if qnum == 21:
            rat = "Identifies mood expressing possibility with modal auxiliary as subjunctive/indicative modal."
        elif qnum == 22:
            rat = "Identifies mood expressing direct advice/admonition as imperative."
        elif qnum == 23:
            rat = "Identifies mood stating factual declaration as indicative."
        elif qnum == 24:
            rat = "Identifies interrogative inquiry of fact as indicative mood."
        elif qnum == 25:
            rat = "Identifies verbal infinitive phrase of purpose 'to speak'."
        elif qnum == 26:
            rat = "Identifies optative wish/prayer 'God bless you' as subjunctive mood."
        elif qnum == 27:
            rat = "Identifies emphatic directive 'Do sit down' as imperative mood."
        elif qnum == 28:
            rat = "Identifies hypothetical/counterfactual clause 'as though he were' as subjunctive mood."
        elif qnum == 29:
            rat = "Identifies statement of future intention as indicative mood."
        else: # 30
            rat = "Identifies direct command 'Take care of your health' as imperative mood."
    elif 31 <= qnum <= 40:
        path = "english/grammar"
        label = "Modal Auxiliaries"
        if qnum == 31:
            rat = "Selects modal auxiliary 'shall' / 'can' for collaborative suggestion."
        elif qnum == 32:
            rat = "Selects modal auxiliary expressing capability / polite request."
        elif qnum == 33:
            rat = "Selects modal auxiliary expressing deduction / logical necessity."
        elif qnum == 34:
            rat = "Selects modal auxiliary expressing past unfulfilled obligation / advice."
        elif qnum == 35:
            rat = "Selects auxiliary 'Didn\\'t' forming past simple interrogative inquiry."
        elif qnum == 36:
            rat = "Selects modal expression 'were able to' denoting past successful achievement in specific instance."
        elif qnum == 37:
            rat = "Selects modal deduction 'must have gone' indicating high-probability past event."
        elif qnum == 38:
            rat = "Selects modal expectation 'should' indicating reasonable likelihood."
        elif qnum == 39:
            rat = "Selects past perfect continuous negative 'hadn\\'t been' for duration prior to past arrival."
        else: # 40
            rat = "Selects modal expression of unfulfilled past obligation 'should have'."
    elif 41 <= qnum <= 50:
        path = "english/grammar"
        label = "Sentence Structure Analysis (Simple, Complex, Compound)"
        if qnum == 41:
            rat = "Classifies sentence with single independent clause as simple sentence."
        elif qnum == 42:
            rat = "Classifies sentence with participial phrase and single finite verb as simple sentence."
        elif qnum == 43:
            rat = "Classifies sentence joined by coordinating conjunction as compound sentence."
        elif qnum == 44:
            rat = "Classifies sentence containing dependent subordinate clause as complex sentence."
        elif qnum == 45:
            rat = "Classifies sentence with single main predication as simple sentence."
        elif qnum == 46:
            rat = "Classifies sentence with relative clause as complex sentence."
        elif qnum == 47:
            rat = "Classifies coordinated independent clauses as compound sentence."
        elif qnum == 48:
            rat = "Classifies sentence with subordinate noun/adverbial clause as complex sentence."
        elif qnum == 49:
            rat = "Classifies sentence joined by coordinating conjunction as compound sentence."
        else: # 50
            rat = "Classifies sentence introduced by subordinating causal conjunction 'As' as complex sentence."
    elif 51 <= qnum <= 60:
        path = "english/grammar"
        label = "Clause Identification"
        if qnum == 51:
            rat = "Identifies object clause 'how the machine works' as noun clause."
        elif qnum == 52:
            rat = "Identifies relative clause 'who is honest' modifying antecedent 'man' as adjective clause."
        elif qnum == 53:
            rat = "Identifies causal clause 'because he is arrogant' modifying verb 'likes' as adverb clause."
        elif qnum == 54:
            rat = "Identifies temporal clause 'When I was younger' modifying matrix verb as adverb clause."
        elif qnum == 55:
            rat = "Identifies relative clause 'who laughs last' modifying subject pronoun 'He' as adjective clause."
        elif qnum == 56:
            rat = "Identifies content clause functioning as subject complement as noun clause."
        elif qnum == 57:
            rat = "Identifies relative clause modifying noun antecedent as adjective clause."
        elif qnum == 58:
            rat = "Identifies conditional/temporal clause modifying main verb as adverb clause."
        elif qnum == 59:
            rat = "Identifies object clause introduced by 'that' as noun clause."
        else: # 60
            rat = "Identifies relative clause 'who is courageous' modifying noun 'man' as adjective clause."
    elif 61 <= qnum <= 70:
        path = "english/grammar"
        label = "Sentence Classification & Forms"
        if qnum == 61:
            rat = "Classifies polite offer/imperative as affirmative sentence."
        elif qnum == 62:
            rat = "Classifies sentence containing negative particle 'not' as negative sentence."
        elif qnum == 63:
            rat = "Classifies positive statement without negation or comparison as affirmative sentence."
        elif qnum == 64:
            rat = "Classifies comparison of inequality using inflected adjective 'sharper' as comparative."
        elif qnum == 65:
            rat = "Classifies sentence containing negative quantifier 'no' as negative sentence."
        elif qnum == 66:
            rat = "Classifies superlative degree comparison with 'tallest' as superlative sentence."
        elif qnum == 67:
            rat = "Classifies affirmative statement expressing factual joy as assertive/affirmative."
        elif qnum == 68:
            rat = "Classifies comparison using 'more sincere than' as comparative sentence."
        elif qnum == 69:
            rat = "Classifies sentence containing negative marker as negative sentence."
        else: # 70
            rat = "Classifies sentence featuring superlative adjective 'richest' as superlative sentence."
    elif 71 <= qnum <= 80:
        path = "english/vocabulary"
        label = "Contextual Word Choice (Pairs)"
        if qnum == 71:
            rat = "Selects contextually accurate collocations 'decided / turned down' describing managerial resignation."
        elif qnum == 72:
            rat = "Selects appropriate semantic pair denoting organizational action and public response."
        elif qnum == 73:
            rat = "Selects appropriate semantic pair describing personal relationship and interaction."
        elif qnum == 74:
            rat = "Selects appropriate semantic pair denoting professional competence and performance."
        elif qnum == 75:
            rat = "Selects contextually precise pair 'prepared / realistic' describing property negotiation."
        elif qnum == 76:
            rat = "Selects causal meteorological pair 'scanty / substantial' describing water supply cut."
        elif qnum == 77:
            rat = "Selects psychological verbs 'tempted / influence' describing futile persuasion."
        elif qnum == 78:
            rat = "Selects appropriate semantic pair 'ignorance / wrong' describing mistaken course of action."
        elif qnum == 79:
            rat = "Selects structural obstacle pair 'hampered / shortage' describing construction delay."
        else: # 80
            rat = "Selects law enforcement escalation pair 'persuasion / force' describing police intervention."
    elif 81 <= qnum <= 85:
        path = "english/vocabulary/idioms-and-phrases"
        label = "Proverbs & Idioms"
        if qnum == 81:
            rat = "Completes standard traditional proverb: 'A bad man is better than a bad name'."
        elif qnum == 82:
            rat = "Completes standard traditional proverb: 'Do good and cast it into the river'."
        elif qnum == 83:
            rat = "Completes standard traditional proverb: 'Guilty conscience is always suspicious'."
        elif qnum == 84:
            rat = "Completes standard traditional proverb: 'A bad workman quarrels with his tools'."
        else: # 85
            rat = "Completes standard traditional proverb: 'Every potter praises his pot'."
    elif qnum in (86, 87, 90, 91):
        path = "english/vocabulary/one-word-substitution"
        label = "One-Word Substitution"
        if qnum == 86:
            rat = "Identifies single lexical substitute for highest attainable position as 'pinnacle'."
        elif qnum == 87:
            rat = "Identifies single lexical substitute for person indifferent to art or culture as 'Philistine'."
        elif qnum == 90:
            rat = "Identifies meaning of Latin legal phrase 'Prima facie' as 'on the first impression'."
        else: # 91
            rat = "Identifies lexical substitute for universal remedy as 'panacea'."
    elif qnum == 88:
        path = "english/vocabulary/synonyms"
        label = "Synonyms"
        rat = "Identifies closest synonym of 'BACKLASH' as 'reaction'."
    elif qnum == 89:
        path = "english/vocabulary/antonyms"
        label = "Antonyms"
        rat = "Identifies direct antonym of 'AMPLE' as 'scanty'."
    elif qnum == 92:
        path = "english/grammar/prepositions"
        label = "Prepositions"
        rat = "Selects dependent preposition 'of' following legal verb 'acquitted of the charge'."
    elif qnum == 93:
        path = "english/vocabulary/idioms-and-phrases"
        label = "Idioms & Collocations"
        rat = "Selects verb 'get / put' completing idiomatic phrase 'get your house in order'."
    else: # 94 <= qnum <= 100
        path = "english/vocabulary"
        label = "Contextual Vocabulary"
        if qnum == 94:
            rat = "Selects contextually appropriate adjective 'delicate' modifying refined sensibility."
        elif qnum == 95:
            rat = "Selects precise adjective 'fastidious' denoting meticulous/particular food preferences."
        elif qnum == 96:
            rat = "Selects standard formal collocation 'exercise restraint'."
        elif qnum == 97:
            rat = "Selects intensifier adverb 'unbelievably' modifying adjective 'hot'."
        elif qnum == 98:
            rat = "Selects physiological adjective 'queasy' denoting seasickness from tossed ship."
        elif qnum == 99:
            rat = "Selects metaphorical adjective 'cloistered' denoting sheltered/isolated lifestyle."
        else: # 100
            rat = "Selects descriptive adjective 'casual' denoting uncommitted/careless work ethic."
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
        "paper_id": "Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-II.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_tax,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rat,
        "batch_id": 52,
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
    "batch": 52,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-II.pdf",
            "paper_title": "Technical Competitive Examinations for Recruitment to the Post of Informatics Officer — General English Paper-II (February 2021)",
            "document_id": "doc_e7390bd6cab5dd95ac26ed38",
            "sha256": "08db2b194c01205f6a2164e50da751cbc9e519ec99879dc17b8439a32ac9bb93",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Informatics Officer General English Paper-II (100/100 MCQs)",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "conventional_marks_preserved": 0,
    "breakdown": breakdown,
    "source_defects": [
        "Q1–Q10 Underlined Target Words in PDF Geometry: Target words in parts of speech questions (any, before, even, by, master, One, back, deep, than, fix) were rendered with vector horizontal lines in the PDF stream; verified via exact PyMuPDF geometry.",
        "Q41–Q50 3-Option Distribution: Original printed paper booklet provided 3 answer options ((a) Simple sentence, (b) Complex Sentence, (c) Compound sentence) for sentence analysis items Q41 to Q50, matching canonical record."
    ],
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted conventional items.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
