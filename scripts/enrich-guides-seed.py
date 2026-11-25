#!/usr/bin/env python3
"""Enrich web/src/data/guides-seed.json into beautifully structured, exam-ready
Concept Guides grounded in Finna's authored study materials and live MPSC PYQs:
- Upgrades Indian Polity Codex (21 chapters): authentic headings, comparison tables,
  exam traps, live Polity MCQ links, and Atlas map links
- Builds Mathematics & Arithmetic Formula Handbook (12 chapters from all 26 topics
  in arithmetic-content.json): mental models, formula grids, worked MPSC examples,
  reference tables, and direct subtopic MCQ links
- Builds Geography of India, World & Mizoram (11 chapters from authored Atlas data):
  mental models, comparison tables, Mizoram 3-river table, Biosphere Reserves table,
  and direct Geography/Environment/Mizoram MCQ + Atlas map links
- Builds Indian, World & Mizoram History (11 chapters from authored Atlas data):
  chronological tables (IVC sites, Buddhist Councils, Delhi Sultanate, 1857 centres,
  INC/Gandhian timeline, Mizoram 1871–1987), exam traps, and Chronicle/Atlas links
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path('/home/hruaia/workspace/projects/personal/finna')
GUIDES_SEED = ROOT / 'web/src/data/guides-seed.json'
ARITHMETIC_JSON = ROOT / 'web/src/data/arithmetic-content.json'
ATLAS_CHAPTERS = ROOT / 'web/src/atlas/data/chapters'

POLITY_HEADINGS = {
    'hist': '1. Historical Background (1773–1947)',
    'ca': '2. Constituent Assembly & Making of the Constitution',
    'preamble': '3. The Preamble',
    'union': '4. Union & Its Territory (Arts. 1–4)',
    'citizen': '5. Citizenship (Arts. 5–11)',
    'fr': '6. Fundamental Rights (Arts. 12–35)',
    'dpsp': '7. Directive Principles of State Policy (Arts. 36–51)',
    'fd': '8. Fundamental Duties (Art. 51A)',
    'amend': '9. Amendments & Basic Structure (Art. 368)',
    'parl': '10. Parliament & Legislative Procedure',
    'exec': '11. President, VP, PM, Governor & Council of Ministers',
    'judi': '12. Judiciary, Writs & PIL',
    'fed': '13. Federalism & Centre–State Relations',
    'emerg': '14. Emergency Provisions (Arts. 352, 356, 360)',
    'cbody': '15. Constitutional & Statutory Bodies',
    'rpa': '16. Elections & Representation of the People Act',
    'adl': '17. Anti-Defection Law & Political Parties',
    'local': '18. Local Government (73rd & 74th Amendments)',
    'sixth': '19. Sixth Schedule, Art. 371G & Mizoram ADCs',
    'pg': '20. Pressure Groups & Civil Society',
    'comp': '21. Comparative Constitutions & High-Yield Tables',
}

POLITY_ATLAS_MAP = {
    'ca': '/atlas/polity-making-of-constitution',
    'union': '/atlas/polity-states-reorganisation',
    'parl': '/atlas/polity-parliament',
    'judi': '/atlas/polity-judiciary',
    'sixth': '/atlas/polity-sixth-schedule',
}

POLITY_ENHANCEMENTS: dict[str, dict[str, str]] = {
    'hist': {
        'model': 'British constitutional evolution moved in two clear eras: Company Rule (1773–1858, centralising power in Calcutta) and Crown Rule (1858–1947, slowly introducing Indian legislatures and provincial autonomy).',
        'table': (
            '### Landmark Acts at a Glance\n\n'
            '| Act | Key Shift | High-Yield Exam Detail |\n'
            '| --- | --- | --- |\n'
            '| Regulating Act 1773 | Governor-General of Bengal | Warren Hastings; Supreme Court at Calcutta (1774) |\n'
            '| Charter Act 1833 | Governor-General of India | Lord William Bentinck; ended EIC commercial role |\n'
            '| GoI Act 1858 | Crown Rule begins | Viceroy of India (Lord Canning); Secretary of State |\n'
            '| Indian Councils Act 1909 | Morley–Minto Reforms | Separate electorates for Muslims |\n'
            '| GoI Act 1919 | Montagu–Chelmsford | Provincial dyarchy; bicameralism & direct elections |\n'
            '| GoI Act 1935 | Blueprint of 1950 Constitution | Provincial autonomy; Federal Court (1937); 3 lists |'
        ),
        'trap': 'Do not confuse **Dyarchy in Provinces** (GoI Act 1919) with **Provincial Autonomy** (GoI Act 1935, which abolished provincial dyarchy and proposed dyarchy at the Centre).',
    },
    'ca': {
        'model': 'The Constituent Assembly (389 members, Cabinet Mission Plan 1946) worked through 8 major committees — knowing the chair of each committee answers a third of all making-of-the-Constitution MCQs.',
        'trap': 'Dr. Sachchidananda Sinha was the **temporary** President (9 Dec 1946); **Dr. Rajendra Prasad** was elected permanent President (11 Dec 1946); **B.N. Rau** was the Constitutional Advisor. From the North East, **Syed Muhammad Saadulla** (Assam) served on the Drafting Committee.',
    },
    'preamble': {
        'model': 'The Preamble states the source of authority (We, the People), the nature of the Indian state (Sovereign, Socialist, Secular, Democratic, Republic), and its four objectives (Justice, Liberty, Equality, Fraternity).',
        'hook': '**42nd Amendment (1976)** added exactly three words — **S-S-I**: **Socialist, Secular, Integrity**. The Preamble has been amended only **once**.',
    },
    'fr': {
        'model': 'Fundamental Rights (Part III, Arts. 12–35) are enforceable directly in the Supreme Court (Art. 32) and High Courts (Art. 226) — they act primarily as shields against arbitrary State action.',
        'table': (
            '### The Six Fundamental Rights\n\n'
            '| Right | Articles | Signature Provisions |\n'
            '| --- | --- | --- |\n'
            '| Right to Equality | Arts. 14–18 | Rule of law (14), Untouchability abolished (17), Titles abolished (18) |\n'
            '| Right to Freedom | Arts. 19–22 | 6 freedoms (19), Life & liberty (21), Education 6–14 yrs (21A) |\n'
            '| Against Exploitation | Arts. 23–24 | Forced labour banned (23), Child labour <14 in factories banned (24) |\n'
            '| Freedom of Religion | Arts. 25–28 | Conscience & propagation (25), Religious denominations (26) |\n'
            '| Cultural & Educational | Arts. 29–30 | Minority scripts/culture (29), Minority institutions (30) |\n'
            '| Constitutional Remedies | Art. 32 | Heart & Soul (Ambedkar); 5 Writs |'
        ),
        'trap': 'Right to Property was removed from Fundamental Rights by the **44th Amendment (1978)** and placed as a legal right under **Art. 300A**. Arts. **20 & 21** can never be suspended even during a National Emergency.',
    },
    'dpsp': {
        'model': 'DPSPs (Part IV, Arts. 36–51, borrowed from Ireland) are positive socio-economic goals for governance — fundamental to law-making, yet non-justiciable in court.',
        'hook': 'Key high-frequency DPSP numbers: **Art. 40** (Village Panchayats), **Art. 44** (Uniform Civil Code), **Art. 48A** (Environment & forests), **Art. 50** (Separation of judiciary from executive), **Art. 51** (International peace).',
    },
    'parl': {
        'model': 'Parliament = President + Lok Sabha + Rajya Sabha (Art. 79). Financial control rests decisively with the Lok Sabha, while federal safeguards sit with the Rajya Sabha.',
        'table': (
            '### Money Bill vs. Ordinary Bill\n\n'
            '| Feature | Money Bill (Art. 110) | Ordinary Bill |\n'
            '| --- | --- | --- |\n'
            '| Introduction | Lok Sabha only, with President’s prior recommendation | Either House |\n'
            '| Certification | Speaker of Lok Sabha (final) | Not required |\n'
            '| Rajya Sabha power | May delay max **14 days**; cannot amend or reject | Equal power; may amend or reject |\n'
            '| Joint Sitting (Art. 108) | **No** joint sitting | **Yes** (presided by LS Speaker) |'
        ),
        'trap': 'A **Vote on Account** funds government expenses during the gap between Budget presentation and passing of the Appropriation Bill. Joint sitting (Art. 108) is **never** available for Money Bills or Constitutional Amendment Bills (Art. 368).',
    },
    'exec': {
        'model': 'India runs a Parliamentary Executive: the President (Union) and Governor (State) are constitutional heads, while the Council of Ministers is collectively responsible to the directly elected lower house (Lok Sabha / Vidhan Sabha).',
        'trap': '**Art. 200** lets a Governor reserve a State Bill for the President’s consideration. Under **Art. 156**, a Governor holds office during the pleasure of the President (normal term 5 years, no impeachment procedure).',
    },
    'judi': {
        'model': 'India has an integrated single judicial hierarchy (SC → HCs → Subordinate Courts) with Judicial Review anchored in Arts. 13, 32, 136, and 226.',
        'table': (
            '### The Five Constitutional Writs\n\n'
            '| Writ | Literal Meaning | Issued For |\n'
            '| --- | --- | --- |\n'
            '| Habeas Corpus | To have the body | Release from unlawful detention (public or private) |\n'
            '| Mandamus | We command | Direct a public official/body to perform a legal duty |\n'
            '| Prohibition | To forbid | Higher court stops lower court exceeding jurisdiction (preventive) |\n'
            '| Certiorari | To be certified | Quash an order already passed without jurisdiction (curative) |\n'
            '| Quo Warranto | By what authority | Challenge illegal usurpation of a public office |'
        ),
        'trap': 'High Court writ jurisdiction (**Art. 226**) is **wider** than the Supreme Court’s (**Art. 32**), because High Courts can issue writs for both Fundamental Rights AND ordinary legal rights.',
    },
    'emerg': {
        'model': 'Part XVIII (Arts. 352–360) temporarily converts India’s federal structure into a unitary one without amending the Constitution.',
        'table': (
            '### Three Types of Emergency Compared\n\n'
            '| Type | Article | Parliamentary Approval | Max Duration |\n'
            '| --- | --- | --- | --- |\n'
            '| National Emergency | Art. 352 | Special majority within **1 month** | Indefinite (renewed every 6 months) |\n'
            '| President’s Rule (State) | Art. 356 | Simple majority within **2 months** | Max **3 years** (renewed every 6 months) |\n'
            '| Financial Emergency | Art. 360 | Simple majority within **2 months** | Indefinite (never imposed so far) |'
        ),
        'trap': 'The **44th Amendment (1978)** replaced "internal disturbance" with **"armed rebellion"** under Art. 352 and required written Cabinet advice to the President.',
    },
    'cbody': {
        'model': 'Distinguish **Constitutional Bodies** (created by a specific Article — e.g. EC, UPSC, CAG, Finance Commission) from **Statutory/Extra-constitutional Bodies** (created by Act of Parliament or executive resolution — e.g. NHRC, CBI, NITI Aayog).',
        'table': (
            '### High-Frequency Bodies & Articles\n\n'
            '| Body | Basis | Key Role / Note |\n'
            '| --- | --- | --- |\n'
            '| Election Commission | Art. 324 (Constitutional) | Parliament, State Legislatures, President & VP polls |\n'
            '| UPSC / State PSC | Art. 315 (Constitutional) | Civil services recruitment (Art. 309 regulates service conditions) |\n'
            '| Finance Commission | Art. 280 (Constitutional) | Tax devolution between Union & States every 5 years |\n'
            '| CAG of India | Art. 148 (Constitutional) | Guardian of public purse; 6 yrs or age 65 |\n'
            '| CBI | DSPE Act 1946 (Statutory/Executive) | Central Bureau of Investigation — NOT a constitutional body |'
        ),
    },
    'local': {
        'model': '73rd Amendment (1992, Part IX, 11th Schedule, 29 subjects) constitutionalised Panchayati Raj; 74th Amendment (1992, Part IXA, 12th Schedule, 18 subjects) constitutionalised Urban Local Bodies.',
        'hook': 'Both amendments mandate a **5-year term**, a **State Election Commission**, a **State Finance Commission**, and at least **1/3rd reservation for women**. Mizoram’s rural areas are exempt from Part IX (governed instead by Village Councils and ADCs).',
    },
    'sixth': {
        'model': 'The Sixth Schedule (Arts. 244(2) & 275(1)) grants legislative, judicial, and financial autonomy through Autonomous District Councils (ADCs) in **AMTM**: Assam, Meghalaya, Tripura, and Mizoram.',
        'table': (
            '### Mizoram’s Special Constitutional Safeguards\n\n'
            '| Safeguard | Provision | Scope |\n'
            '| --- | --- | --- |\n'
            '| **Art. 371G** | 53rd Amendment (1986) | No Act of Parliament applies to Mizo religion, customary law, civil/criminal justice, or land ownership unless Mizoram Assembly resolves so |\n'
            '| **LADC** | Sixth Schedule (1972) | Lai Autonomous District Council — HQ: Lawngtlai |\n'
            '| **MADC** | Sixth Schedule (1972) | Mara Autonomous District Council — HQ: Siaha |\n'
            '| **CADC** | Sixth Schedule (1972) | Chakma Autonomous District Council — HQ: Kamalanagar (Chawngte) |'
        ),
        'trap': 'Do not mix up the **Fifth Schedule** (Scheduled Areas in 10 mainland states) with the **Sixth Schedule** (Tribal Areas in **Assam, Meghalaya, Tripura, Mizoram** — remember **AMTM**, NOT Manipur or Nagaland!).',
    },
}

MATHS_ENHANCEMENTS: dict[str, dict[str, str]] = {
    'number-system-simplification': {
        'example': 'Simplify `(√5 + √3) / (√5 − √3)`. Multiply top & bottom by `(√5 + √3)` → `(5 + 3 + 2√15) / (5 − 3) = (8 + 2√15) / 2 = **4 + √15**`.',
        'trap': 'In BODMAS, **`of` binds tighter than `÷` and `×`**. So `12 ÷ 3 of 2 = 12 ÷ 6 = 2`, NOT `(12 ÷ 3) × 2 = 8`!',
    },
    'hcf-and-lcm': {
        'example': 'Find the **LCM of 36, 54, and 72** (real MPSC PYQ): prime factorise `36 = 2²×3²`, `54 = 2×3³`, `72 = 2³×3²`. Take the highest power of each prime → `2³ × 3³ = 8 × 27 = **216**`.',
        'trap': 'For **HCF** take the *lowest* common prime power; for **LCM** take the *highest* prime power present in any number.',
    },
    'ratio-proportion-partnership-mixtures': {
        'example': 'If `A : B = 2 : 3` and `B : C = 4 : 5`, equalise `B` to `12` → `A : B : C = **8 : 12 : 15**`.',
        'trap': 'In Partnership problems, profit share is always proportional to **`Capital × Time`** — never forget to convert all durations to the same unit (months)!',
    },
    'percentages-and-sets': {
        'table': (
            '### Must-Know Fraction ↔ Percentage Table\n\n'
            '| Fraction | % | Fraction | % | Fraction | % |\n'
            '| --- | --- | --- | --- | --- | --- |\n'
            '| `1/2` | 50% | `1/6` | 16.67% | `1/10` | 10% |\n'
            '| `1/3` | 33.33% | `1/7` | 14.28% | `1/12` | 8.33% |\n'
            '| `1/4` | 25% | `1/8` | 12.5% | `1/16` | 6.25% |\n'
            '| `1/5` | 20% | `1/9` | 11.11% | `1/20` | 5% |'
        ),
        'example': 'Hostel of **600 boys**: 75% play Hockey, 45% play Football, all play at least one (real MPSC PYQ). Both = `(75% + 45%) − 100% = 20%` of `600` = **120 boys**.',
        'trap': 'Raising a price by 20% and then cutting by 20% does **not** return to 100% — net change is `−(20²/100)% = −4%`!',
    },
    'profit-loss-discount': {
        'example': 'Cost Price = ₹400, Sold at 15% profit → `SP = 400 × 1.15 = **₹460**`. If SP = ₹460 at 15% profit, recover CP by dividing: `460 / 1.15 = ₹400`.',
        'trap': '**Profit % and Loss %** are ALWAYS calculated on **Cost Price (CP)**, whereas **Discount %** is ALWAYS calculated on **Marked Price (MP)**.',
    },
    'simple-and-compound-interest': {
        'example': 'Difference between CI and SI for **2 years at 5% p.a. is ₹5** (real MPSC PYQ). Use shortcut `CI − SI = P × (R/100)²` → `5 = P × (5/100)² = P / 400` → `P = **₹2,000**` in 5 seconds!',
        'trap': 'When interest is compounded **half-yearly**, halve the rate (`R/2`) and double the time (`2T`).',
    },
    'averages-ages-ap': {
        'example': 'Average of 5 numbers is 20 (sum = 100). If one number is removed and the new average of 4 numbers is 18 (sum = 72), the removed number is `100 − 72 = **28**`.',
        'trap': 'The **age difference** between two people NEVER changes over time — anchor age equations on the constant difference.',
    },
    'time-work-pipes': {
        'example': 'A finishes work in 12 days, B in 15 days. Take LCM = 60 units total work → A does `5 u/day`, B does `4 u/day` → Together = `60 / (5 + 4) = **6⅔ days**`.',
        'trap': 'An outlet (emptying) pipe has a **negative** rate — always subtract its hourly units from the inlet pipes.',
    },
    'time-speed-distance-trains': {
        'example': 'A 150 m train at `54 km/h` crosses a pole in: convert `54 × 5/18 = 15 m/s` → `Time = 150 / 15 = **10 seconds**`.',
        'trap': 'To convert `km/h → m/s` multiply by **`5/18`**; `m/s → km/h` multiply by **`18/5`**. Opposite directions **add** speeds; same direction **subtracts**.',
    },
    'algebra-probability-pnc': {
        'example': 'If `x + 1/x = 5`, then `x² + 1/x² = 5² − 2 = **23**` and `x³ + 1/x³ = 5³ − 3(5) = **110**`.',
        'trap': '**Permutations (`nPr`)** care about order (e.g. seating, PINs); **Combinations (`nCr`)** ignore order (e.g. choosing a committee).',
    },
    'mensuration-2d-3d': {
        'table': (
            '### Master Mensuration Formula Table\n\n'
            '| Shape | Area / Surface Area | Perimeter / Volume |\n'
            '| --- | --- | --- |\n'
            '| Circle (radius `r`) | `πr²` | Circumference `2πr` |\n'
            '| Triangle (`b, h`) | `½ × b × h` (Heron: `√[s(s−a)(s−b)(s−c)]`) | `a + b + c` |\n'
            '| Cube (side `a`) | TSA `6a²` · LSA `4a²` | Volume `a³` · Diagonal `a√3` |\n'
            '| Cylinder (`r, h`) | CSA `2πrh` · TSA `2πr(r+h)` | Volume `πr²h` |\n'
            '| Cone (`r, h, l`) | CSA `πrl` (`l = √(r²+h²)`) | Volume `⅓πr²h` |\n'
            '| Sphere (`r`) | Surface Area `4πr²` | Volume `⁴⁄₃πr³` |'
        ),
        'trap': 'When a solid is melted and recast into another shape, **Volume stays constant** (surface area changes!).',
    },
    'geometry-trig-di-stats': {
        'table': (
            '### Standard Trigonometry Values\n\n'
            '| Ratio | 0° | 30° | 45° | 60° | 90° |\n'
            '| --- | --- | --- | --- | --- | --- |\n'
            '| `sin θ` | `0` | `1/2` | `1/√2` | `√3/2` | `1` |\n'
            '| `cos θ` | `1` | `√3/2` | `1/√2` | `1/2` | `0` |\n'
            '| `tan θ` | `0` | `1/√3` | `1` | `√3` | `∞` |'
        ),
        'example': 'Find the **complement of `2/3` of a right angle** (real MPSC PYQ): `2/3 × 90° = 60°` → Complement = `90° − 60° = **30°**`.',
        'trap': '**Complementary angles** sum to **90°**; **Supplementary angles** sum to **180°**.',
    },
}

GEOGRAPHY_ENHANCEMENTS: dict[str, dict[str, str]] = {
    'physiographic-divisions': {
        'table': (
            '### India’s Six Physiographic Divisions\n\n'
            '| Division | Geological Origin | Signature Exam Feature |\n'
            '| --- | --- | --- |\n'
            '| Northern & NE Mountains | Young fold (Indo-Australian × Eurasian) | ~2,400 km; Himadri, Himachal, Shiwalik |\n'
            '| Northern Plains | Quaternary river alluvium | Indus–Ganga–Brahmaputra; Bhabar, Terai, Bhangar, Khadar |\n'
            '| Peninsular Plateau | **Oldest** Gondwana crystalline shield | Deccan Traps, Western & Eastern Ghats |\n'
            '| Indian Desert (Thar) | Arid aeolian sands | Rain shadow of Aravallis; Luni river |\n'
            '| Coastal Plains | Marine & river deposition | Narrow West (Konkan, Malabar) vs Wide East (Coromandel) |\n'
            '| Islands | Coral & volcanic | Lakshadweep (coral) · Andaman & Nicobar (volcanic — Barren Island) |'
        ),
    },
    'rivers': {
        'table': (
            '### Himalayan vs. Peninsular Rivers\n\n'
            '| Feature | Himalayan Rivers | Peninsular Rivers |\n'
            '| --- | --- | --- |\n'
            '| Source | Snow + glaciers + rain (perennial) | Rain-fed (mostly seasonal) |\n'
            '| Examples | Indus, Ganga, Brahmaputra | Godavari, Krishna, Kaveri, Mahanadi, Narmada, Tapi |\n'
            '| Flow direction | Mostly East → Bay of Bengal (Indus → Arabian Sea) | East → Bay of Bengal **except Narmada & Tapi** (West → Arabian Sea, rift valleys) |'
        ),
        'trap': '**Narmada and Tapi** flow *westward* through rift valleys and form **estuaries** (not deltas). **Godavari** is the longest Peninsular river ("Dakshin Ganga").',
    },
    'climate-monsoon': {
        'table': (
            '### India’s Three Cropping Seasons\n\n'
            '| Season | Sown → Harvested | High-Yield Crop Examples |\n'
            '| --- | --- | --- |\n'
            '| **Kharif** (Monsoon) | Jun–Jul → Sep–Oct | Rice (Paddy), Maize, Cotton, Jute, Groundnut, Soyabean |\n'
            '| **Rabi** (Winter) | Oct–Dec → Mar–Apr | Wheat, Barley, Mustard, Gram, Peas |\n'
            '| **Zaid** (Summer) | Mar → Jun | Watermelon, Cucumber, Muskmelon, Fodder crops |'
        ),
        'trap': 'Tamil Nadu (Coromandel Coast) receives its **bulk rainfall in Oct–Dec** from the **Retreating (NE) Monsoon**, not the June SW Monsoon!',
    },
    'soils': {
        'table': (
            '### Major Indian Soils Quick Match\n\n'
            '| Soil Type | Region | Best Known For |\n'
            '| --- | --- | --- |\n'
            '| Alluvial | Northern Plains & deltas (~40% of India) | Most fertile; Khadar (new) > Bhangar (old) |\n'
            '| Black (Regur) | Deccan Trap (Maharashtra, MP, Gujarat) | **Cotton**; self-ploughing, high moisture retention |\n'
            '| Red & Yellow | Eastern & Southern Peninsula | Iron oxide gives red colour; millets & pulses |\n'
            '| Laterite | Heavy rain Ghats, NE Hills, Kerala | Leached; brick-making, **tea, coffee, cashew** |'
        ),
    },
    'forests': {
        'table': (
            '### High-Frequency Biosphere Reserves (Match the Following)\n\n'
            '| Biosphere Reserve | State / Region | Exam Highlight |\n'
            '| --- | --- | --- |\n'
            '| Nilgiri (1986) | TN / Kerala / Karnataka | India’s **first** Biosphere Reserve; Western Ghats hotspot |\n'
            '| Nanda Devi | Uttarakhand | Himalayan alpine flora |\n'
            '| Manas | Assam | UNESCO World Heritage; Golden Langur & Pygmy Hog |\n'
            '| Nokrek | Meghalaya | Garo Hills; Red Panda & citrus gene pool |\n'
            '| Simlipal | Odisha | Tiger reserve & elephants |\n'
            '| Sundarbans | West Bengal | World’s largest mangrove forest; Royal Bengal Tiger |'
        ),
    },
    'mizoram-geography': {
        'table': (
            '### Mizoram’s Three River Families & Key Landmarks\n\n'
            '| Family / Feature | Direction & Basin | Key Rivers / Details |\n'
            '| --- | --- | --- |\n'
            '| North-flowing | → Barak (Assam) | **Tlawng** (longest in Mizoram, ~185 km), Tuirial, Tuivawl, Teirei |\n'
            '| South-flowing | → Kaladan (Myanmar) | **Chhimtuipui** (Kaladan), Mat, Tuichang, Tiau (India–Myanmar border) |\n'
            '| West-flowing | → Karnaphuli (Bangladesh) | **Khawthlangtuipui**, Tuichawng, Kau |\n'
            '| Peaks & Lakes | Highest / Largest | **Phawngpui** (Blue Mountain, 2,157 m, Lawngtlai) · **Palak Dil** (largest natural lake, Siaha) · **Tam Dil** (Saitual) |'
        ),
        'hook': 'Remember Mizoram’s borders: **3 Indian states** (Assam, Manipur, Tripura) and **2 countries** (Myanmar to east/south, Bangladesh to west). The **Tropic of Cancer (23.5°N)** passes right through Mizoram near Thenzawl!',
    },
    'world-restless-earth': {
        'trap': '**Tsunamis** are triggered primarily by **undersea earthquakes** (vertical seafloor displacement at subduction zones) or submarine volcanic eruptions — NOT by surface winds or tides.',
    },
}

HISTORY_ENHANCEMENTS: dict[str, dict[str, str]] = {
    'indus-valley': {
        'table': (
            '### IVC Major Sites · River · Excavator\n\n'
            '| Site | River | Excavator & Year | Signature Find |\n'
            '| --- | --- | --- | --- |\n'
            '| Harappa | Ravi | Dayaram Sahni (1921) | Granaries, first site excavated |\n'
            '| Mohenjodaro | Indus | R.D. Banerji (1922) | Great Bath, Bronze Dancing Girl, Pashupati seal |\n'
            '| Lothal (Gujarat) | Bhogava | S.R. Rao (1954) | World’s earliest tidal **dockyard**, rice husks |\n'
            '| Kalibangan (Rajasthan) | Ghaggar | A. Ghosh / B.B. Lal | Ploughed field, fire altars |\n'
            '| Dholavira (Gujarat) | Luni basin | R.S. Bisht | UNESCO site; 3-part town & water reservoirs |'
        ),
        'hook': 'IVC 4 geographical extremes: **North** Manda (J&K) · **South** Daimabad (Maharashtra) · **West** Sutkagendor (Balochistan) · **East** Alamgirpur (UP).',
    },
    'vedic-age': {
        'table': (
            '### The Four Vedas & Six Vedangas\n\n'
            '| Veda | Focus | Key Fact |\n'
            '| --- | --- | --- |\n'
            '| Rigveda | Hymns (1,028 suktas) | Oldest; contains **Gayatri Mantra** (3rd Mandala) |\n'
            '| Samaveda | Chants & melodies | Origin of Indian classical music |\n'
            '| Yajurveda | Sacrificial rituals | Prose + verse (Shukla & Krishna) |\n'
            '| Atharvaveda | Charms, medicine, daily life | Added last |\n'
            '| **Six Vedangas** | Auxiliary limbs | *Shiksha, Kalpa, Vyakarana, Nirukta, Chhanda, Jyotisha* |'
        ),
    },
    'buddhism-jainism': {
        'table': (
            '### The Four Buddhist Councils\n\n'
            '| Council | Place | Patron King | President / Outcome |\n'
            '| --- | --- | --- | --- |\n'
            '| 1st (483 BC) | Rajagriha | Ajatashatru | Mahakassapa; Vinaya & Sutta Pitaka compiled |\n'
            '| 2nd (383 BC) | Vaishali | Kalasoka | Sabakami; split into Sthaviravadins & Mahasanghikas |\n'
            '| 3rd (250 BC) | Pataliputra | **Ashoka** | Moggaliputta Tissa; Abhidhamma Pitaka |\n'
            '| 4th (72 AD) | Kashmir (Kundalvana) | **Kanishka** | Vasumitra; **Hinayana & Mahayana** split |'
        ),
    },
    'delhi-sultanate': {
        'table': (
            '### Five Dynasties of Delhi Sultanate (1206–1526)\n\n'
            '| Dynasty | Period | Founder | Key Exam Anchor |\n'
            '| --- | --- | --- | --- |\n'
            '| Slave (Mamluk) | 1206–1290 | Qutb-ud-din Aibak | Qutb Minar; Iltutmish (Iqta); Razia Sultan; Balban |\n'
            '| Khilji | 1290–1320 | Jalal-ud-din Khilji | Alauddin Khilji — market price control & dagh/chehra |\n'
            '| Tughlaq | 1320–1414 | Ghiyas-ud-din Tughlaq | Muhammad bin Tughlaq (Daulatabad, token currency) |\n'
            '| Sayyid | 1414–1451 | Khizr Khan | Post-Timur invasion |\n'
            '| Lodi | 1451–1526 | Bahlul Lodi | First Afghan dynasty; Ibrahim Lodi defeated at **Panipat (1526)** |'
        ),
        'hook': 'Mnemonic for the 5 dynasties in order: **S–K–T–S–L** (*Slave, Khilji, Tughlaq, Sayyid, Lodi*).',
    },
    'freedom-struggle-map': {
        'table': (
            '### Revolt of 1857 — Centres & Leaders\n\n'
            '| Centre | Indian Leader(s) | British Suppressor |\n'
            '| --- | --- | --- |\n'
            '| Delhi | Bahadur Shah II & Bakht Khan | John Nicholson |\n'
            '| **Kanpur** | **Nana Saheb** & Tantia Tope | Sir Colin Campbell |\n'
            '| Lucknow | Begum Hazrat Mahal | Sir Colin Campbell |\n'
            '| Jhansi | Rani Lakshmibai | Sir Hugh Rose |\n'
            '| Bihar (Jagdishpur) | Kunwar Singh | William Taylor |'
        ),
        'trap': '**Swadeshi & Boycott** were first adopted as mass-struggle methods during the **1905 Partition of Bengal** (Lord Curzon) — NOT the Non-Cooperation Movement (1920). **Calcutta** remained British India’s capital until **1911**.',
    },
    'modern-india-mizoram-world-milestones': {
        'table': (
            '### Mizoram History Chronology (1871–1987)\n\n'
            '| Year | Milestone |\n'
            '| --- | --- |\n'
            '| 1871–72 & 1889–90 | First & Second Lushai Expeditions; British administration begins |\n'
            '| 11 Jan 1894 | J.H. Lorrain (*Pu Buanga*) & F.W. Savidge (*Sap Upa*) arrive; Mizo alphabet created |\n'
            '| 1946 / 1952 | Mizo Union founded (1946); Lushai Hills Autonomous District Council (1952) |\n'
            '| 1954 / 1959 | Abolition of Chieftainship (1954); Mautam bamboo-flowering famine (1959) |\n'
            '| 1972 | Mizoram becomes a Union Territory (LADC, MADC, CADC created) |\n'
            '| 30 Jun 1986 | **Mizoram Peace Accord** signed (GoI + MNF) |\n'
            '| 20 Feb 1987 | **23rd State of India** inaugurated with Art. 371G protection |'
        ),
    },
}


def decode_js_string(raw: str) -> str:
    out: list[str] = []
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == '\\' and i + 1 < n:
            nxt = raw[i + 1]
            if nxt == 'u' and i + 5 < n:
                try:
                    out.append(chr(int(raw[i + 2 : i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
            if nxt == 'n':
                out.append('\n')
                i += 2
                continue
            if nxt == 't':
                out.append(' ')
                i += 2
                continue
            if nxt in ("'", '"', '\\'):
                out.append(nxt)
                i += 2
                continue
        out.append(ch)
        i += 1
    return ''.join(out)


def extract_ts_field(text: str, field: str) -> str:
    pattern = re.compile(
        rf'\b{re.escape(field)}\s*:\s*\n?\s*([\'"])((?:\\.|(?!\1).)*)\1',
        re.DOTALL,
    )
    m = pattern.search(text)
    return decode_js_string(m.group(2)).strip() if m else ''


def extract_atlas_chapter(slug: str) -> dict:
    path = ATLAS_CHAPTERS / f'{slug}.ts'
    text = path.read_text(encoding='utf-8')
    export_idx = text.find('export const')
    body = text[export_idx:] if export_idx != -1 else text
    title = extract_ts_field(body, 'title') or slug
    summary = extract_ts_field(body, 'summary')
    focus = extract_ts_field(body, 'focus')
    facts_idx = body.find('facts:')
    facts: list[str] = []
    if facts_idx != -1:
        for m in re.finditer(r'\btext\s*:\s*([\'"])((?:\\.|(?!\1).)*)\1', body[facts_idx:], re.DOTALL):
            val = decode_js_string(m.group(2)).strip()
            if val:
                facts.append(val)
    return {'slug': slug, 'title': title, 'summary': summary, 'focus': focus, 'facts': facts}


def build_maths_guide() -> dict:
    items = json.loads(ARITHMETIC_JSON.read_text(encoding='utf-8'))
    by_id = {x['id']: x for x in items}

    groups = [
        (
            'number-system-simplification',
            '1. Number System, Surds, Roots & Simplification (BODMAS)',
            ['num', 'simp'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic#exam-question-browser',
            'Practise Arithmetic MCQs →',
        ),
        (
            'hcf-and-lcm',
            '2. HCF, LCM & Divisibility Rules',
            ['hcflcm'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic&q=LCM#exam-question-browser',
            'Practise HCF & LCM MCQs →',
        ),
        (
            'ratio-proportion-partnership-mixtures',
            '3. Ratio, Proportion, Partnership & Mixtures',
            ['ratio', 'part', 'mix'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic&subtopic_id=mathematics%2Farithmetic%2Fratio-and-proportion#exam-question-browser',
            'Practise Ratio & Proportion MCQs (113 Qs) →',
        ),
        (
            'percentages-and-sets',
            '4. Percentages & Set Theory (Venn Surveys)',
            ['pct', 'sets'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic&subtopic_id=mathematics%2Farithmetic%2Fpercentages#exam-question-browser',
            'Practise Percentages MCQs (110 Qs) →',
        ),
        (
            'profit-loss-discount',
            '5. Profit, Loss & Discount',
            ['pl'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic&subtopic_id=mathematics%2Farithmetic%2Fprofit-and-loss#exam-question-browser',
            'Practise Profit & Loss MCQs (57 Qs) →',
        ),
        (
            'simple-and-compound-interest',
            '6. Simple & Compound Interest (CI − SI Shortcuts)',
            ['si', 'ci'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic&q=interest#exam-question-browser',
            'Practise Interest MCQs →',
        ),
        (
            'averages-ages-ap',
            '7. Averages, Ages & Arithmetic Progression',
            ['avg', 'ages', 'ap'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic&subtopic_id=mathematics%2Farithmetic%2Faverages#exam-question-browser',
            'Practise Averages MCQs (47 Qs) →',
        ),
        (
            'time-work-pipes',
            '8. Time & Work, Pipes & Cisterns',
            ['tw', 'pipes'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic&q=work#exam-question-browser',
            'Practise Time & Work MCQs →',
        ),
        (
            'time-speed-distance-trains',
            '9. Time, Speed, Distance & Trains',
            ['tsd'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Farithmetic&q=speed#exam-question-browser',
            'Practise Speed & Distance MCQs →',
        ),
        (
            'algebra-probability-pnc',
            '10. Algebra, Equations, Indices, Probability & P&C',
            ['alg', 'prob', 'pnc'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Falgebra#exam-question-browser',
            'Practise Algebra MCQs (173 Qs) →',
        ),
        (
            'mensuration-2d-3d',
            '11. Mensuration — 2D Area & 3D Volume',
            ['mens2', 'mens3'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Fmensuration#exam-question-browser',
            'Practise Mensuration MCQs (122 Qs) →',
        ),
        (
            'geometry-trig-di-stats',
            '12. Geometry, Trigonometry, Coordinate Geometry & Statistics',
            ['trig', 'coord', 'stat', 'di'],
            '/subjects/mathematics?view=browse&subject_id=mathematics&topic_id=mathematics%2Fgeometry#exam-question-browser',
            'Practise Geometry MCQs (62 Qs) →',
        ),
    ]

    chapters = []
    for ord_idx, (anchor, heading, ids, pq, plabel) in enumerate(groups, start=1):
        parts: list[str] = []
        for item_id in ids:
            entry = by_id.get(item_id)
            if not entry:
                continue
            if len(ids) > 1:
                parts.append(f"### {entry['name']}")
            if entry.get('analogy'):
                parts.append(f"**Intuition:** {entry['analogy'].strip()}")
            if entry.get('explain'):
                parts.append(entry['explain'].strip())
            formulas = entry.get('formulas') or []
            if formulas:
                lines = '\n'.join(f"- `{f.strip()}`" for f in formulas if f.strip())
                parts.append(f"**Key Formulas & Shortcuts**\n\n{lines}")
        enh = MATHS_ENHANCEMENTS.get(anchor, {})
        if enh.get('table'):
            parts.append(enh['table'])
        if enh.get('example'):
            parts.append(f"**Worked Example:** {enh['example']}")
        if enh.get('trap'):
            parts.append(f"**Exam Trap:** {enh['trap']}")
        chapters.append(
            {
                'ord': ord_idx,
                'anchor': anchor,
                'heading': heading,
                'body_markdown': '\n\n'.join(parts),
                'practice_query': pq,
                'practice_label': plabel,
                'companion_href': '/arithmetic',
                'companion_label': 'Open interactive Formula Lab →',
            }
        )

    return {
        'slug': 'maths-and-arithmetic',
        'title': 'Mathematics & Arithmetic Formula Handbook',
        'subject_id': 'mathematics',
        'subject_label': 'Mathematics',
        'topic_id': 'mathematics/arithmetic',
        'exam_scope': ['udc', 'ldc', 'assistant', 'combined-prelims', 'subject-mathematics'],
        'summary': 'All 26 high-yield Arithmetic, Algebra, Mensuration, Geometry & Statistics concepts distilled into intuitions, formula cards, worked MPSC examples, and exam traps — wired to 2,807 live Mathematics PYQs.',
        'reading_minutes': 22,
        'status': 'published',
        'chapters': chapters,
    }


def build_geography_guide() -> dict:
    specs = [
        ('physiographic-divisions', 'gk-gs:geography', 'Practise Geography MCQs (1,050 Qs) →'),
        ('mountains', 'gk-gs:geography', 'Practise Geography MCQs (1,050 Qs) →'),
        ('rivers', 'gk-gs:geography', 'Practise Geography MCQs (1,050 Qs) →'),
        ('climate-monsoon', 'gk-gs:geography', 'Practise Geography MCQs (1,050 Qs) →'),
        ('soils', 'gk-gs:geography', 'Practise Geography MCQs (1,050 Qs) →'),
        ('forests', 'gk-gs:environment', 'Practise Environment & Biodiversity MCQs (345 Qs) →'),
        ('mizoram-geography', 'gk-gs:mizoram', 'Practise Mizoram Geography & GK MCQs (515 Qs) →'),
        ('world-restless-earth', 'gk-gs:geography', 'Practise Physical Geography MCQs →'),
        ('world-atmosphere-heat', 'gk-gs:geography', 'Practise Physical Geography MCQs →'),
        ('world-winds-currents', 'gk-gs:geography', 'Practise Physical Geography MCQs →'),
        ('world-resources-industries', 'gk-gs:geography', 'Practise World Geography MCQs →'),
    ]
    chapters = []
    for ord_idx, (slug, topic_id, plabel) in enumerate(specs, start=1):
        ch = extract_atlas_chapter(slug)
        enh = GEOGRAPHY_ENHANCEMENTS.get(slug, {})
        parts: list[str] = []
        if ch['summary']:
            parts.append(f"**Overview:** {ch['summary']}")
        if ch['focus']:
            parts.append(f"**Core Mental Model:** {ch['focus']}")
        if enh.get('table'):
            parts.append(enh['table'])
        if enh.get('hook'):
            parts.append(f"**Memory Hook:** {enh['hook']}")
        if enh.get('trap'):
            parts.append(f"**Exam Trap:** {enh['trap']}")
        if ch['facts']:
            bullets = '\n'.join(f"- {f}" for f in ch['facts'])
            parts.append(f"### High-Yield Exam Facts\n\n{bullets}")
        encoded_topic = topic_id.replace(':', '%3A')
        chapters.append(
            {
                'ord': ord_idx,
                'anchor': slug,
                'heading': f"{ord_idx}. {ch['title']}",
                'body_markdown': '\n\n'.join(parts),
                'practice_query': f"/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id={encoded_topic}#exam-question-browser",
                'practice_label': plabel,
                'companion_href': f"/atlas/{slug}",
                'companion_label': 'Open interactive map in Atlas →',
            }
        )
    return {
        'slug': 'geography-essentials',
        'title': 'Geography of India, World & Mizoram',
        'subject_id': 'gk-gs',
        'subject_label': 'Geography',
        'topic_id': 'gk-gs:geography',
        'exam_scope': ['udc', 'ldc', 'combined-prelims', 'subject-gk-gs'],
        'summary': '11 visual Geography & Environment chapters with comparison tables, Mizoram’s three river families, biosphere reserves, and 131 verified exam facts — linked directly to Atlas maps and 1,910 live PYQs.',
        'reading_minutes': 24,
        'status': 'published',
        'chapters': chapters,
    }


def build_history_guide() -> dict:
    specs = [
        ('indus-valley', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('vedic-age', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('buddhism-jainism', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('mahajanapadas-mauryas', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('medieval-gateway-battles', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('delhi-sultanate', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('medieval-south', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('european-conquest', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('battle-of-plassey', 'gk-gs:indian-history', 'Practise Indian History MCQs (820 Qs) →'),
        ('freedom-struggle-map', 'gk-gs:indian-history', 'Practise Freedom Struggle MCQs (820 Qs) →'),
    ]
    chapters = []
    for ord_idx, (slug, topic_id, plabel) in enumerate(specs, start=1):
        ch = extract_atlas_chapter(slug)
        enh = HISTORY_ENHANCEMENTS.get(slug, {})
        parts: list[str] = []
        if ch['summary']:
            parts.append(f"**Overview:** {ch['summary']}")
        if ch['focus']:
            parts.append(f"**Core Mental Model:** {ch['focus']}")
        if enh.get('table'):
            parts.append(enh['table'])
        if enh.get('hook'):
            parts.append(f"**Memory Hook:** {enh['hook']}")
        if enh.get('trap'):
            parts.append(f"**Exam Trap:** {enh['trap']}")
        if ch['facts']:
            bullets = '\n'.join(f"- {f}" for f in ch['facts'])
            parts.append(f"### High-Yield Exam Facts\n\n{bullets}")
        encoded_topic = topic_id.replace(':', '%3A')
        chapters.append(
            {
                'ord': ord_idx,
                'anchor': slug,
                'heading': f"{ord_idx}. {ch['title']}",
                'body_markdown': '\n\n'.join(parts),
                'practice_query': f"/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id={encoded_topic}#exam-question-browser",
                'practice_label': plabel,
                'companion_href': f"/atlas/{slug}",
                'companion_label': 'Explore historical map in Atlas →',
            }
        )

    m_enh = HISTORY_ENHANCEMENTS['modern-india-mizoram-world-milestones']
    chapters.append(
        {
            'ord': 11,
            'anchor': 'modern-india-mizoram-world-milestones',
            'heading': '11. Modern India Milestones, Mizoram History & World History',
            'body_markdown': '\n\n'.join([
                '**Overview:** High-frequency MPSC Prelims & Clerical anchors covering Mughal culture, 1857, INC, the Gandhian Era, Mizoram’s political journey, and World History turning points.',
                '**Core Mental Model:** Link every modern Indian event to its decade anchor — 1857 (Revolt), 1885 (INC), 1905 (Swadeshi), 1911 (Delhi capital), 1920/1930/1942 (Gandhi’s three mass movements) — and pair Mizoram’s journey from 1894 (Alphabet) to 1986 (Peace Accord) & 1987 (Statehood).',
                m_enh['table'],
                '### High-Frequency Indian History Anchors\n\n'
                '- **Vedic & Classical:** Six Vedangas are *Shiksha, Kalpa, Vyakarana, Nirukta, Chhanda, Jyotisha*. Akbar introduced **Din-i-Ilahi** (1582) as a syncretic ethical order.\n'
                '- **Indian National Congress (1885):** Founded by A.O. Hume in Bombay; first President was **W.C. Bonnerjee** (72 delegates).\n'
                '- **Partition of Bengal (1905):** Lord Curzon partitioned Bengal; **Swadeshi & Boycott** were adopted as mass struggle methods for the first time during this agitation.\n'
                '- **Capital Shift (1911):** Calcutta remained the capital of British India until **1911**, when the Delhi Durbar announced the shift to New Delhi.\n'
                '- **Gandhian Mass Movements:** Champaran (1917) → Kheda & Ahmedabad (1918) → Non-Cooperation (1920–22) → Civil Disobedience / Dandi March (1930) → Quit India (August 1942).',
                '### World History Quick Landmarks\n\n'
                '- **1776:** American Declaration of Independence · **1789:** French Revolution (*Liberty, Equality, Fraternity*) · **1914–1918:** World War I (Treaty of Versailles, 1919) · **1917:** Russian Revolution · **1939–1945:** World War II → **United Nations founded (24 October 1945)**.',
            ]),
            'practice_query': '/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id=gk-gs%3Aworld-history#exam-question-browser',
            'practice_label': 'Practise World History MCQs (142 Qs) →',
            'companion_href': '/chronicle',
            'companion_label': 'Open interactive History Chronicle →',
        }
    )

    return {
        'slug': 'history-essentials',
        'title': 'Indian, World & Mizoram History',
        'subject_id': 'gk-gs',
        'subject_label': 'History',
        'topic_id': 'gk-gs:indian-history',
        'exam_scope': ['udc', 'ldc', 'combined-prelims', 'subject-gk-gs'],
        'summary': '11 chronological History chapters with site/dynasty/revolt tables, Mizoram’s statehood timeline (1871–1987), and exam traps — linked directly to Atlas maps, Chronicle, and 962+ History PYQs.',
        'reading_minutes': 25,
        'status': 'published',
        'chapters': chapters,
    }


def build_computer_guide() -> dict:
    chapters = [
        {
            'ord': 1,
            'anchor': 'hardware-memory-architecture',
            'heading': '1. Hardware, CPU, Memory Hierarchy & Binary Units',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** A computer processes data in four stages (Input → Processing → Output → Storage). Speed increases and capacity shrinks as you move closer to the CPU: **Registers > L1/L2/L3 Cache > RAM > SSD/HDD**.',
                '### Memory Types Comparison\n\n'
                '| Memory | Volatility | Speed | Primary Role |\n'
                '| --- | --- | --- | --- |\n'
                '| CPU Registers | Volatile | Fastest | Holds immediate ALU operands & instruction pointer |\n'
                '| Cache (SRAM) | Volatile | Very fast | Bridges CPU–RAM speed gap (flip-flops, no refresh needed) |\n'
                '| RAM (DRAM) | Volatile | Fast | Holds active OS & running apps; loses data on power-off |\n'
                '| ROM / BIOS / UEFI | Non-volatile | Moderate | Stores boot firmware (POST — Power-On Self-Test) |\n'
                '| SSD / HDD / Optical | Non-volatile | Slower | Permanent mass storage (flash vs magnetic platters) |',
                '### Binary & Storage Units\n\n'
                '| Unit | Exact Value | Quick Rule |\n'
                '| --- | --- | --- |\n'
                '| 1 Nibble | 4 bits | 1 hexadecimal digit |\n'
                '| 1 Byte | 8 bits | 1 ASCII character (256 values) |\n'
                '| 1 KB | 1,024 Bytes (2¹⁰) | Kilobyte |\n'
                '| 1 MB | 1,024 KB (2²⁰ B) | Megabyte |\n'
                '| 1 GB | 1,024 MB (2³⁰ B) | Gigabyte |\n'
                '| 1 TB | 1,024 GB (2⁴⁰ B) | Terabyte |',
                '- **CPU components:** ALU (Arithmetic Logic Unit), CU (Control Unit — fetches/decodes), and Registers.\n'
                '- **Computer Generations:** 1st Vacuum Tubes → 2nd Transistors → 3rd Integrated Circuits (IC) → 4th Microprocessors (VLSI) → 5th AI / ULSI.\n'
                '- **Input vs Output:** OCR, OMR, MICR (cheques), Barcode Reader, Joystick = Input; Plotter, Laser Printer, Monitor, Speaker = Output.',
                '**Exam Trap:** **RAM is volatile** (clears when power turns off) — that is why it cannot be used for permanent storage. **SRAM** is faster and costlier than **DRAM** and is used in Cache, whereas DRAM is used in main RAM.',
            ]),
            'practice_query': '/subjects/computer-science?view=browse#exam-question-browser',
            'practice_label': 'Practise Computer Hardware & Architecture MCQs →',
        },
        {
            'ord': 2,
            'anchor': 'os-windows-shortcuts',
            'heading': '2. Operating Systems, File Systems & Windows Shortcuts',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** The Operating System (OS) is the resource manager sitting between hardware and user applications — handling **process scheduling, memory management (paging/virtual memory), file systems, and device drivers**.',
                '### High-Frequency Windows Shortcuts\n\n'
                '| Shortcut | Action |\n'
                '| --- | --- |\n'
                '| `Alt + Tab` | Switch between open applications |\n'
                '| `Win + D` | Show / hide Desktop (minimise all windows) |\n'
                '| `Win + L` | Lock the computer |\n'
                '| `Ctrl + Shift + Esc` | Open Task Manager directly |\n'
                '| `Alt + F4` | Close active window / Shut down on Desktop |\n'
                '| `Shift + Delete` | Permanently delete file (bypasses Recycle Bin) |\n'
                '| `F2` | Rename selected file or folder |\n'
                '| `Win + E` | Open File Explorer |',
                '- **Booting:** Cold boot (power from off) vs Warm boot (restart via `Ctrl+Alt+Del` or Restart).\n'
                '- **OS Types:** Batch, Time-sharing, Real-Time (RTOS — missiles/medical), Distributed, Embedded.\n'
                '- **Deadlock Conditions (Coffman):** Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait.\n'
                '- **File Extensions:** `.exe` (executable), `.pdf` (Portable Document Format), `.csv` (comma-separated values), `.zip` (compressed archive).',
                '**Exam Trap:** `Ctrl + Shift + Esc` opens **Task Manager** directly, whereas `Ctrl + Alt + Del` opens the Windows Security screen first. **Thrashing** occurs when a system spends more time swapping pages (virtual memory) than executing instructions.',
            ]),
            'practice_query': '/subjects/computer-science?view=browse#exam-question-browser',
            'practice_label': 'Practise OS & Windows Shortcuts MCQs →',
        },
        {
            'ord': 3,
            'anchor': 'ms-office-word-excel-ppt',
            'heading': '3. MS Office — Word, Excel Formulas & PowerPoint',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** MPSC & MSSSB Computer papers test practical office fluency — knowing **which tool solves a formatting/data task** and exact keyboard shortcuts.',
                '### MS Word, Excel & PowerPoint Essentials\n\n'
                '| Application | Feature / Shortcut | What It Does |\n'
                '| --- | --- | --- |\n'
                '| MS Word | **Format Painter** (`Ctrl+Shift+C` / `V`) | Copies exact text/paragraph formatting to another selection |\n'
                '| MS Word | **Mail Merge** | Combines a template letter with a recipient data source (Excel/CSV) |\n'
                '| MS Word | `Ctrl + H` / `Ctrl + K` / `F7` | Find & Replace / Insert Hyperlink / Spelling & Grammar check |\n'
                '| MS Word | `Ctrl + J` / `Ctrl + E` | Justify align / Center align |\n'
                '| MS Excel | `$A$1` (Absolute Reference) | Locks both column and row when copying formulas (`F4` toggles) |\n'
                '| MS Excel | `=SUM()`, `=AVERAGE()`, `=COUNT()`, `=IF()` | Core aggregation & conditional formulas (always begin with `=`) |\n'
                '| MS PowerPoint | `F5` / `Shift + F5` | Start slideshow from slide 1 / from current slide |\n'
                '| MS PowerPoint | `Ctrl + M` vs `Ctrl + N` | Insert **new slide** vs open **new presentation** |',
                '**Exam Trap:** In PowerPoint, `Ctrl + M` inserts a **new slide** inside the current deck, while `Ctrl + N` creates an entirely new presentation. In Word, **Gutter margin** adds extra space on the binding side for printing/bookbinding. Default modern extensions: `.docx`, `.xlsx`, `.pptx`.',
            ]),
            'practice_query': '/subjects/computer-science?view=browse#exam-question-browser',
            'practice_label': 'Practise MS Office MCQs →',
        },
        {
            'ord': 4,
            'anchor': 'networking-internet-cyber',
            'heading': '4. Computer Networks, OSI/TCP-IP, Internet & Cybersecurity',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Data travels down the sender’s **7-layer OSI stack** (encapsulation) and up the receiver’s stack. Knowing **which device & protocol sits at which layer** solves most networking questions.',
                '### OSI 7 Layers, Devices & Protocols\n\n'
                '| Layer | Name | Key Device / Protocol |\n'
                '| --- | --- | --- |\n'
                '| 7 | Application | HTTP (80), HTTPS (443), FTP (21), SMTP (25), DNS (53), POP3/IMAP |\n'
                '| 6 | Presentation | SSL/TLS encryption, compression (JPEG, ASCII) |\n'
                '| 5 | Session | Session setup, checkpointing, NetBIOS |\n'
                '| 4 | Transport | **TCP** (reliable, connection-oriented) & **UDP** (fast, connectionless) |\n'
                '| 3 | Network | **Router**, IP (IPv4 = 32-bit, IPv6 = 128-bit), ICMP (`ping`) |\n'
                '| 2 | Data Link | **Switch**, Bridge, MAC address (48-bit), Ethernet Frames |\n'
                '| 1 | Physical | **Hub**, Repeater, Cables (Twisted Pair, Fiber Optic), Bits |',
                '**Memory Hook:** OSI Layers bottom-to-top (1→7): **P**lease **D**o **N**ot **T**hrow **S**ausage **P**izza **A**way (Physical, Data Link, Network, Transport, Session, Presentation, Application).',
                '- **Topologies:** Star (central switch — most common LAN), Bus (single backbone), Ring, Mesh (highest fault tolerance).\n'
                '- **Cybersecurity:** **Phishing** (fake emails/sites stealing credentials), **Ransomware** (encrypts files for ransom), **Trojan** (disguised legitimate software), **Firewall** (filters network traffic), **HTTPS** (HTTP over TLS/SSL).',
                '**Exam Trap:** **SMTP** *sends* email (outgoing); **POP3 / IMAP** *receives* email (incoming). **DNS** translates domain names (`study.hawayu.in`) into IP addresses. **Switch** works at Layer 2 (MAC), **Router** at Layer 3 (IP), and **Hub** at Layer 1 (broadcasts to all ports).',
            ]),
            'practice_query': '/subjects/computer-science?view=browse#exam-question-browser',
            'practice_label': 'Practise Networking & Internet MCQs →',
        },
        {
            'ord': 5,
            'anchor': 'databases-sql-basics',
            'heading': '5. Databases, Keys, Normalization & SQL Basics',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** A Relational DBMS (RDBMS) stores data in tables (**relations**) of rows (**tuples**) and columns (**attributes**), linked via keys and protected by **ACID** transactions.',
                '### Database Keys & SQL Command Groups\n\n'
                '| Concept | Meaning & Exam Example |\n'
                '| --- | --- |\n'
                '| Primary Key | Uniquely identifies every row; **cannot be NULL** or duplicate |\n'
                '| Foreign Key | Column referencing the Primary Key of another table (referential integrity) |\n'
                '| Candidate / Super Key | Minimal unique identifier / any superset of a candidate key |\n'
                '| DDL (Structure) | `CREATE`, `ALTER`, `DROP`, `TRUNCATE` |\n'
                '| DML (Data) | `SELECT`, `INSERT`, `UPDATE`, `DELETE` |\n'
                '| DCL / TCL | `GRANT`, `REVOKE` / `COMMIT`, `ROLLBACK`, `SAVEPOINT` |',
                '- **ACID Properties:** **A**tomicity (all-or-nothing), **C**onsistency, **I**solation, **D**urability.\n'
                '- **Normalization:** 1NF (atomic values, no repeating groups) → 2NF (no partial dependency) → 3NF (no transitive dependency) → BCNF.',
                '**Exam Trap:** `DELETE` removes specific rows (can use `WHERE` and be rolled back); `TRUNCATE` removes all rows fast and resets identity; `DROP` deletes the entire table structure itself.',
            ]),
            'practice_query': '/subjects/computer-science?view=browse#exam-question-browser',
            'practice_label': 'Practise DBMS & SQL MCQs →',
        },
    ]
    return {
        'slug': 'computer-fundamentals',
        'title': 'Computer & IT Fundamentals',
        'subject_id': 'computer-science',
        'subject_label': 'Computer & IT',
        'topic_id': 'computer-science/computer-systems-and-architecture',
        'exam_scope': ['udc', 'ldc', 'combined-prelims', 'subject-computer-science'],
        'summary': '5 exam-ready chapters covering Hardware/Memory, Windows Shortcuts & OS, MS Word/Excel/PowerPoint, OSI Networking & Cybersecurity, and DBMS/SQL — tuned for 7,450+ Computer & IT PYQs.',
        'reading_minutes': 16,
        'status': 'published',
        'chapters': chapters,
    }


def build_science_guide() -> dict:
    chapters = [
        {
            'ord': 1,
            'anchor': 'physics-units-optics-electricity',
            'heading': '1. Physics — SI Units, Mechanics, Optics, Heat & Electricity',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Competitive Physics questions test **everyday applications of laws** (why the sky is blue, which mirror goes in headlights vs rear-view, Ohm’s law, SI units, and wave properties).',
                '### High-Yield SI Units & Instruments\n\n'
                '| Quantity | SI Unit | Measuring Instrument |\n'
                '| --- | --- | --- |\n'
                '| Force / Weight | Newton (N) | Spring balance |\n'
                '| Pressure | Pascal (Pa = N/m²) | Barometer (air), Manometer (gas) |\n'
                '| Work / Energy / Heat | Joule (J) | Calorimeter (heat) |\n'
                '| Power | Watt (W = J/s) | 1 Horsepower (HP) = **746 W** |\n'
                '| Electric Current / Resistance | Ampere (A) / Ohm (Ω) | Ammeter (series) / Voltmeter (parallel) |\n'
                '| Frequency / Sound Loudness | Hertz (Hz) / Decibel (dB) | Audiometer / Sonar (ultrasound) |\n'
                '| Optical Power of Lens | Dioptre (`P = 1/f` in m) | Convex (+), Concave (−) |',
                '### Mirrors, Lenses & Eye Defects\n\n'
                '| Application / Defect | Mirror or Lens Used | Key Reason |\n'
                '| --- | --- | --- |\n'
                '| Vehicle rear-view mirror | **Convex mirror** | Always erect, diminished, wider field of view |\n'
                '| Headlights, shaving & dentist mirror | **Concave mirror** | Parallel beam / magnified erect image up close |\n'
                '| Myopia (near-sightedness) | **Concave lens** | Image forms in front of retina; diverges rays |\n'
                '| Hypermetropia (far-sightedness) | **Convex lens** | Image forms behind retina; converges rays |\n'
                '| Astigmatism | **Cylindrical lens** | Uneven corneal curvature |',
                '- **Light Phenomena:** Sky blue & sunset red = **Rayleigh Scattering**; Mirage, Optical Fibre & Diamond sparkle = **Total Internal Reflection (TIR)**; Rainbow = Dispersion + Refraction + Internal Reflection.\n'
                '- **Thermodynamics:** Specific heat of a gas in an **isothermal** process (ΔT = 0) is **infinity (∞)**; in an **adiabatic** process (ΔQ = 0) it is **zero**.\n'
                '- **Electricity:** Fuse wire = low melting point, high resistance (lead-tin alloy, placed in **series** on live wire). Household wiring is always in **parallel**.',
                '**Exam Trap:** **Light-year** and **Parsec** are units of **distance** (not time!). Sound waves are **longitudinal mechanical waves** (cannot travel in vacuum; fastest in **solids**, slowest in gases), while light is a **transverse electromagnetic wave** (fastest in vacuum).',
            ]),
            'practice_query': '/subjects/science?view=browse#exam-question-browser',
            'practice_label': 'Practise Physics MCQs (539 Qs) →',
        },
        {
            'ord': 2,
            'anchor': 'chemistry-periodic-acids-everyday',
            'heading': '2. Chemistry — Atomic Structure, Periodic Table, Acids/Bases & Everyday Chemistry',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** General Chemistry MCQs focus on **common chemical names, pH & acids, alloys, allotropes of carbon, gases, and periodic trends**.',
                '### Must-Know Common Chemicals & Formulas\n\n'
                '| Common Name | Chemical Name | Formula | Everyday Use |\n'
                '| --- | --- | --- | --- |\n'
                '| Baking Soda | Sodium bicarbonate | `NaHCO₃` | Antacid, baking, fire extinguisher |\n'
                '| Washing Soda | Sodium carbonate decahydrate | `Na₂CO₃·10H₂O` | Softening hard water, detergent |\n'
                '| Bleaching Powder | Calcium oxychloride | `CaOCl₂` | Water disinfection, bleaching |\n'
                '| Plaster of Paris | Calcium sulphate hemihydrate | `CaSO₄·½H₂O` | Casts, moulds (from Gypsum `2H₂O`) |\n'
                '| Laughing Gas | Nitrous oxide | `N₂O` | Mild anaesthetic |\n'
                '| Dry Ice | Solid carbon dioxide | `CO₂(s)` | Sublimation cooling |\n'
                '| Quick Lime / Slaked Lime | Calcium oxide / hydroxide | `CaO` / `Ca(OH)₂` | Cement / whitewashing |',
                '### Key Alloys & Everyday Acids\n\n'
                '| Alloy / Source | Composition / Acid |\n'
                '| --- | --- |\n'
                '| Brass / Bronze | Copper + Zinc (**Brass**) / Copper + Tin (**Bronze**) |\n'
                '| Solder / Stainless Steel | Lead + Tin / Iron + Chromium + Nickel + Carbon |\n'
                '| Vinegar / Lemon / Tamarind / Ant sting | Acetic / Citric / Tartaric / **Formic (Methanoic)** acid |\n'
                '| Curd / Stomach gastric juice / Car battery | Lactic / **Hydrochloric (HCl)** / **Sulphuric (H₂SO₄)** acid |',
                '- **Allotropes of Carbon:** **Graphite** (used in pencils & lubricants; good conductor of electricity), **Diamond** (hardest natural substance; electrical insulator), Fullerene (C₆₀).\n'
                '- **pH Scale (0–14):** `< 7` Acidic, `= 7` Neutral (pure water), `> 7` Basic. Human blood pH = **7.35–7.45** (slightly alkaline).\n'
                '- **Isotopes vs Isobars:** Isotopes = same atomic number (protons), different mass number (e.g., ¹²C, ¹⁴C); Isobars = same mass number, different atomic number.',
                '**Exam Trap:** **Aqua Regia** (dissolves gold & platinum) is a **3 : 1** mixture of concentrated **HCl** and concentrated **HNO₃**. **Graphite** (not lead!) is used in pencil leads. **Mercury** is the only liquid metal; **Bromine** is the only liquid non-metal at room temperature.',
            ]),
            'practice_query': '/subjects/science?view=browse#exam-question-browser',
            'practice_label': 'Practise Chemistry MCQs (295 Qs) →',
        },
        {
            'ord': 3,
            'anchor': 'biology-human-body-diseases',
            'heading': '3. Biology — Cells, Human Body Systems, Hormones, Vitamins & Diseases',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Biology in MPSC/MSSSB revolves around **cell organelles, endocrine hormones, blood groups, vitamin deficiencies, and pathogen classification (viral vs bacterial vs protozoan)**.',
                '### Vitamins & Deficiency Diseases\n\n'
                '| Vitamin | Chemical Name | Solubility | Deficiency Disease |\n'
                '| --- | --- | --- | --- |\n'
                '| Vitamin A | Retinol | Fat (A, D, E, K) | Night blindness, Xerophthalmia |\n'
                '| Vitamin B₁ | Thiamine | Water (B, C) | Beri-beri |\n'
                '| Vitamin B₃ / B₁₂ | Niacin / Cobalamin | Water | Pellagra / Pernicious anaemia (contains Cobalt) |\n'
                '| Vitamin C | Ascorbic acid | Water | Scurvy (bleeding gums) |\n'
                '| Vitamin D | Calciferol | Fat | Rickets (children), Osteomalacia (adults) |\n'
                '| Vitamin K | Phylloquinone | Fat | Delayed blood clotting |',
                '### Endocrine Glands & Hormones\n\n'
                '| Gland | Hormone | Core Function / Disorder |\n'
                '| --- | --- | --- |\n'
                '| Pituitary (“Master Gland”) | Growth Hormone (GH), TSH | Controls other glands; Dwarfism / Gigantism |\n'
                '| Thyroid | Thyroxine (needs Iodine) | Metabolism; deficiency causes **Goitre** |\n'
                '| Pancreas (Islets of Langerhans) | **Insulin** (Beta cells) / Glucagon (Alpha) | Lowers / raises blood sugar (**Diabetes mellitus**) |\n'
                '| Adrenal | Adrenaline | Fight-or-flight emergency hormone |',
                '- **Cell Organelles:** Mitochondria = powerhouse (ATP); Ribosomes = protein synthesis (built from **amino acids**); Lysosomes = suicidal bags; Chloroplast = photosynthesis (plants).\n'
                '- **Blood:** Universal Donor = **O−** (O); Universal Recipient = **AB+** (AB); Red colour = Haemoglobin (Iron); Clotting = Platelets + Fibrinogen + Vitamin K.\n'
                '- **Pathogens:** Viral (Polio, Dengue, AIDS, Rabies, Measles, COVID-19); Bacterial (TB, Typhoid, Cholera, Tetanus, Leprosy); Protozoan (Malaria — *Plasmodium* via female *Anopheles*, Kala-azar, Amoebiasis).',
                '**Exam Trap:** **Beta cells** of the Islets of Langerhans in the pancreas secrete **Insulin** (which *lowers* blood glucose), while Alpha cells secrete Glucagon. **Bile** is produced by the **Liver** (largest gland) and stored in the Gall Bladder — it emulsifies fats but contains **no digestive enzymes**.',
            ]),
            'practice_query': '/subjects/science?view=browse#exam-question-browser',
            'practice_label': 'Practise Biology MCQs (331 Qs) →',
        },
        {
            'ord': 4,
            'anchor': 'space-isro-applied-science',
            'heading': '4. Space (ISRO PSLV/GSLV), Defence & Applied Science',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** ISRO & Science-in-the-News questions test **launch vehicles (PSLV vs GSLV/LVM3), orbits (LEO vs GEO), landmark Indian missions, and nuclear/biotech basics**.',
                '### ISRO Launch Vehicles Compared\n\n'
                '| Vehicle | Stages & Fuel | Target Orbit & Role |\n'
                '| --- | --- | --- |\n'
                '| **PSLV** (Workhorse) | 4 stages (Solid–Liquid–Solid–Liquid) | Sun-Synchronous Polar Orbit (SSPO) — remote sensing, Chandrayaan-1, Mangalyaan, Aditya-L1 |\n'
                '| **GSLV Mk-II** | 3 stages (Solid–Liquid–**Cryogenic** LOX/LH₂) | Geosynchronous Transfer Orbit (GTO) — heavier communication satellites (~2.2 tonnes) |\n'
                '| **LVM3** (formerly GSLV Mk-III) | 3 stages (2 solid S200 + L110 liquid + C25 cryogenic) | Heavy-lift (~4 tonnes GTO) — Chandrayaan-2, Chandrayaan-3, Gaganyaan |',
                '- **Key ISRO Centres:** HQ = Bengaluru; Vikram Sarabhai Space Centre (VSSC) = Thiruvananthapuram; Satish Dhawan Space Centre (SDSC) = **Sriharikota** (Andhra Pradesh, launchpad).\n'
                '- **Landmark Missions:** Aryabhata (1975, first Indian satellite), Chandrayaan-1 (2008, lunar water), Mangalyaan / MOM (2013, first Asian Mars orbiter), Chandrayaan-3 (Aug 2023, lunar south pole soft landing — *Shiv Shakti* point), Aditya-L1 (Sun–Earth L1 point).\n'
                '- **Nuclear Energy:** Fission (splitting heavy U-235/Pu-239 in reactors; Heavy Water `D₂O` or Graphite = moderator, Cadmium/Boron = control rods) vs Fusion (combining light H nuclei — powers the Sun & stars).',
                '**Exam Trap:** The core difference between **PSLV** and **GSLV** is **payload capacity + target orbit + cryogenic upper stage** (PSLV has 4 alternating solid/liquid stages for polar orbits; GSLV uses a 3rd-stage **cryogenic engine** to push heavier communication satellites to GTO).',
            ]),
            'practice_query': '/subjects/science?view=browse#exam-question-browser',
            'practice_label': 'Practise General Science MCQs (1,572 Qs) →',
        },
    ]
    return {
        'slug': 'general-science',
        'title': 'General Science Essentials',
        'subject_id': 'science',
        'subject_label': 'General Science',
        'topic_id': 'science/physics',
        'exam_scope': ['udc', 'ldc', 'combined-prelims', 'subject-science'],
        'summary': '4 high-yield chapters covering Physics (SI units, optics, electricity), Chemistry (formulas, alloys, acids), Biology (vitamins, hormones, diseases), and ISRO/Space — linked to 1,572+ Science PYQs.',
        'reading_minutes': 15,
        'status': 'published',
        'chapters': chapters,
    }


def build_economy_guide() -> dict:
    chapters = [
        {
            'ord': 1,
            'anchor': 'national-income-gdp',
            'heading': '1. National Income, GDP/GNP & Sectors of the Economy',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** **Domestic (GDP)** cares about *geography* (produced inside India’s borders regardless of nationality); **National (GNP)** cares about *citizenship* (produced by Indian residents anywhere in the world).',
                '### Core National Income Identities\n\n'
                '| Formula | Meaning |\n'
                '| --- | --- |\n'
                '| `GNP = GDP + NFIA` | Add Net Factor Income from Abroad |\n'
                '| `NDP = GDP − Depreciation` | Net = Gross minus Wear & Tear |\n'
                '| `NNP (at Factor Cost) = National Income` | NNP at Market Price − Indirect Taxes + Subsidies |\n'
                '| `Per Capita Income = National Income ÷ Population` | Average income per citizen |\n'
                '| `Real GDP = Nominal GDP ÷ (GDP Deflator / 100)` | Adjusted for inflation (base year prices) |',
                '- **Three Sectors:** **Primary** (Agriculture, Forestry, Fishing, Mining — largest employer in India), **Secondary** (Manufacturing, Construction, Utilities), **Tertiary / Services** (IT, Banking, Trade, Transport — **largest contributor to India’s GDP**, >50%).\n'
                '- **Official Agency:** National Statistical Office (**NSO**, under MoSPI — formed by merging CSO & NSSO) estimates India’s GDP.',
                '**Exam Trap:** **Real GDP** (constant base-year prices) measures true volume growth, whereas **Nominal GDP** includes price inflation. Transfer payments (pensions, scholarships, unemployment dole) are **excluded** from National Income because no current good/service is produced.',
            ]),
            'practice_query': '/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id=gk-gs%3Aindian-economy#exam-question-browser',
            'practice_label': 'Practise Indian Economy MCQs (677 Qs) →',
        },
        {
            'ord': 2,
            'anchor': 'rbi-money-banking',
            'heading': '2. Money, Banking, RBI Monetary Policy & Financial Schemes',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** The **Reserve Bank of India (RBI)** — established 1 April 1935 (Hilton Young Commission), nationalised 1 Jan 1949 — controls inflation and liquidity via **Quantitative** (economy-wide) and **Qualitative** (sector-specific) credit control tools.',
                '### RBI Monetary Policy Instruments\n\n'
                '| Instrument | Mechanism | Effect When Raised (Hawkish) |\n'
                '| --- | --- | --- |\n'
                '| **Repo Rate** | Rate at which banks borrow short-term from RBI against govt securities | Borrowing costlier → curbs inflation |\n'
                '| **Reverse Repo / SDF** | Rate at which RBI absorbs surplus liquidity from banks | Banks park cash with RBI → reduces money supply |\n'
                '| **CRR** (Cash Reserve Ratio) | % of NDTL kept as **cash** with RBI (earns 0% interest) | Reduces lendable funds |\n'
                '| **SLR** (Statutory Liquidity Ratio) | % of NDTL kept by banks in liquid assets (cash, gold, G-Secs) | Restricts commercial lending |\n'
                '| **Bank Rate** | Long-term discount/penalty rate without collateral | Signals dear money |\n'
                '| **OMO** (Open Market Operations) | RBI buys/sells Govt securities in open market | Selling G-Secs sucks out liquidity |',
                '### Flagship Financial Inclusion Schemes\n\n'
                '| Scheme | Key Exam Facts |\n'
                '| --- | --- |\n'
                '| **PM MUDRA Yojana (PMMY)** | Collateral-free micro-enterprise loans: **Shishu** (up to ₹50,000), **Kishor** (₹50,001–₹5 lakh), **Tarun** (₹5 lakh–₹10 lakh; Tarun Plus up to ₹20 lakh) |\n'
                '| **PM Jan Dhan Yojana (2014)** | Zero-balance bank accounts, RuPay debit card, overdraft facility |\n'
                '| **NABARD (1982)** | Apex rural & agricultural credit institution (Sivaraman Committee) |\n'
                '| **SEBI (1988; statutory 1992)** | Capital market & stock exchange regulator |',
                '**Exam Trap:** **Taxation and Government Expenditure** are **Fiscal Policy** tools (Ministry of Finance), **NOT** RBI credit-control instruments! The **Monetary Policy Committee (MPC)** has **6 members** (3 RBI + 3 Govt), chaired by the RBI Governor, targeting CPI inflation at **4% ± 2%**.',
            ]),
            'practice_query': '/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id=gk-gs%3Aindian-economy#exam-question-browser',
            'practice_label': 'Practise RBI & Banking MCQs →',
        },
        {
            'ord': 3,
            'anchor': 'budget-fiscal-taxation',
            'heading': '3. Union Budget, Fiscal Deficits, GST & Taxation',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Under **Art. 112**, the Union Budget (“Annual Financial Statement”) splits into **Revenue Account** (day-to-day income & expenses that don’t change assets/liabilities) and **Capital Account** (loans, borrowings, disinvestment, and asset creation like highways).',
                '### Budget Deficits & Tax Classification\n\n'
                '| Term | Exact Formula / Meaning |\n'
                '| --- | --- |\n'
                '| **Revenue Deficit** | Revenue Expenditure − Revenue Receipts |\n'
                '| **Fiscal Deficit** | Total Expenditure − (Revenue Receipts + Non-Debt Capital Receipts) = **Total Borrowing** |\n'
                '| **Primary Deficit** | **Fiscal Deficit − Interest Payments** (current-year borrowing excluding past debt interest) |\n'
                '| **Direct Taxes** | Burden cannot be shifted: **Income Tax**, Corporate Tax, Capital Gains Tax |\n'
                '| **Indirect Taxes** | Burden shifted to consumer: **GST** (101st Amendment, 1 July 2017), **Customs Duty** (export/import) |',
                '- **GST Council (Art. 279A):** Chaired by the Union Finance Minister; Centre has 1/3rd voting weight, States 2/3rd; decisions require 3/4th majority.\n'
                '- **Finance Commission (Art. 280):** Constitutional body constituted every 5 years by the President to recommend Centre–State tax devolution (16th FC chaired by Dr. Arvind Panagariya).',
                '**Exam Trap:** **Customs Duty** is the tax imposed on the **import and export of commodities**. **GST** subsumed VAT, Excise, and Service Tax, but **petroleum products and alcohol for human consumption** remain outside GST.',
            ]),
            'practice_query': '/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id=gk-gs%3Aindian-economy#exam-question-browser',
            'practice_label': 'Practise Budget & Taxation MCQs →',
        },
        {
            'ord': 4,
            'anchor': 'inflation-unemployment-planning',
            'heading': '4. Inflation, Unemployment, Poverty & Planning (NITI Aayog)',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Distinguishing the **type of unemployment**, **type of inflation**, and **milestone Five-Year Plans** answers a huge share of GS Economy MCQs.',
                '### Types of Unemployment & Inflation\n\n'
                '| Type | Classic Exam Definition |\n'
                '| --- | --- |\n'
                '| **Disguised Unemployment** | More workers employed than needed (**marginal productivity = 0**) — classic feature of **Indian agriculture** |\n'
                '| **Seasonal Unemployment** | Work available only during specific seasons (sowing/harvesting, tourism) |\n'
                '| **Structural Unemployment** | Skill mismatch between workers and modern job requirements |\n'
                '| **Frictional Unemployment** | Temporary gap while switching between jobs |\n'
                '| **Demand-Pull vs Cost-Push** | Too much money chasing too few goods vs rising input/wage costs |\n'
                '| **Stagflation** | Stagnant growth + high unemployment + high inflation together |',
                '- **CPI vs WPI:** **CPI** (Consumer Price Index, NSO) covers **goods + services** at retail level (RBI’s policy anchor); **WPI** (Wholesale Price Index, DPIIT) covers **only goods** (no services).\n'
                '- **Planning Milestones:** 1st FYP (1951–56, Harrod–Domar, agriculture); 2nd FYP (1956–61, **Mahalanobis**, heavy industry); 5th FYP (*Garibi Hatao*); **1991 LPG Reforms** (Liberalisation, Privatisation, Globalisation — PV Narasimha Rao & Dr. Manmohan Singh); **NITI Aayog** replaced Planning Commission on **1 Jan 2015** (PM = ex-officio Chairman).\n'
                '- **Inequality:** **Lorenz Curve** plots income distribution; **Gini Coefficient** (0 = perfect equality, 1 = total inequality) measures it.',
                '**Exam Trap:** **Disguised unemployment** (zero marginal productivity of extra hands on a family farm) is the hallmark of Indian agriculture. **NITI Aayog** is a **non-constitutional, non-statutory** policy think-tank — it does *not* allocate funds to States.',
            ]),
            'practice_query': '/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id=gk-gs%3Aindian-economy#exam-question-browser',
            'practice_label': 'Practise Inflation & Planning MCQs →',
        },
        {
            'ord': 5,
            'anchor': 'bop-trade-global-bodies',
            'heading': '5. Balance of Payments, Foreign Trade & International Institutions',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** **Balance of Payments (BoP)** records all economic transactions between a country and the rest of the world in two accounts: **Current Account** (trade in goods/services + remittances) and **Capital Account** (FDI, FPI, external borrowings).',
                '### Current Account vs. Capital Account\n\n'
                '| BoP Account | What Goes Inside |\n'
                '| --- | --- |\n'
                '| **Current Account** | Export & import of **goods** (Balance of Trade), **services** (IT, tourism), primary income (dividends/interest), **remittances & unilateral transfers** |\n'
                '| **Capital / Financial Account** | **FDI** (long-term ownership/management ≥10%), **FPI/FII** (portfolio stocks/bonds), External Commercial Borrowings (ECB), NRI deposits |',
                '### Key Global Economic Institutions\n\n'
                '| Institution | HQ | Core Mandate |\n'
                '| --- | --- | --- |\n'
                '| **IMF** (Bretton Woods, 1944) | Washington D.C. | BoP crisis lending, exchange stability, **SDR** (Special Drawing Rights) |\n'
                '| **World Bank** (IBRD + IDA) | Washington D.C. | Long-term development & poverty reduction loans |\n'
                '| **WTO** (1995, replaced GATT) | Geneva | Global trade rules, tariff reduction, dispute settlement |\n'
                '| **ADB** (1966) / **NDB** (BRICS) | Manila / Shanghai | Asian & BRICS infrastructure/development finance |',
                '**Exam Trap:** **Balance of Trade (BoT)** counts **only visible goods** (merchandise); **Current Account** counts goods + invisible services + remittances. **Devaluation** (official fixed-rate cut) or **Depreciation** (market fall) makes **exports cheaper** and **imports costlier**.',
            ]),
            'practice_query': '/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id=gk-gs%3Aindian-economy#exam-question-browser',
            'practice_label': 'Practise BoP & Global Trade MCQs →',
        },
    ]
    return {
        'slug': 'indian-economy',
        'title': 'Indian Economy & Banking',
        'subject_id': 'gk-gs',
        'subject_label': 'Indian Economy',
        'topic_id': 'gk-gs:indian-economy',
        'exam_scope': ['udc', 'ldc', 'combined-prelims', 'subject-gk-gs'],
        'summary': '5 focused Economy chapters — National Income/GDP, RBI Monetary Policy & MUDRA, Budget Deficits & GST, Unemployment/Inflation/NITI Aayog, and Balance of Payments — mapped to 677+ Economy PYQs.',
        'reading_minutes': 15,
        'status': 'published',
        'chapters': chapters,
    }


def build_reasoning_guide() -> dict:
    chapters = [
        {
            'ord': 1,
            'anchor': 'series-ejoty-patterns',
            'heading': '1. Number, Alphabet & Alphanumeric Series (EJOTY Trick)',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Every series follows one of six disciplined engines — check **differences first**, then **double differences**, then **alternating series**, then **squares/cubes (n² ± 1, n³ ± 1)**, then **multipliers**, and for letters convert to numbers using **EJOTY**.',
                '### Alphabet Position Shortcuts (A=1 … Z=26)\n\n'
                '| Anchor Letter | Position | Opposite Pair (Sum = 27) |\n'
                '| --- | --- | --- |\n'
                '| **E** | 5 | E ↔ V (5 + 22 = 27) |\n'
                '| **J** | 10 | J ↔ Q (10 + 17 = 27) |\n'
                '| **O** | 15 | O ↔ L (15 + 12 = 27) |\n'
                '| **T** | 20 | T ↔ G (20 + 7 = 27) |\n'
                '| **Y** | 25 | Y ↔ B (25 + 2 = 27) |',
                '**Worked Example:** *MPSC Series:* `SCD, TEF, UGH, ____, WKL`. Split each triplet into 3 independent tracks: 1st letters `S → T → U → V → W` (+1); 2nd & 3rd letters `CD → EF → GH → IJ → KL` (+2 pairs). Answer = **`VIJ`**.',
                '**Exam Trap:** If a number series jumps up and down unpredictably (e.g., `2, 15, 4, 12, 6, 9, ?`), immediately split into **two interleaved alternating series** (odd positions vs even positions).',
            ]),
            'practice_query': '/subjects/reasoning?view=browse#exam-question-browser',
            'practice_label': 'Practise Series & Pattern MCQs →',
        },
        {
            'ord': 2,
            'anchor': 'coding-analogy-classification',
            'heading': '2. Coding-Decoding, Analogy & Odd-One-Out',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Write the original word **directly above** the coded word and inspect column-by-column: check (1) uniform shift (`+k` / `-k`), (2) **reverse order** + shift, (3) **opposite letters** (sum = 27), (4) **case / vowel–consonant** rules, and (5) **direct substitution**.',
                '**Worked Example:** *MPSC Coding:* `POTASSIUM` is coded as `PoTassium` — how is `GRAPHITE` coded? Notice the exact pattern: letters at positions 1 and 3 stay **UPPERCASE**, all other letters become **lowercase** (`P` o `T` assium → `G` r `A` phite = **`GrAphite`**). Always inspect capitalisation and letter swaps before hunting for arithmetic shifts!',
                '- **Analogy checklist:** Capital–Country, Instrument–Measurement, Worker–Tool, Animal–Young One, Cause–Effect, Synonym/Antonym, `n : n² + n`.\n'
                '- **Odd-One-Out priority:** Prime numbers → Squares/Cubes → Divisibility → Digit sum → Vowel count.',
                '**Memory Hook:** Opposite-letter pairs (sum = 27): **A**Z (Azad), **B**Y (Boy), **C**X (Crux), **D**W (Dew), **E**V (Even), **F**U (Full), **G**T (GT Road), **H**S (High School), **I**R (Indian Railway), **J**Q (Jungle Queen), **K**P (Kanpur), **L**O (Love), **M**N (Man).',
            ]),
            'practice_query': '/subjects/reasoning?view=browse#exam-question-browser',
            'practice_label': 'Practise Coding & Verbal Reasoning MCQs →',
        },
        {
            'ord': 3,
            'anchor': 'seating-ranking-order',
            'heading': '3. Seating Arrangements (Circular & Linear) & Ranking',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Never guess seating layouts in your head — draw slots immediately and anchor the **most constrained clue first** (e.g., “second to the left of X” or “not at any end”).',
                '### Circular & Ranking Formulas\n\n'
                '| Situation | Rule / Formula |\n'
                '| --- | --- |\n'
                '| Facing **Centre** (Circle) | **Left = Clockwise**; **Right = Anti-clockwise** |\n'
                '| Facing **Outside** (Circle) | **Left = Anti-clockwise**; **Right = Clockwise** |\n'
                '| Facing **North** (Row) | Left = your left; Right = your right (Facing South = flipped!) |\n'
                '| Total in a Row (Rank from both ends) | `Total = Left Rank + Right Rank − 1` |\n'
                '| People strictly between A and B (non-overlap) | `Between = Total − (Left_A + Right_B)` |\n'
                '| Position swap between two people | `Total = New_Pos(A) + Old_Pos(B) − 1` |',
                '**Worked Example:** *Ranking:* If Ram is 12th from the left and 19th from the right in a queue, total students = `12 + 19 − 1 = 30`. Always subtract 1 so Ram is not counted twice.',
                '**Exam Trap:** In phrasing like *“A sits 2nd to the right of B, **who** sits next to C”*, the pronoun **“who / whom / whose”** refers to the **immediately preceding person (B)**, whereas **“and / but”** refers to the **first subject (A)**.',
            ]),
            'practice_query': '/subjects/reasoning?view=browse#exam-question-browser',
            'practice_label': 'Practise Seating & Ranking MCQs →',
        },
        {
            'ord': 4,
            'anchor': 'blood-relations-directions',
            'heading': '4. Blood Relations & Direction Sense',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Draw a **3-row family tree** (vertical lines = parent/child, double horizontal `=` = married couple, single horizontal `—` = siblings, `+` male / `−` female). For Directions, track **Net North–South** and **Net East–West** separately, then apply Pythagoras.',
                '### Direction & Shadow Shortcuts\n\n'
                '| Case | Fast Rule |\n'
                '| --- | --- |\n'
                '| Shortest distance | `√(ΔN-S² + ΔE-W²)` — watch for **3–4–5**, **5–12–13**, **8–15–17** triples! |\n'
                '| Turn cancellation | Every `1 Left + 1 Right` cancels out; `4 Right` or `4 Left` = same direction; `2 Right` = opposite |\n'
                '| **Morning** (Sun in East) | Shadows fall **West**. If shadow is to your **Left**, you face **North** |\n'
                '| **Evening** (Sun in West) | Shadows fall **East**. If shadow is to your **Left**, you face **South** |',
                '**Exam Trap:** In Blood Relations, **never assume gender from a name** (e.g., “Kiran” or “Zira”) unless explicitly stated via *son, daughter, father, sister, husband, wife*. Break pointing questions backwards starting from **“my …”**.',
            ]),
            'practice_query': '/subjects/reasoning?view=browse#exam-question-browser',
            'practice_label': 'Practise Blood Relations & Direction MCQs →',
        },
        {
            'ord': 5,
            'anchor': 'syllogism-clocks-calendars-images',
            'heading': '5. Syllogisms, Venn Diagrams, Clocks, Calendars & Mirror/Water Images',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** Turn visual & time puzzles into **exact mechanical formulas** so you never second-guess under exam pressure.',
                '### Clocks, Calendars & Mirror/Water Image Formulas\n\n'
                '| Topic | Exact Formula / Rule |\n'
                '| --- | --- |\n'
                '| Angle between Clock Hands at `H : M` | `θ = |30H − 5.5M|` (reflex angle = `360° − θ`) |\n'
                '| Hands coincide / opposite / right-angle | In 12 hrs: **11** times coincide, **11** times opposite (180°), **22** times right-angle (90°) |\n'
                '| Calendar Odd Days | Normal year (365d) = **1 odd day**; Leap year (366d) = **2 odd days**; 100/200/300/400 yrs = **5 / 3 / 1 / 0** |\n'
                '| **Mirror Image** (Vertical mirror) | **Left ↔ Right flips**; Top & Bottom stay unchanged |\n'
                '| **Water Image** (Horizontal mirror) | **Top ↔ Bottom flips**; Left & Right stay unchanged |\n'
                '| Syllogism “Either–Or” | Both conclusions individually false + same subject/predicate + complementary pair (*Some + No* or *Some + Some not*) |',
                '**Worked Example:** *Clock Angle at 3:20:* `θ = |30(3) − 5.5(20)| = |90 − 110| = 20°`.',
                '**Exam Trap:** Century years (`1900`, `2100`) are **NOT leap years** unless divisible by **400** (`2000`, `2400` are leap years). In Syllogisms, a definite conclusion must hold in **all** valid Venn diagrams — never assume “Some A are B” implies “Some A are not B”.',
            ]),
            'practice_query': '/subjects/reasoning?view=browse#exam-question-browser',
            'practice_label': 'Practise Syllogism, Clocks & Images MCQs →',
        },
        {
            'ord': 6,
            'anchor': 'data-interpretation-decision',
            'heading': '6. Data Interpretation & Analytical Decision-Making',
            'body_markdown': '\n\n'.join([
                '**Core Mental Model:** 90% of Data Interpretation (Tables, Bar Graphs, Line Charts, Pie Charts) uses just **three calculations**: Percentage Change, Ratio, and Average — speed comes from **approximation & fraction equivalents**.',
                '### Pie Chart & DI Speed Conversions\n\n'
                '| Quantity | Conversion |\n'
                '| --- | --- |\n'
                '| Pie Chart Full Circle | `100% = 360°` → `1% = 3.6°` and `10% = 36°` |\n'
                '| % More / Less than B | `(Difference ÷ Base after “than”) × 100` |\n'
                '| Growth Rate (CAGR approx.) | Check absolute jump vs smaller base year first |\n'
                '| Decision-Making / Conflict Resolution | Pick options that are **objective, lawful, evidence-based, and collaborative** — reject extreme, biased, or impulsive choices |',
                '**Exam Trap:** In Pie Charts, never compute raw values for two slices if the question only asks for their **ratio** or **percentage difference** — divide the **percentages or central angles directly** to save 45 seconds!',
            ]),
            'practice_query': '/subjects/reasoning?view=browse#exam-question-browser',
            'practice_label': 'Practise Reasoning & DI MCQs (1,533 Qs) →',
        },
    ]
    return {
        'slug': 'reasoning-aptitude',
        'title': 'Reasoning & Mental Ability',
        'subject_id': 'reasoning',
        'subject_label': 'Reasoning',
        'topic_id': 'reasoning-and-aptitude/verbal-reasoning',
        'exam_scope': ['udc', 'ldc', 'combined-prelims', 'subject-reasoning'],
        'summary': '6 shortcut-packed Reasoning chapters — EJOTY Series, Coding-Decoding, Circular/Linear Seating, Blood Relations & Directions, Clocks/Calendars/Mirror-Water Images, and Data Interpretation — linked to 1,533+ Reasoning PYQs.',
        'reading_minutes': 16,
        'status': 'published',
        'chapters': chapters,
    }


def strip_prior_polity_enhancements(md: str) -> str:
    """Keep script idempotent if run multiple times on polity-codex."""
    marker = '### Key Constitutional Notes\n\n'
    if marker in md:
        return md.split(marker, 1)[1].strip()
    return md.strip()


def main() -> None:
    existing = json.loads(GUIDES_SEED.read_text(encoding='utf-8'))
    upgraded: list[dict] = []
    rebuilt_slugs = {
        'maths-and-arithmetic',
        'geography-essentials',
        'history-essentials',
        'computer-fundamentals',
        'general-science',
        'indian-economy',
        'reasoning-aptitude',
    }

    for guide in existing:
        slug = guide['slug']
        if slug in rebuilt_slugs:
            continue
        if slug == 'polity-codex':
            guide['subject_id'] = 'gk-gs'
            guide['subject_label'] = 'Indian Polity'
            guide['topic_id'] = 'gk-gs:indian-polity'
            guide['exam_scope'] = ['udc', 'ldc', 'combined-prelims', 'subject-gk-gs']
            guide['summary'] = (
                'Complete 21-chapter Indian Constitution & Polity reference with comparison tables, writ/emergency cheat sheets, exam traps, and Mizoram Art. 371G & Sixth Schedule coverage — linked directly to 1,297 Polity PYQs.'
            )
            for ch in guide.get('chapters', []):
                anc = ch.get('anchor', '')
                if anc in POLITY_HEADINGS:
                    ch['heading'] = POLITY_HEADINGS[anc]
                raw_body = strip_prior_polity_enhancements(ch.get('body_markdown', ''))
                enh = POLITY_ENHANCEMENTS.get(anc)
                if enh:
                    parts: list[str] = []
                    if enh.get('model'):
                        parts.append(f"**Core Mental Model:** {enh['model']}")
                    if enh.get('table'):
                        parts.append(enh['table'])
                    if enh.get('hook'):
                        parts.append(f"**Memory Hook:** {enh['hook']}")
                    if enh.get('trap'):
                        parts.append(f"**Exam Trap:** {enh['trap']}")
                    parts.append(f"### Key Constitutional Notes\n\n{raw_body}")
                    ch['body_markdown'] = '\n\n'.join(parts)
                ch['practice_query'] = '/subjects/gk-gs?view=browse&subject_id=gk-gs&topic_id=gk-gs%3Aindian-polity#exam-question-browser'
                ch['practice_label'] = 'Practise Indian Polity MCQs (1,297 Qs) →'
                if anc in POLITY_ATLAS_MAP:
                    ch['companion_href'] = POLITY_ATLAS_MAP[anc]
                    ch['companion_label'] = 'Open Polity map in Atlas →'
        upgraded.append(guide)

    upgraded.extend([
        build_maths_guide(),
        build_geography_guide(),
        build_history_guide(),
        build_computer_guide(),
        build_science_guide(),
        build_economy_guide(),
        build_reasoning_guide(),
    ])

    GUIDES_SEED.write_text(json.dumps(upgraded, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    catalog = [
        {
            'slug': g['slug'],
            'title': g['title'],
            'subject_id': g.get('subject_id'),
            'subject_label': g.get('subject_label'),
            'topic_id': g.get('topic_id'),
            'summary': g.get('summary', ''),
            'reading_minutes': g.get('reading_minutes', 10),
            'chapter_count': len(g.get('chapters', [])),
            'status': g.get('status', 'published'),
        }
        for g in upgraded
    ]
    catalog_path = ROOT / 'web/src/data/guides-catalog.json'
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Enriched {GUIDES_SEED}: {len(upgraded)} guides (catalog: {catalog_path.stat().st_size} bytes)')
    for g in upgraded:
        tables = sum(1 for c in g['chapters'] if '| --- |' in c['body_markdown'])
        examples = sum(1 for c in g['chapters'] if '**Worked Example:**' in c['body_markdown'])
        traps = sum(1 for c in g['chapters'] if '**Exam Trap:**' in c['body_markdown'])
        print(f"  - {g['slug']:22s} | ch={len(g['chapters']):2d} | tables={tables:2d} | examples={examples:2d} | traps={traps:2d}")


if __name__ == '__main__':
    main()
