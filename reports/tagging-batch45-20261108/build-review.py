"""Build review packet and findings for Batch 45: ADA, AA & ATA General English (60 MCQs)."""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

def parse_path(path_str):
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

# Proposals mapped by qnum
proposals = {
    # Group 1: Parts of Speech (Q1-Q10)
    1: (2, "Parts of Speech (Transitive Verb)", "english/grammar/parts-of-speech", "retag", "Identifies 'hurt' functioning as a transitive verb in the predicate."),
    2: (2, "Parts of Speech (Common Noun)", "english/grammar/parts-of-speech", "retag", "Identifies 'Grammar' functioning as a noun naming a systematic body of rules."),
    3: (2, "Parts of Speech (Predicate Adjective)", "english/grammar/parts-of-speech", "retag", "Identifies 'true' functioning as a predicate adjective following linking verb 'sounds'."),
    4: (2, "Noun Classes (Abstract Noun)", "english/grammar/parts-of-speech", "retag", "Classifies 'Laughter' as an abstract noun denoting a state or emotion."),
    5: (2, "Noun Classes (Collective Noun)", "english/grammar/parts-of-speech", "retag", "Classifies 'crowd' as a collective noun denoting a collection of persons."),
    6: (2, "Parts of Speech (Adverb of Degree)", "english/grammar/parts-of-speech", "retag", "Identifies 'quite' functioning as an adverb of degree modifying adjective 'big'."),
    7: (2, "Parts of Speech (Adverb of Manner)", "english/grammar/parts-of-speech", "retag", "Identifies 'fast' functioning as an adverb of manner modifying verb 'runs'."),
    8: (2, "Parts of Speech (Interjection)", "english/grammar/parts-of-speech", "retag", "Identifies exclamatory word 'Bravo!' as an interjection expressing praise/approval."),
    9: (2, "Parts of Speech (Descriptive Adjective)", "english/grammar/parts-of-speech", "retag", "Identifies 'courageous' functioning as a descriptive adjective used substantively with definite article."),
    10: (2, "Parts of Speech (Preposition)", "english/grammar/parts-of-speech", "retag", "Identifies 'over' functioning as a spatial preposition showing relation between 'balloon' and 'fan'."),

    # Group 2: Modals & Sentence Functions (Q11-Q20)
    11: (3, "Modal Notions (Possibility)", "english/grammar", "retag", "Identifies modal auxiliary 'may' expressing possibility in 'It may rain tomorrow'."),
    12: (3, "Modal Notions (Obligation)", "english/grammar", "retag", "Identifies modal auxiliary 'must' expressing moral duty and obligation in 'One must always respect the elders'."),
    13: (3, "Sentence Function (Order / Command)", "english/grammar", "retag", "Identifies imperative sentence 'Get out of the room now' functioning as a direct order."),
    14: (3, "Sentence Function (Polite Request)", "english/grammar", "retag", "Identifies conditional modal question with 'Would you kindly' functioning as a polite request."),
    15: (3, "Aspect & Habitual Action", "english/grammar", "retag", "Identifies simple present with frequency adverb 'usually' expressing habitual action."),
    16: (3, "Clause Purpose", "english/grammar", "retag", "Identifies infinitive phrase 'to save his friend' expressing purpose."),
    17: (3, "Optative Mood (Wish / Prayer)", "english/grammar", "retag", "Identifies optative construction 'May you be blessed' expressing a wish or blessing."),
    18: (3, "Modal Notions (Moral Obligation / Advice)", "english/grammar", "retag", "Identifies modal 'must' expressing ethical duty/advice in 'You must stand for what is right'."),
    19: (3, "Clause Purpose", "english/grammar", "retag", "Identifies infinitive of purpose 'just to see you' denoting intention."),
    20: (3, "Conditional Sentence", "english/grammar", "retag", "Identifies subordinate clause introduced by 'only if' expressing condition."),

    # Group 3: Prepositions (Q21-Q27)
    21: (3, "Prepositions of Time", "english/grammar/prepositions", "retag", "Selects 'since' denoting a point of origin in time with negative perfect tense."),
    22: (3, "Dependent Prepositions (fight for)", "english/grammar/prepositions", "retag", "Selects preposition 'for' expressing the objective/prize in 'fought for the crown'."),
    23: (4, "Prepositions of Direction / Motion", "english/grammar/prepositions", "retag", "Selects preposition of motion 'into' in poetic quotation 'walk into my parlour'."),
    24: (4, "Idiomatic Preposition (with the lark)", "english/grammar/prepositions", "retag", "Selects preposition 'with' in traditional idiom 'rise with the lark' meaning very early."),
    25: (4, "Fixed Prepositional Idiom (by God)", "english/grammar/prepositions", "retag", "Selects 'By' for swearing an oath in 'By the name of God he swore'."),
    26: (4, "Prepositions of Position (among)", "english/grammar/prepositions", "retag", "Selects 'among' for position surrounded by plural persons ('sits among his boys')."),
    27: (4, "Prepositions of Position (across)", "english/grammar/prepositions", "keep", "Confirms exact active subtopic for spatial preposition 'across' ('Her arms across her breast she laid')."),

    # Group 4: Conjunctions (Q28-Q34)
    28: (4, "Adversative Conjunction (but)", "english/grammar/parts-of-speech", "retag", "Selects coordinating conjunction 'but' introducing an unexpected contrast ('ran fast, but I missed')."),
    29: (4, "Concessive Conjunction (though)", "english/grammar/parts-of-speech", "retag", "Selects subordinating conjunction of concession 'though' ('finished first though he began late')."),
    30: (4, "Causal Conjunction (Since)", "english/grammar/parts-of-speech", "retag", "Selects subordinating conjunction 'Since' expressing reason/cause ('Since duty calls us we must obey')."),
    31: (4, "Explanatory Coordinating Conjunction (for)", "english/grammar/parts-of-speech", "retag", "Selects coordinating conjunction 'for' denoting reason in biblical proverb ('for they shall obtain mercy')."),
    32: (4, "Alternative Conjunction (else)", "english/grammar/parts-of-speech", "retag", "Selects alternative conjunction 'else' meaning otherwise ('Give me the drink, else I shall die')."),
    33: (4, "Temporal Conjunction (before)", "english/grammar/parts-of-speech", "retag", "Selects subordinating temporal conjunction 'before' ('died before I was born')."),
    34: (4, "Conditional Conjunction (Unless)", "english/grammar/parts-of-speech", "retag", "Selects negative conditional conjunction 'Unless' ('Unless you tell me the truth...')."),

    # Group 5: Verbals - Gerund vs Participle (Q35-Q42)
    35: (5, "Verbals (Gerund as Subject)", "english/grammar/parts-of-speech", "retag", "Identifies 'Hunting' functioning as a verbal noun / gerund subject of sentence."),
    36: (5, "Verbals (Gerund as Prepositional Object)", "english/grammar/parts-of-speech", "retag", "Identifies 'hoarding' functioning as a gerund object of preposition 'of'."),
    37: (5, "Verbals (Participial Adjective)", "english/grammar/parts-of-speech", "retag", "Identifies 'swimming' in 'swimming pool' as a participle/noun-adjunct functioning adjectivally."),
    38: (5, "Verbals (Gerund as Subject)", "english/grammar/parts-of-speech", "retag", "Identifies 'Swimming' functioning as a gerund subject."),
    39: (5, "Verbals (Participial Adjective)", "english/grammar/parts-of-speech", "retag", "Identifies 'losing' modifying noun 'game' as a present participle."),
    40: (5, "Verbals (Gerund in Comparison)", "english/grammar/parts-of-speech", "retag", "Identifies 'Giving' and 'receiving' functioning as gerunds compared with 'better than'."),
    41: (5, "Verbals (Participial Adjective)", "english/grammar/parts-of-speech", "retag", "Identifies 'standing' modifying 'building' as a present participle."),
    42: (5, "Verbals (Gerund as Subject Complement)", "english/grammar/parts-of-speech", "retag", "Identifies 'smoking' functioning as a gerund predicate complement after 'is'."),

    # Group 6: Sentence Types (Q43-Q51)
    43: (5, "Sentence Classification (Interrogative)", "english/grammar", "retag", "Classifies question with inverted structure and question mark as an interrogative sentence."),
    44: (5, "Sentence Classification (Assertive)", "english/grammar", "keep", "Confirms active topic for declarative statement 'Nature is the best physician'."),
    45: (5, "Sentence Classification (Imperative)", "english/grammar", "retag", "Classifies prayer/request 'Have mercy on us' with implied subject 'you' as an imperative sentence."),
    46: (5, "Sentence Classification (Assertive)", "english/grammar", "retag", "Classifies declarative sentence 'Daphne is the tallest girl in her class' as assertive."),
    47: (5, "Sentence Classification (Exclamatory)", "english/grammar", "retag", "Classifies exclamatory statement 'How very cold the night is!' expressing strong emotion."),
    48: (6, "Sentence Classification (Exclamatory / Optative)", "english/grammar", "retag", "Classifies blessing/wish 'May you have all the joy...' in traditional sentence taxonomy."),
    49: (6, "Sentence Classification (Negative)", "english/grammar", "retag", "Classifies negative declarative statement 'You cannot have all the riches...'."),
    50: (6, "Sentence Classification (Assertive)", "english/grammar", "retag", "Classifies affirmative declarative statement 'Today is a fine day' as assertive."),
    51: (6, "Sentence Classification (Imperative)", "english/grammar", "retag", "Classifies direct command 'Shut the door at once' as an imperative sentence."),

    # Group 7: Subject-Verb Agreement (Q52-Q60)
    52: (6, "Subject-Verb Agreement (Prepositional Intervener)", "english/grammar/subject-verb-agreement", "retag", "Selects singular past verb 'was' agreeing with head noun 'quality', not intervening plural 'mangoes'."),
    53: (6, "Subject-Verb Agreement (One of + Plural Noun)", "english/grammar/subject-verb-agreement", "retag", "Selects singular verb 'takes' agreeing with singular subject 'one'."),
    54: (6, "Subject-Verb Agreement (Compound Subject)", "english/grammar/subject-verb-agreement", "retag", "Selects plural auxiliary 'do' with compound subject joined by and ('Fire and water do not agree')."),
    55: (6, "Subject-Verb Agreement (Single Combined Unit)", "english/grammar/subject-verb-agreement", "retag", "Selects singular verb 'is' for compound subject expressing a single integrated unit ('The horse and carriage is at the door')."),
    56: (6, "Subject-Verb Agreement (Correlative Conjunction)", "english/grammar/subject-verb-agreement", "retag", "Selects singular verb 'seems' agreeing with nearer singular subject 'blame' in 'Neither praise nor blame'."),
    57: (6, "Subject-Verb Agreement (Singular Field of Study)", "english/grammar/subject-verb-agreement", "retag", "Selects singular verb 'is' for subject 'Physics' naming a branch of science."),
    58: (6, "Subject-Verb Agreement (Collective Noun Divided)", "english/grammar/subject-verb-agreement", "retag", "Selects plural verb 'are' / 'were' for collective noun 'Committee' acting individually / divided in opinion."),
    59: (7, "Subject-Verb Agreement (Book Title as Proper Noun)", "english/grammar/subject-verb-agreement", "retag", "Selects singular verb 'is' for title of a single book 'The Arabian Nights'."),
    60: (7, "Subject-Verb Agreement (Fraction of an Uncountable Whole)", "english/grammar/subject-verb-agreement", "retag", "Selects singular verb 'is' for fraction of singular/uncountable whole 'Three parts of the business is left'.")
}

