"""Build review packet and findings for Batch 53: Inspector of Excise General English Paper-II (100 MCQs)."""
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
        label = "Parts of Speech"
        if qnum == 1:
            rat = "Identifies 'either' functioning as distributive pronoun governing prepositional phrase ('either of them')."
        elif qnum == 2:
            rat = "Identifies 'Either' modifying singular count noun 'pen' as distributive adjective/determiner."
        elif qnum == 3:
            rat = "Identifies 'Both' functioning as indefinite pronoun governing prepositional phrase ('Both of them')."
        elif qnum == 4:
            rat = "Identifies 'both' modifying plural noun 'ways' as determiner/adjective."
        elif qnum == 5:
            rat = "Identifies 'half' functioning as fraction noun governing complement ('One half of this task')."
        elif qnum == 6:
            rat = "Identifies 'half' modifying adjective 'dead' as adverb of degree."
        elif qnum == 7:
            rat = "Identifies 'above' functioning as nominal complement of preposition 'from'."
        elif qnum == 8:
            rat = "Identifies 'above' functioning as spatial preposition governing noun phrase 'our head'."
        elif qnum == 9:
            rat = "Identifies 'after' functioning as temporal adverb modifying verb 'arrived'."
        else: # 10
            rat = "Identifies 'after' introducing temporal subordinate clause as subordinating conjunction."
    elif 11 <= qnum <= 20:
        path = "english/grammar/parts-of-speech"
        label = "Classification of Adverbs"
        if qnum == 11:
            rat = "Classifies 'fast' modifying verb 'walk' as adverb of manner."
        elif qnum == 12:
            rat = "Classifies 'almost' modifying adjective 'ripe' as adverb of degree."
        elif qnum == 13:
            rat = "Classifies 'before' denoting prior time as adverb of time."
        elif qnum == 14:
            rat = "Classifies 'round' denoting spatial direction/position as adverb of place."
        elif qnum == 15:
            rat = "Classifies 'always' denoting habitual repetition as adverb of frequency."
        elif qnum == 16:
            rat = "Classifies adverb modifying verb/predicate according to semantic category."
        elif qnum == 17:
            rat = "Classifies adverb expressing place/direction."
        elif qnum == 18:
            rat = "Classifies adverb denoting frequency or repetition."
        elif qnum == 19:
            rat = "Classifies adverb denoting degree or measure."
        else: # 20
            rat = "Classifies adverb denoting manner or time."
    elif 21 <= qnum <= 30:
        path = "english/grammar/prepositions"
        label = "Prepositions"
        if qnum == 21:
            rat = "Selects preposition of distribution among more than two entities 'among'."
        elif qnum == 22:
            rat = "Selects spatial containment preposition 'in' / 'into'."
        elif qnum == 23:
            rat = "Selects spatial proximity/direction preposition."
        elif qnum == 24:
            rat = "Selects phrasal verb particle 'up' in 'beaten up'."
        elif qnum == 25:
            rat = "Selects transportation preposition 'by' with vehicle."
        elif qnum == 26:
            rat = "Selects spatial alignment preposition 'along' the river."
        elif qnum == 27:
            rat = "Selects partitive preposition 'of' / 'among' all the other players."
        elif qnum == 28:
            rat = "Selects temporal duration preposition 'in' four hours."
        elif qnum == 29:
            rat = "Selects spatial preposition indicating position above or over."
        else: # 30
            rat = "Selects dependent preposition completing verbal phrase."
    elif 31 <= qnum <= 40:
        path = "english/grammar/tenses"
        label = "Tenses & Verb Forms"
        if qnum == 31:
            rat = "Selects present perfect tense 'have sent' with time adverbial 'up to now'."
        elif qnum == 32:
            rat = "Selects past simple tense indicating completed past action."
        elif qnum == 33:
            rat = "Selects present continuous or habitual present verb form."
        elif qnum == 34:
            rat = "Selects past perfect tense indicating prior past completion."
        elif qnum == 35:
            rat = "Selects future tense or conditional form."
        elif qnum == 36:
            rat = "Selects past continuous tense indicating interrupted action."
        elif qnum == 37:
            rat = "Selects present perfect continuous tense."
        elif qnum == 38:
            rat = "Selects past simple tense 'went' with past time marker 'ago'."
        elif qnum == 39:
            rat = "Selects present perfect tense 'have done' for today's completed accomplishments."
        else: # 40
            rat = "Selects simple present tense 'appears' for regular recurring publication schedule."
    elif 41 <= qnum <= 50:
        path = "english/grammar"
        label = "Sentence Structure Analysis (Simple, Complex, Compound)"
        if qnum == 41:
            rat = "Classifies sentence with single independent clause as simple sentence."
        elif qnum == 42:
            rat = "Classifies sentence joined by coordinating alternative conjunction 'or' as compound sentence."
        elif qnum == 43:
            rat = "Classifies sentence with dependent subordinate clause as complex sentence."
        elif qnum == 44:
            rat = "Classifies simple sentence containing participial phrase."
        elif qnum == 45:
            rat = "Classifies compound sentence joined by coordinator."
        elif qnum == 46:
            rat = "Classifies complex sentence containing relative clause."
        elif qnum == 47:
            rat = "Classifies simple sentence with single main finite verb."
        elif qnum == 48:
            rat = "Classifies compound sentence with coordinated clauses."
        elif qnum == 49:
            rat = "Classifies complex sentence with subordinate clause."
        else: # 50
            rat = "Classifies sentence structure according to clause composition."
    elif 51 <= qnum <= 60:
        path = "english/grammar"
        label = "Sentence Forms & Degrees of Comparison"
        if qnum == 51:
            rat = "Classifies positive statement without negation or comparison as affirmative sentence."
        elif qnum == 52:
            rat = "Classifies equative comparison with 'as... as' as positive degree."
        elif qnum == 53:
            rat = "Classifies comparison of inequality with 'more useful than' as comparative sentence."
        elif qnum == 54:
            rat = "Classifies sentence containing negative marker 'not' as negative sentence."
        elif qnum == 55:
            rat = "Classifies comparison with 'the most beautiful' as superlative sentence."
        elif qnum == 56:
            rat = "Classifies affirmative or assertive sentence structure."
        elif qnum == 57:
            rat = "Classifies comparative degree structure."
        elif qnum == 58:
            rat = "Classifies superlative degree structure."
        elif qnum == 59:
            rat = "Classifies negative sentence structure."
        else: # 60
            rat = "Classifies sentence according to degree of comparison or assertion type."
    elif 61 <= qnum <= 70:
        path = "english/grammar"
        label = "Clause Identification"
        if qnum == 61:
            rat = "Identifies object content clause 'that we will win the match' as noun clause."
        elif qnum == 62:
            rat = "Identifies dependent clause functioning as adverbial/adjective modifier."
        elif qnum == 63:
            rat = "Identifies relative clause modifying noun antecedent as adjective clause."
        elif qnum == 64:
            rat = "Identifies temporal clause 'till I return' as adverb clause."
        elif qnum == 65:
            rat = "Identifies relative clause 'that has no turning' modifying 'lane' as adjective clause."
        elif qnum == 66:
            rat = "Identifies object content clause 'that the weather will change' as noun clause."
        elif qnum == 67:
            rat = "Identifies locative adverbial clause 'where living was cheaper' as adverb clause."
        elif qnum == 68:
            rat = "Identifies relative clause 'who comes late' modifying 'boy' as adjective clause."
        elif qnum == 69:
            rat = "Identifies subordinate clause functioning as noun/adverbial element."
        else: # 70
            rat = "Identifies clause function according to syntactic role."
    elif 71 <= qnum <= 80:
        path = "english/sentence-correction"
        label = "Sentence Improvement & Correction"
        if qnum == 71:
            rat = "Selects correct prepositional phrase / idiom in sentence improvement."
        elif qnum == 72:
            rat = "Selects correct grammatical structure correcting faulty phrasing."
        elif qnum == 73:
            rat = "Selects correct tense / verb form in sentence improvement."
        elif qnum == 74:
            rat = "Selects concise idiomatic phrasing in sentence improvement."
        elif qnum == 75:
            rat = "Selects correct subject-verb agreement or modifier placement."
        elif qnum == 76:
            rat = "Selects correct parallel structure or pronoun reference."
        elif qnum == 77:
            rat = "Evaluates grammatical correctness of 'Any able bodied man is eligible' (no improvement needed)."
        elif qnum == 78:
            rat = "Applies correct politeness order of personal pronouns (second, third, first person: 'You, your brother and I')."
        elif qnum == 79:
            rat = "Selects natural possessive noun phrase 'your child\\'s hand'."
        else: # 80
            rat = "Applies conditional clause inversion 'Had you not reached' for third conditional."
    elif 81 <= qnum <= 90:
        path = "english/vocabulary"
        label = "Contextual Vocabulary & Analogies"
        if qnum == 81:
            rat = "Completes semantic analogy: life is to death as pleasure is to pain/suffering."
        elif qnum == 82:
            rat = "Selects contextually accurate vocabulary word filling sentence blank."
        elif qnum == 83:
            rat = "Selects appropriate word completing contextual description."
        elif qnum == 84:
            rat = "Selects contextually accurate collocation."
        elif qnum == 85:
            rat = "Selects precise descriptive adjective."
        elif qnum == 86:
            rat = "Selects contextually accurate word filling blank."
        elif qnum == 87:
            rat = "Selects appropriate descriptive word."
        elif qnum == 88:
            rat = "Selects contextually fitting vocabulary term."
        elif qnum == 89:
            rat = "Selects appropriate semantic term."
        else: # 90
            rat = "Selects precise descriptive term 'verbatim' / 'literal' describing translation."
    elif qnum in (91, 93, 94):
        path = "english/vocabulary"
        label = "Collective Nouns & Nomenclature"
        if qnum == 91:
            rat = "Selects specific collective noun 'sheaf' for bound stalks of wheat."
        elif qnum == 93:
            rat = "Selects specific collective noun 'litter' for offspring born at one birth."
        else: # 94
            rat = "Identifies specific zoological term 'calf' for the young of an elephant."
    elif qnum in (92, 96, 98, 100):
        path = "english/vocabulary/idioms-and-phrases"
        label = "Idioms, Similes & Proverbs"
        if qnum == 92:
            rat = "Completes traditional idiomatic simile: 'as blind as a bat'."
        elif qnum == 96:
            rat = "Completes well-known English proverb: 'Beggars cannot be choosers'."
        elif qnum == 98:
            rat = "Completes metaphorical English proverb: 'Beneath the rose lies the serpent/thorn'."
        else: # 100
            rat = "Completes standard idiomatic expression: 'To spread like wildfire'."
    elif qnum == 95:
        path = "english/vocabulary/synonyms"
        label = "Synonyms"
        rat = "Identifies direct lexical synonym of 'LAUD' as 'praise'."
    elif qnum == 97:
        path = "english/vocabulary/antonyms"
        label = "Antonyms"
        rat = "Identifies direct lexical antonym of 'LETHARGIC' as 'hyperactive'."
    else: # 99
        path = "english/vocabulary/one-word-substitution"
        label = "Foreign Phrases / One-Word Equivalent"
        rat = "Identifies literal meaning of Latin phrase 'per centum' as 'by the hundred'."
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
        "paper_id": "Old_Questions/Direct_2020-2021/Inspector of Excise - General English Paper-II.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_tax,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rat,
        "batch_id": 53,
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
    "batch": 53,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2020-2021/Inspector of Excise - General English Paper-II.pdf",
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Inspector under Excise & Narcotics Department — General English Paper-II (February 2021)",
            "document_id": "doc_96761ae7f42a829600dbd517",
            "sha256": "770be2f84dc46f578cb30c5a1ab63be07011812f44433fde603f1bef1614fb93",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for Inspector of Excise General English Paper-II (100/100 MCQs)",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "conventional_marks_preserved": 0,
    "breakdown": breakdown,
    "source_defects": [
        "Q41–Q50 3-Option Distribution: Original printed paper booklet provided 3 answer options ((a) Simple sentence, (b) Complex sentence, (c) Compound sentence) for sentence analysis items Q41 to Q50, matching canonical record."
    ],
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted conventional items.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
