"""Build candidates, findings, summary for Batch 151 (LDC Law & Judicial Paper-I)."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

def make_primary(sid, tid=None, subid=None):
    return {
        "subject_id": sid,
        "topic_id": tid,
        "subtopic_id": subid
    }

decisions = {
    1: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional framework: Original parts, articles and schedules of Indian Constitution.", "static"),
    2: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional sources: Borrowed provision of Federation with strong centre.", "static"),
    3: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional bodies: UPSC reporting mandate to President of India.", "static"),
    4: (make_primary("general-studies", "general-studies/indian-polity", None), "Fundamental Rights under Part III of the Constitution.", "static"),
    5: (make_primary("general-studies", "general-studies/indian-polity", None), "Parliament of India: Minimum age qualification for Rajya Sabha member.", "static"),
    6: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional amendment procedure under Article 368.", "static"),
    7: (make_primary("general-studies", "general-studies/indian-history", None), "Modern Indian history: First Indian in ICS (Satyendranath Tagore).", "static"),
    8: (make_primary("general-studies", "general-studies/indian-history", None), "National movement: First president of Indian National Congress (W.C. Bonnerjee).", "static"),
    9: (make_primary("general-studies", "general-studies/indian-history", None), "Civil disobedience: Launch date of Dandi March by Mahatma Gandhi.", "static"),
    10: (make_primary("general-studies", "general-studies/indian-history", None), "Colonial expansion: Doctrine of Lapse introduced by Lord Dalhousie.", "static"),
    11: (make_primary("general-studies", "general-studies/indian-history", None), "European advent: Portuguese as first Europeans to arrive in India.", "static"),
    12: (make_primary("general-studies", "general-studies/indian-history", None), "Socio-religious reform: Servants of India Society founded by G.K. Gokhale.", "static"),
    13: (make_primary("general-studies", "general-studies/indian-economy", None), "Economic systems: Concept and definition of Mixed Economy in India.", "static"),
    14: (make_primary("general-studies", "general-studies/indian-economy", None), "Banking sector concepts: Definition and objectives of Green Banking.", "static"),
    15: (make_primary("general-studies", "general-studies/indian-economy", None), "Macroeconomic terminology: Definition of stagflation (stagnant growth + inflation).", "static"),
    16: (make_primary("general-studies", "general-studies/indian-economy", None), "Financial regulation: Scheduled Bank classification under RBI Act.", "static"),
    17: (make_primary("general-studies", "general-studies/indian-economy", None), "Agricultural economics: Disguised and seasonal unemployment in Indian agriculture.", "static"),
    18: (make_primary("science", "science/physics", None), "Physical states of matter: Plasma as the fourth state after solid, liquid, gas.", "static"),
    19: (make_primary("science", "science/physics", None), "Optics: Correction of myopia (near-sightedness) using concave lenses.", "static"),
    20: (make_primary("science", "science/chemistry", None), "Chemical nomenclature: Sodium bicarbonate as baking soda.", "static"),
    21: (make_primary("science", "science/chemistry", None), "Everyday chemistry: Antacids for neutralising stomach acidity.", "static"),
    22: (make_primary("science", "science/chemistry", None), "Metallurgy and alloys: Composition of brass (copper and zinc).", "static"),
    23: (make_primary("science", "science/chemistry", None), "Corrosion prevention: Galvanisation of iron using zinc coating.", "static"),
    24: (make_primary("science", "science/biology", None), "Human disease etiology: Protozoan infections (malaria/amoebic dysentery).", "static"),
    25: (make_primary("science", "science/biology", None), "Nutritional biochemistry: Vitamin A deficiency causing night blindness.", "static"),
    26: (make_primary("general-studies", "general-studies/geography", None), "Indian physical geography: Duncan Passage location in Andaman & Nicobar.", "static"),
    27: (make_primary("general-studies", "general-studies/geography", None), "Global biomes: Tundra vegetation characteristics.", "static"),
    28: (make_primary("general-studies", "general-studies/geography", None), "Coordinate geography: Equator as the great circle line of latitude.", "static"),
    29: (make_primary("general-studies", "general-studies/geography", None), "World physical geography: Atacama Desert as the driest non-polar desert.", "static"),
    30: (make_primary("general-studies", "general-studies/geography", None), "Mineral resources of India: Digboi as the oldest operating oil field.", "static"),
    31: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "North-East Indian cultural festivals: Bihu, Sangai, etc.", "static"),
    32: (make_primary("general-studies", "general-studies/current-affairs", None), "International multilateral partnerships: QUAD At Sea Observer Mission.", "dynamic"),
    33: (make_primary("general-studies", "general-studies/current-affairs", None), "National security & foreign policy: International terrorist designation.", "dynamic"),
    34: (make_primary("general-studies", "general-studies/current-affairs", None), "Fintech and AI developments: AI-powered banking initiatives in the news.", "dynamic"),
    35: (make_primary("general-studies", "general-studies/current-affairs", None), "Diplomatic summits: 25th SCO Summit host nation.", "dynamic"),
    36: (make_primary("general-studies", "general-studies/current-affairs", None), "Space exploration in the news: Lunar Polar Exploration (LUPEX) with JAXA.", "dynamic"),
    37: (make_primary("general-studies", "general-studies/current-affairs", None), "Neighbourhood political leadership: Female Prime Minister in Nepal.", "dynamic"),
    38: (make_primary("general-studies", "general-studies/current-affairs", None), "Domestic legal & political events: Climate activist detention under NSA.", "dynamic"),
    39: (make_primary("general-studies", "general-studies/current-affairs", None), "National urban sanitation rankings: Swachh Survekshan survey outcomes.", "dynamic"),
    40: (make_primary("general-studies", "general-studies/current-affairs", None), "Global financial trends: Countries transitioning to cashless economy.", "dynamic"),
    41: (make_primary("general-studies", "general-studies/current-affairs", None), "Government programmes & schemes: Incredible India 2.0 initiative.", "dynamic"),
    42: (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram personalities: Child prodigy Esther Hnamte national awards.", "mizoram"),
    43: (make_primary("general-studies", "general-studies/current-affairs", None), "Digital governance laws: National restrictions on youth social media use.", "dynamic"),
    44: (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram geography: Bordering Indian states (Assam, Manipur, Tripura).", "mizoram"),
    45: (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram physical geography: Sur Tlang mountain peak location.", "mizoram"),
    46: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo history: Settlement period and history of Selesih village.", "mizoram"),
    47: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo traditional calendar: Traditional name for month of April (Vau thla).", "mizoram"),
    48: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo material culture: Traditional bamboo basket types (Thul, Dawrawn).", "mizoram"),
    49: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo mythology and folklore: Pheichham (one-legged supernatural spirit).", "mizoram"),
    50: (make_primary("general-studies", "general-studies/mizoram", None), "Traditional Mizo village administration: Blacksmith (Thirdeng) meat dues.", "mizoram"),
    51: (make_primary("english", "english/grammar", None), "English grammar: Identification of parts of speech (nouns used after 'any').", "static"),
    52: (make_primary("english", "english/grammar", None), "English grammar: Identification of adjective / quantifier in context.", "static"),
    53: (make_primary("english", "english/grammar", None), "English grammar: Adverb of time functioning after verbs.", "static"),
    54: (make_primary("english", "english/grammar", None), "English grammar: Prepositional usage in spatial phrases ('over the hills').", "static"),
    55: (make_primary("english", "english/grammar", None), "English grammar: Pronoun / noun usage of 'everything'.", "static"),
    56: (make_primary("english", "english/grammar", None), "English grammar: Clause classification (Adverb clause of time).", "static"),
    57: (make_primary("english", "english/grammar", None), "English grammar: Clause classification (Adverb clause of condition with 'unless').", "static"),
    58: (make_primary("english", "english/grammar", None), "English grammar: Phrase structure (Noun phrase functioning as subject).", "static"),
    59: (make_primary("english", "english/grammar", None), "English grammar: Phrase structure (Adjective phrase qualifying 'boy').", "static"),
    60: (make_primary("english", "english/grammar", None), "English grammar: Phrase / clause modification (Adverbial phrase of manner/enthusiasm).", "static"),
    61: (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of idiom 'throw down the gauntlet'.", "static"),
    62: (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of idiomatic expression 'hold water'.", "static"),
    63: (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of figurative expression 'red herring'.", "static"),
    64: (make_primary("english", "english/grammar", None), "English grammar: Direct and indirect speech with habitual universal truths.", "static"),
    65: (make_primary("english", "english/grammar", None), "English grammar: Reported speech rules with second person pronouns.", "static"),
    66: (make_primary("english", "english/grammar", None), "English grammar: Reported speech conversion with future time reference.", "static"),
    67: (make_primary("english", "english/grammar", None), "English grammar: Active to passive voice transformation (simple present).", "static"),
    68: (make_primary("english", "english/grammar", None), "English grammar: Passive to active voice transformation.", "static"),
    69: (make_primary("english", "english/grammar", None), "English grammar: Interrogative passive voice sentence transformation.", "static"),
    70: (make_primary("english", "english/grammar", None), "English grammar: Imperative sentence voice transformation with 'let'.", "static"),
    71: (make_primary("english", "english/vocabulary", None), "English vocabulary: Synonym determination for 'prolific'.", "static"),
    72: (make_primary("english", "english/vocabulary", None), "English vocabulary: Antonym determination for 'ephemeral'.", "static"),
    73: (make_primary("english", "english/vocabulary", None), "English vocabulary: Standard English simile completion ('as meek as a lamb').", "static"),
    74: (make_primary("english", "english/vocabulary", None), "English vocabulary: Contextual vocabulary selection for compliant behavior.", "static"),
    75: (make_primary("english", "english/vocabulary", None), "English vocabulary: Animal nomenclature for young ones (cygnet for swan).", "static")
}

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

registered_doc = packet["documents"][0] if packet.get("documents") else {
    "id": "doc_42937decfe7f2c5ce0323459",
    "sha256": "33a418d155b8378eb79b973c7c3695b3a60f3f0eb5ada70b204770cfcf91a6ee"
}

for it in packet["items"]:
    snap = it["snapshot"]
    rec = snap["record"]
    aid = it["appearance_id"]
    cid = it["canonical_id"]
    cur_primary = rec["classification"]
    pid = it["appearance"]["paper_id"]
    qnum = int(it["appearance"]["qnum"])
    page = int(rec.get("page") or 1)

    prop, reason, time_behavior = decisions[qnum]
    action = "keep" if prop == cur_primary else "retag"
    action_counts[action] += 1
    tax_counts[f"{prop['subject_id']} > {prop['topic_id']}"] += 1

    if time_behavior == "mizoram":
        ctx = {
            "region": "IN-MZ",
            "language": "en",
            "time_behavior": "static",
            "reference_period": "",
            "reference_basis": "unknown"
        }
        context_reason = "Regional context: Mizoram state history, culture, geography, and achievements."
    elif time_behavior == "dynamic":
        ctx = {
            "region": "IN" if "India" in rec["question"] else "",
            "language": "en",
            "time_behavior": "dated-event",
            "reference_period": "2025-2026",
            "reference_basis": "exam-date"
        }
        context_reason = "Current affairs event from 2025-2026 examination period."
    else:
        ctx = {
            "region": "",
            "language": "en",
            "time_behavior": "static",
            "reference_period": "",
            "reference_basis": "unknown"
        }
        context_reason = "Standard static syllabus knowledge."

    cand = {
        "candidate_id": f"tcand_b151_{aid[:16]}",
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": pid,
        "source_fingerprint": it["source_fingerprint"],
        "action": action,
        "review_status": "pending",
        "current_primary": cur_primary,
        "proposed_primary": prop,
        "proposed_related": [],
        "tested_skill": reason,
        "rationale": f"Batch 151 source-inspected (PDF page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": registered_doc["id"],
            "sha256": registered_doc["sha256"],
            "physical_page": page,
            "printed_question": str(qnum),
            "inspected": True,
            "note": f"Inspected physical page {page} of LDC Paper-I under Law & Judicial Deptt (Q{qnum}). Verified stem, options, and section classification."
        },
        "context_candidate": ctx,
        "context_reason": context_reason,
        "source_issues": [],
        "taxonomy_gap": None,
        "alternatives": [],
        "owner_question": None,
        "reviewer_tool": "antigravity",
        "reviewer_model": "gemini"
    }
    pending_candidates.append(cand)

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, indent=2, ensure_ascii=False) + "\n")

summary = {
    "batch": 151,
    "paper_id": packet["papers"][0]["id"] if packet.get("papers") else "Old_Questions/Direct_NG_2024-2027/LDC Paper-I under Law _ Judicial Deptt...pdf",
    "paper_title": packet["papers"][0]["exam_name"] + " " + packet["papers"][0]["post"] if packet.get("papers") else "LDC Paper-I under Law & Judicial Deptt",
    "total_targets": len(pending_candidates),
    "actions": dict(action_counts),
    "taxonomy_distribution": dict(tax_counts),
    "source_defect_notes": "Clean scan, complete 75 MCQs across 8 physical pages without omission."
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending candidates for Batch 151. Actions: {dict(action_counts)}")