candidates = []
findings = []
breakdown = {}
action_counts = {"retag": 0, "keep": 0}

for it in packet["items"]:
    qn = int(it["appearance"]["qnum"])
    page, skill, path_str, action, rationale = proposals[qn]
    proposed_tax = parse_path(path_str)
    
    cur_class = it["snapshot"]["record"]["classification"]
    cur_sub = cur_class.get("subject_id")
    cur_top = cur_class.get("topic_id")
    cur_subtop = cur_class.get("subtopic_id")
    
    if cur_subtop:
        cur_path = cur_subtop
    elif cur_top:
        cur_path = cur_top
    elif cur_sub:
        cur_path = cur_sub
    else:
        cur_path = "untagged"
        
    prop_path = path_str
    breakdown[prop_path] = breakdown.get(prop_path, 0) + 1
    action_counts[action] = action_counts.get(action, 0) + 1
    
    cand = {
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "paper_id": it["appearance"]["paper_id"],
        "source_fingerprint": it["source_fingerprint"],
        "review_status": "pending",
        "action": action,
        "current_primary": cur_class,
        "proposed_primary": proposed_tax,
        "rationale": rationale,
        "batch_id": 45,
        "policy": "study-tagging-v1"
    }
    candidates.append(cand)
    
    finding = {
        "index": len(candidates),
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "printed_question": f"Q{qn}",
        "physical_page": page,
        "tested_skill": skill,
        "current_path": cur_path,
        "proposed_path": prop_path,
        "action": action,
        "rationale": rationale
    }
    findings.append(finding)

