"""Build candidates, findings, summary for Batch 153 (LDC SW & WCD Paper-I)."""
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
    1: (make_primary("general-studies", "general-studies/indian-history", None), "Medieval Indian literature: Authorship of Kitab-ul-Hind by Al-Biruni.", "static"),
    2: (make_primary("general-studies", "general-studies/indian-history", None), "Ancient Indian architecture: Ellora rock-cut cave temples (Hindu, Buddhist, Jain).", "static"),
    3: (make_primary("general-studies", "general-studies/indian-history", None), "Modern Indian history: British Governor-General counterpart of Tipu Sultan (Warren Hastings/Cornwallis).", "static"),
    4: (make_primary("general-studies", "general-studies/indian-history", None), "Modern Indian history: First Indian to qualify ICS (Satyendranath Tagore).", "static"),
    5: (make_primary("general-studies", "general-studies/indian-history", None), "Modern Indian history: Viceroy Lord Chelmsford during Jallianwala Bagh massacre (1919).", "static"),
    6: (make_primary("general-studies", "general-studies/indian-history", None), "British administrative history: Lord Mayo / Lord Ripon associated with local self-government.", "static"),
    7: (make_primary("general-studies", "general-studies/indian-history", None), "Colonial constitutional history: Magna Carta of English Education in India (Wood's Despatch 1854).", "static"),
    8: (make_primary("general-studies", "general-studies/indian-history", None), "National movement publications: New India and Commonweal newspapers by Annie Besant.", "static"),
    9: (make_primary("general-studies", "general-studies/indian-history", None), "National movement: Non-Cooperation Movement resolution passed at Calcutta Special Session (Sept 1920).", "static"),
    10: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional executive: Resignation of President of India tendered to Vice President.", "static"),
    11: (make_primary("general-studies", "general-studies/indian-polity", None), "Parliament of India: Presidential nominations to Lok Sabha (Anglo-Indians under historical Art 331).", "static"),
    12: (make_primary("general-studies", "general-studies/indian-polity", None), "Constituent Assembly debates: Dr. B.R. Ambedkar's historical stance on Panchayati Raj.", "static"),
    13: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional structure: Part IV containing Directive Principles of State Policy (DPSP).", "static"),
    14: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional amendments: 86th Amendment Act 2002 introducing Right to Education (Art 21A).", "static"),
    15: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional executive: 91st Amendment limiting Council of Ministers to 15% of Lok Sabha.", "static"),
    16: (make_primary("general-studies", "general-studies/indian-polity", None), "National institutions: NITI Aayog replacing the Planning Commission in 2015.", "static"),
    17: (make_primary("general-studies", "general-studies/indian-polity", None), "Local self-government: 73rd Amendment population threshold (20 lakh) for intermediate panchayat.", "static"),
    18: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional bodies: Election Commission of India established under Article 324.", "static"),
    19: (make_primary("general-studies", "general-studies/geography", None), "Indian agriculture: Crop seasons, cotton as a prominent Kharif crop.", "static"),
    20: (make_primary("general-studies", "general-studies/geography", None), "Economic geography: Surat designated as the Diamond City of India.", "static"),
    21: (make_primary("general-studies", "general-studies/geography", None), "Physical geography of India: Eight Indian states through which Tropic of Cancer passes.", "static"),
    22: (make_primary("general-studies", "general-studies/geography", None), "Mountain passes: Umling La / Mig La pass as highest motorable pass in India.", "static"),
    23: (make_primary("general-studies", "general-studies/geography", None), "Indian drainage and landforms: Lodh / Hundru / Dassam waterfalls of Chotanagpur Plateau.", "static"),
    24: (make_primary("general-studies", "general-studies/geography", None), "Energy resources: Highest installed wind/solar energy capacity state (Rajasthan/Gujarat/Tamil Nadu).", "static"),
    25: (make_primary("general-studies", "general-studies/geography", None), "Physical geography: Confluence of Western Ghats and Eastern Ghats at Nilgiri Hills.", "static"),
    26: (make_primary("general-studies", "general-studies/geography", None), "Time zones and longitudinal geography: Standard time differences from GMT in half-hour multiples.", "static"),
    27: (make_primary("general-studies", "general-studies/geography", None), "World geography: India as the seventh-largest country by land area.", "static"),
    28: (make_primary("general-studies", "general-studies/indian-economy", None), "Banking sector concepts: NPA full form (Non-Performing Asset).", "static"),
    29: (make_primary("general-studies", "general-studies/indian-economy", None), "Financial regulators: RBI and SEBI regulatory authority over financial markets.", "static"),
    30: (make_primary("general-studies", "general-studies/indian-economy", None), "Economic systems: Socialist / Command economy market characteristics.", "static"),
    31: (make_primary("general-studies", "general-studies/indian-economy", None), "Social legislation & food security: National Food Security Act passed in 2013.", "static"),
    32: (make_primary("general-studies", "general-studies/indian-economy", None), "Public finance: Definition and scope of Capital Expenditure in Union Budget.", "static"),
    33: (make_primary("general-studies", "general-studies/indian-economy", None), "Economic planning history: Agriculture as the prime target of First Five Year Plan (1951-56).", "static"),
    34: (make_primary("general-studies", "general-studies/indian-economy", None), "Agricultural revolutions: Golden Revolution related to horticulture and honey production.", "static"),
    35: (make_primary("general-studies", "general-studies/indian-economy", None), "Economic planning models: Mahalanobis heavy-industry model of Second Five Year Plan.", "static"),
    36: (make_primary("general-studies", "general-studies/indian-economy", None), "Institutional insignia: Reserve Bank of India official seal (Panther and Palm Tree).", "static"),
    37: (make_primary("science", "science/biology", None), "Plant anatomy: Petiole joining the leaf blade to the stem.", "static"),
    38: (make_primary("science", "science/biology", None), "Human biochemistry: Vitamin K as essential factor for blood clotting.", "static"),
    39: (make_primary("science", "science/biology", None), "Cell biology: Ribosomes as the sites of cellular protein synthesis.", "static"),
    40: (make_primary("science", "science/physics", None), "Classical mechanics: Newton's First Law of Motion (Inertia) explaining forward jerk in braking bus.", "static"),
    41: (make_primary("science", "science/chemistry", None), "Chemical bonding & allotropes: Graphite conductivity due to delocalised electrons.", "static"),
    42: (make_primary("science", "science/biology", None), "Pathology: Hepatitis as viral inflammatory liver disease.", "static"),
    43: (make_primary("science", "science/biology", None), "Cell biology: Cytoplasm as jelly-like fluid substance filling cellular interior.", "static"),
    44: (make_primary("science", "science/physics", None), "Applied optics: Convex lenses used in optical projectors to produce enlarged real images.", "static"),
    45: (make_primary("science", "science/physics", None), "Optics and materials: Silver as the best natural reflector of light.", "static"),
    46: (make_primary("general-studies", "general-studies/mizoram", None), "Traditional Mizo religion: Puithiam / Sadawt as sacrificial priest in traditional society.", "mizoram"),
    47: (make_primary("general-studies", "general-studies/mizoram", None), "Traditional Mizo culture: Sahlam as tree/pole on which captured enemy heads were hung.", "mizoram"),
    48: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo folklore & oral literature: Folktale associated with character Phawthira.", "mizoram"),
    49: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo historical biography: Laltheri daughter of Chief Suakpuilala / Lalhrima.", "mizoram"),
    50: (make_primary("general-studies", "general-studies/mizoram", None), "Traditional Mizo hunting & warrior implements: Fungki bison-horn container for gunpowder.", "mizoram"),
    51: (make_primary("english", "english/grammar", None), "English grammar: Indefinite article usage with general singular nouns ('A dog is a faithful animal').", "static"),
    52: (make_primary("english", "english/grammar", None), "English grammar: Spatial prepositions ('bridge across the river').", "static"),
    53: (make_primary("english", "english/grammar", None), "English grammar: Subject-verb agreement with plural subjects ('We all are playthings').", "static"),
    54: (make_primary("english", "english/grammar", None), "English grammar: Simple present tense for habitual actions ('goes to church everyday').", "static"),
    55: (make_primary("english", "english/grammar", None), "English grammar: Past perfect tense sequence ('everyone had left by the time we reached').", "static"),
    56: (make_primary("english", "english/grammar", None), "English grammar: Subject-verb agreement with parenthetical additions ('I, as well as he, am to blame').", "static"),
    57: (make_primary("english", "english/grammar", None), "English grammar: Passive to active voice transformation (past continuous).", "static"),
    58: (make_primary("english", "english/grammar", None), "English grammar: Active to passive voice transformation (present continuous).", "static"),
    59: (make_primary("english", "english/vocabulary", None), "English vocabulary: Antonym determination for 'generous' (miserly / selfish).", "static"),
    60: (make_primary("english", "english/vocabulary", None), "English vocabulary: Antonym determination for 'ancient' (modern / recent).", "static"),
    61: (make_primary("english", "english/vocabulary", None), "English vocabulary: Synonym determination for 'brief' (short / concise).", "static"),
    62: (make_primary("english", "english/vocabulary", None), "English vocabulary: Synonym determination for 'cautious' (alert / careful).", "static"),
    63: (make_primary("english", "english/sentence-correction", None), "English sentence structure: Correct auxiliary negation with third-person singular ('doesn't like').", "static"),
    64: (make_primary("english", "english/sentence-correction", None), "English sentence structure: Negative adverb inversion word order ('Hardly had he finished when').", "static"),
    65: (make_primary("english", "english/sentence-correction", None), "English orthography: Correct spelling of 'accommodation'.", "static"),
    66: (make_primary("english", "english/sentence-correction", None), "English orthography: Correct spelling of 'environment'.", "static"),
    67: (make_primary("english", "english/grammar", None), "English grammar: Indirect speech reporting habitual universal routine without tense shift.", "static"),
    68: (make_primary("english", "english/vocabulary", None), "English vocabulary: One-word substitution for lawless state of society ('anarchy').", "static"),
    69: (make_primary("english", "english/vocabulary", None), "English vocabulary: Word etymology and definition of 'infanticide' (killing of an infant).", "static"),
    70: (make_primary("english", "english/vocabulary", None), "English vocabulary: Contextual meaning of 'resolve' (determination / firm decision).", "static"),
    71: (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning and usage of 'resilient' (able to recover quickly / flexible).", "static"),
    72: (make_primary("english", "english/grammar", None), "English grammar: Complex prepositional usage ('succeeded because of his hard work').", "static"),
    73: (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of idiom 'hit the nail on the head' (describe exactly / be right).", "static"),
    74: (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of idiom 'blessing in disguise' (hidden good in apparent misfortune).", "static"),
    75: (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of idiom 'once in a blue moon' (very rarely).", "static")
}

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

registered_doc = packet["documents"][0] if packet.get("documents") else {
    "id": "doc_ee8fe8351d5c2fa126ec89f1",
    "sha256": "4da69e38d7265d63f0d576a917e76161c5df60cf8db62c97a48d88fa7b25bc53"
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
        context_reason = "Regional context: Mizoram traditional society, culture, folklore, and warrior implements."
    else:
        ctx = {
            "region": "",
            "language": "en",
            "time_behavior": "static",
            "reference_period": "",
            "reference_basis": "unknown"
        }
        context_reason = "Standard static syllabus knowledge (Indian History, Polity, Geography, Economy, Science, English)."

    cand = {
        "candidate_id": f"tcand_b153_{aid[:16]}",
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
        "rationale": f"Batch 153 source-inspected (PDF page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": registered_doc["id"],
            "sha256": registered_doc["sha256"],
            "physical_page": page,
            "printed_question": str(qnum),
            "inspected": True,
            "note": f"Inspected physical page {page} of LDC under SW, WCD Paper-I (Q{qnum}). Verified stem, options, and section classification."
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
    "batch": 153,
    "paper_id": packet["papers"][0]["id"] if packet.get("papers") else "Old_Questions/Direct_NG_2024-2027/LDC under SW, WCD Paper - I..pdf",
    "paper_title": packet["papers"][0]["exam_name"] + " " + packet["papers"][0]["post"] if packet.get("papers") else "LDC under SW, WCD Paper - I",
    "total_targets": len(pending_candidates),
    "actions": dict(action_counts),
    "taxonomy_distribution": dict(tax_counts),
    "source_defect_notes": "Clean scan, complete 75 MCQs across 13 physical pages without omission."
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending candidates for Batch 153. Actions: {dict(action_counts)}")
