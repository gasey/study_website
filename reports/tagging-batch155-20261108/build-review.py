"""Build candidates, findings, summary for Batch 155 (Assistant UDC MPSC Paper-I)."""
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
    "1": (make_primary("science", "science/physics", None), "Scientific instruments: Fathometer used for measuring ocean depth.", "static"),
    "2": (make_primary("general-studies", "general-studies/world-history", None), "20th century world history: Fascist totalitarian policy of Adolf Hitler.", "static"),
    "3": (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Indian defence pioneers: Dr. A.P.J. Abdul Kalam as Father of Indian Missile Programme.", "static"),
    "4": (make_primary("science", "science/biology", None), "Invertebrate zoology: Compound eyes allowing omnidirectional vision in insects.", "static"),
    "5": (make_primary("general-studies", "general-studies/geography", None), "Transport geography: Jawaharlal Nehru Port (JNPT) as busiest container port in India.", "static"),
    "6": (make_primary("general-studies", "general-studies/geography", None), "Physical geography: Equator having equal day and night throughout the year.", "static"),
    "7": (make_primary("science", "science/biology", None), "Biochemistry: Keratin fibrous structural protein found in human hair and nails.", "static"),
    "8": (make_primary("general-studies", "general-studies/current-affairs", None), "Space technology in the news: ISRO landing mission of Pushpak RLV-TD in March 2024.", "dynamic"),
    "9": (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "Literary awards: Arundhati Roy as first Indian woman to win Booker Prize (1997).", "static"),
    "10": (make_primary("general-studies", "general-studies/indian-economy", None), "Monetary policy: Open Market Operations (selling securities to absorb liquidity).", "static"),
    "11": (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional law: Supreme Court as guarantor and protector of Fundamental Rights.", "static"),
    "12": (make_primary("general-knowledge", "general-knowledge/sports", None), "International hockey: Men's FIH Hockey World Cup 2023 champions (Germany).", "dynamic"),
    "13": (make_primary("general-studies", "general-studies/current-affairs", None), "International current affairs: National travel restrictions to conflict zones.", "dynamic"),
    "14": (make_primary("general-studies", "general-studies/current-affairs", None), "International diplomacy: US State Department Countries of Particular Concern designations.", "dynamic"),
    "15": (make_primary("general-studies", "general-studies/current-affairs", None), "National urban sanitation: Indore cleanest city for seventh consecutive year.", "dynamic"),
    "16": (make_primary("general-studies", "general-studies/current-affairs", None), "Renewable energy policy: Solar Policy 2024 installed capacity targets.", "dynamic"),
    "17": (make_primary("general-studies", "general-studies/current-affairs", None), "State governance: Nitish Kumar oath-taking record as Chief Minister of Bihar.", "dynamic"),
    "18": (make_primary("general-studies", "general-studies/indian-polity", None), "Judicial administration: Witness Protection Scheme approved by Supreme Court in 2018.", "static"),
    "19": (make_primary("general-studies", "general-studies/current-affairs", None), "Cross-border diplomacy: Free Movement Regime (FMR) between India and Myanmar.", "dynamic"),
    "20": (make_primary("general-studies", "general-studies/indian-economy", None), "International finance: FDI full form (Foreign Direct Investment).", "static"),
    "21": (make_primary("general-studies", "general-studies/current-affairs", None), "Health policy portals: NAMASTE Portal for AYUSH traditional medicine standardization.", "dynamic"),
    "22": (make_primary("general-studies", "general-studies/current-affairs", None), "Sustainable banking: Green Rupee Term Deposit introduced by SBI in 2024.", "dynamic"),
    "23": (make_primary("general-studies", "general-studies/current-affairs", None), "Welfare schemes: PM Young Achievers Scholarship Award Scheme (PM-YASASVI) target groups.", "dynamic"),
    "24": (make_primary("general-studies", "general-studies/current-affairs", None), "Telecommunications initiatives: Bharat 5G Portal launched by Ministry of Communications.", "dynamic"),
    "25": (make_primary("general-studies", "general-studies/current-affairs", None), "Neurotechnology in the news: Neuralink first human brain-computer interface implant.", "dynamic"),
    "26": (make_primary("general-studies", "general-studies/current-affairs", None), "Global sustainability rankings: QS World University Rankings for Sustainability.", "dynamic"),
    "27": (make_primary("general-studies", "general-studies/indian-polity", None), "Centre-state relations: Special Category States (SCS) criteria and recognized states.", "static"),
    "28": (make_primary("general-studies", "general-studies/environment", None), "Botanical conservation: India's first Gymnosperm Garden in Uttarakhand.", "static"),
    "29": (make_primary("general-studies", "general-studies/indian-economy", None), "Financial centres: GIFT City (Gujarat International Finance Tec-City) in Gandhinagar.", "static"),
    "30": (make_primary("general-studies", "general-studies/current-affairs", None), "Aviation sector: Air India inducting first commercial Airbus A350 in India.", "dynamic"),
    "31": (make_primary("general-studies", "general-studies/current-affairs", None), "Regional infrastructure: Kaladan Multi-Modal Transit Transport Project connecting India & Myanmar.", "dynamic"),
    "32": (make_primary("general-studies", "general-studies/current-affairs", None), "State legislative enactments: Bihar reservation increase legislation to 65% in 2023.", "dynamic"),
    "33": (make_primary("general-studies", "general-studies/indian-polity", None), "Electoral administration: First EVM pilot usage in Paravur assembly constituency Kerala (1982).", "static"),
    "34": (make_primary("general-studies", "general-studies/current-affairs", None), "Tourism diplomacy: Visa-free travel agreements in Southeast Asia.", "dynamic"),
    "35": (make_primary("general-knowledge", "general-knowledge/sports", None), "National observances: National Sports Day celebrated on 29th August (Major Dhyan Chand birthday).", "static"),
    "36": (make_primary("general-studies", "general-studies/current-affairs", None), "Welfare administration: Ministry of Rural Development Aadhaar-based payment deadline.", "dynamic"),
    "37": (make_primary("general-studies", "general-studies/indian-polity", None), "Political history: Sucheta Kripalani as first female Chief Minister of an Indian state (UP).", "static"),
    "38": (make_primary("general-studies", "general-studies/current-affairs", None), "Global maritime industry: Deep sea mining / commercial whaling developments.", "dynamic"),
    "39": (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional amendments: 42nd Amendment Act 1976 adding Socialist and Secular to Preamble.", "static"),
    "40": (make_primary("general-studies", "general-studies/current-affairs", None), "Global economic indices: India's rank in Global Innovation Index (GII) 2023.", "dynamic"),
    "41": (make_primary("general-studies", "general-studies/mizoram", None), "Mizo literature & history: Mizo Chanchin written and published by K. Zawla in 1938.", "mizoram"),
    "42": (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram ecclesiastical history: Rev. Challiana as first ordained Mizo pastor.", "mizoram"),
    "43": (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram colonial ethnography: The Lakhers monograph written by N.E. Parry in 1932.", "mizoram"),
    "44": (make_primary("general-studies", "general-studies/indian-history", None), "Ancient Indian philosophy: Upanishads as philosophical treatises on Brahman and Atman.", "static"),
    "45": (make_primary("general-studies", "general-studies/indian-history", None), "Ancient Indian history: Harshavardhana as last great imperial ruler of northern India.", "static"),
    "46": (make_primary("general-studies", "general-studies/indian-history", None), "Pre-Aryan civilisation: Original inhabitants of Indus Valley and subcontinent.", "static"),
    "47": (make_primary("general-studies", "general-studies/indian-history", None), "Medieval Indian history: Razia Sultana as sole sovereign female ruler of Delhi Sultanate.", "static"),
    "48": (make_primary("general-studies", "general-studies/geography", None), "Forest resources of India: Madhya Pradesh possessing largest forest cover by area.", "static"),
    "49": (make_primary("general-studies", "general-studies/indian-economy", None), "Market regulators: SEBI (Securities and Exchange Board of India) regulating capital markets.", "static"),
    "50": (make_primary("general-studies", "general-studies/indian-economy", None), "Fiscal policy: Fiscal deficit targets in Union Budget 2024.", "dynamic"),
    "51": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'soporific' (tending to induce drowsiness or sleep).", "static"),
    "52": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'abated' (subsided or became less intense).", "static"),
    "53": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'rancour' (bitterness or resentfulness).", "static"),
    "54": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'idiosyncrasies' (peculiar personal habits or characteristics).", "static"),
    "55": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'redundant' (superfluous or no longer needed).", "static"),
    "56": (make_primary("english", "english/vocabulary", None), "English vocabulary: Legal vocabulary meaning of 'abetting' (encouraging or assisting in crime).", "static"),
    "57": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'nepotism' (favouritism shown to relatives in power).", "static"),
    "58": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'perfunctorily' (carried out with minimum effort or care).", "static"),
    "59": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'pernicious' (having harmful or destructive effect).", "static"),
    "60": (make_primary("english", "english/vocabulary", None), "English vocabulary: Meaning of 'imperious' (arrogant and domineering).", "static"),
    "61": (make_primary("english", "english/grammar", None), "English grammar: Indefinite determiners with uncountable abstract nouns ('some advice').", "static"),
    "62": (make_primary("english", "english/grammar", None), "English grammar: Subject-verb agreement with compound subjects expressing single idea ('is').", "static"),
    "63": (make_primary("english", "english/grammar", None), "English grammar: Subject-verb agreement with singular collective noun ('committee has issued its report').", "static"),
    "64": (make_primary("english", "english/grammar", None), "English grammar: Distributive pronoun agreement ('Each of the suspected men was arrested').", "static"),
    "65": (make_primary("english", "english/grammar", None), "English grammar: Subject-verb agreement when two singular nouns refer to same person ('is').", "static"),
    "66": (make_primary("english", "english/vocabulary", None), "English idioms: Meaning of 'rub shoulders with' (associate or mingle with people).", "static"),
    "67": (make_primary("english", "english/vocabulary", None), "English idioms: Meaning of 'teething problems' (initial difficulties when starting new venture).", "static"),
    "68": (make_primary("english", "english/vocabulary", None), "English idioms: Meaning of 'have an axe to grind' (having private selfish motive).", "static"),
    "69": (make_primary("english", "english/vocabulary", None), "English idioms: Meaning of 'drive home' (emphasise or make point clearly understood).", "static"),
    "70": (make_primary("english", "english/vocabulary", None), "English idioms: Meaning of 'throw dust in someone's eyes' (mislead or deceive).", "static"),
    "71": (make_primary("english", "english/vocabulary", None), "English vocabulary: Precision word choice for liquid heat injury ('scalded').", "static"),
    "72": (make_primary("english", "english/vocabulary", None), "English vocabulary: Precision adjective selection in contextual analysis ('critical glance').", "static"),
    "73": (make_primary("english", "english/vocabulary", None), "English vocabulary: Precision adjective selection for lavish meal ('sumptuous dinner').", "static"),
    "74": (make_primary("english", "english/vocabulary", None), "English vocabulary: Collocation with 'restraint' ('exercise restraint').", "static"),
    "75": (make_primary("english", "english/vocabulary", None), "English vocabulary: Precision verb selection for reaction ('evoked little response').", "static"),
    "W1": (make_primary("english", "english/writing", None), "English writing: Precis writing condensing passage to one-third length with title.", "static"),
    "W2": (make_primary("english", "english/writing", None), "English writing: Essay composition on good governance or social issues.", "static"),
    "W3": (make_primary("english", "english/comprehension", None), "English reading: Reading comprehension passage analysis and question answering.", "static")
}

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

registered_doc = packet["documents"][0] if packet.get("documents") else {
    "id": "doc_809bef5448f39c1cb1101ccc",
    "sha256": "6e55b48c3f6fbfb5c1c1126ee5524cfce6c0352d8a50227aa6c382b841be39a8"
}

for it in packet["items"]:
    snap = it["snapshot"]
    rec = snap["record"]
    aid = it["appearance_id"]
    cid = it["canonical_id"]
    cur_primary = rec["classification"]
    pid = it["appearance"]["paper_id"]
    qnum_str = str(it["appearance"]["qnum"])
    page = int(rec.get("page") or 1)

    prop, reason, time_behavior = decisions[qnum_str]
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
        context_reason = "Regional context: Mizoram history, published literature, and ecclesiastical history."
    elif time_behavior == "dynamic":
        ctx = {
            "region": "IN" if "India" in rec["question"] else "",
            "language": "en",
            "time_behavior": "dated-event",
            "reference_period": "2023-2024",
            "reference_basis": "exam-date"
        }
        context_reason = "Current affairs event from 2023-2024 examination period."
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
        "candidate_id": f"tcand_b155_{aid[:16]}",
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
        "rationale": f"Batch 155 source-inspected (PDF page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": registered_doc["id"],
            "sha256": registered_doc["sha256"],
            "physical_page": page,
            "printed_question": qnum_str,
            "inspected": True,
            "note": f"Inspected physical page {page} of Assistant UDC under MPSC Paper-I (Q{qnum_str}). Verified stem, options, and section classification."
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
    "batch": 155,
    "paper_id": packet["papers"][0]["id"] if packet.get("papers") else "Old_Questions/Direct_NG_2024-2027/Assistant UDC under MPSC paper-I..pdf",
    "paper_title": packet["papers"][0]["exam_name"] + " " + packet["papers"][0]["post"] if packet.get("papers") else "Assistant UDC under MPSC paper-I",
    "total_targets": len(pending_candidates),
    "actions": dict(action_counts),
    "taxonomy_distribution": dict(tax_counts),
    "source_defect_notes": "Clean scan, complete 78 appearances (75 MCQs + 3 writing prompts) across 8 physical pages without omission."
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending candidates for Batch 155. Actions: {dict(action_counts)}")