assert len(candidates) == 60
assert len(findings) == 60

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Conventional written intake
written_intake = [
    {
        "paper_id": "Old_Questions/Direct_2019-2020/ADA, AA & ATA General English.pdf",
        "section": "SECTION - A (40 Marks)",
        "question_number": "1",
        "physical_page": 1,
        "marks": 20,
        "task_type": "essay_writing",
        "prompt": "Write an essay on any one of the following topics: Relation between Man and the Environment; Importance of Education in life; Role of women in Mizo society; Importance of Information Technology at the present time.",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/essay"
        },
        "reason_unextracted": "Conventional descriptive essay composition task with 4 topic choices, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2019-2020/ADA, AA & ATA General English.pdf",
        "section": "SECTION - A (40 Marks)",
        "question_number": "2",
        "physical_page": 1,
        "marks": 20,
        "task_type": "précis_writing",
        "prompt": "Read the given passages carefully and write a précis in about 1/3rd of the original. Give a suitable title of the précis: When we survey our lives and efforts we soon observe that almost the whole of our actions and desires are bound up with the existence of other human beings... (approx 300 words on human interdependence, society, and individuality).",
        "taxonomy_target": {
            "subject_id": "english",
            "topic_id": "english/writing",
            "subtopic_id": "english/writing/precis"
        },
        "reason_unextracted": "Conventional descriptive précis condensation task, excluded from automated MCQ database ingestion."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")

summary = {
    "batch": 45,
    "paper": {
        "paper_id": "Old_Questions/Direct_2019-2020/ADA, AA & ATA General English.pdf",
        "paper_title": "Competitive Examinations for Recruitment to the Posts of Assistant Auditor, Assistant Treasury Accountant & Assistant Divisional Accountant (January 2019) — General English",
        "document_id": "doc_28eafb04c21bfc501a33c583",
        "sha256": "596901764877688d6dfb8d80f82dfbc9d9cba916fa9044cc10b067d5cf2c5ea4",
        "targets": 60
    },
    "single_booklet_deduplication": {
        "enforced": True,
        "primary_booklet": "Single booklet examination (doc_28eafb04c21bfc501a33c583)",
        "bypassed_siblings": [],
        "redundant_reviews_saved": 0
    },
    "targets": 60,
    "completion": "100% of extracted MCQs reviewed for ADA, AA & ATA General English (2019)",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "conventional_marks_preserved": 40,
    "ocr_dropped_mcqs_documented": 0,
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted conventional items.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
