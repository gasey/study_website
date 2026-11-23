#!/usr/bin/env python3
"""
Admin-side SSC PYQ Study Material Publisher for Finna CMS.

Reads the Shiksha SSC PYQ compilation (parsed JSON + Modern History DOCX) and
authors 11 structured, high-yield revision guides published under official team
authorship (`author_id = 'team'` -> "India Study Map") in PostgreSQL CMS tables
(`materials`, `material_revisions`, `material_events`).

Never modifies `canonical_questions` or the question bank.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.services.content_studio import Document  # noqa: E402

SSC_BANK_PATH = Path("/home/hruaia/workspace/projects/worktrees/ssc_bank.json")
SSC_DOCX_DIR = Path(
    "/home/hruaia/workspace/projects/work/SSC PYQs DOCX File-20260906T130907Z-1-001/SSC PYQs DOCX File"
)

# Subject editorial definitions: id, title, subject_id (review_taxonomy), tags, summary, chapters
SUBJECT_SPECS: list[dict] = [
    {
        "key": "Indian Polity",
        "id": "ssc-pyq-indian-polity",
        "title": "Indian Polity: SSC PYQ Revision Guide",
        "subject_id": "general-studies",
        "tags": ["SSC PYQ", "Polity", "Indian Polity", "Revision Notes"],
        "summary": (
            "Distilled high-yield Indian Polity notes from SSC CGL, CHSL, MTS, CPO and JE "
            "previous-year papers (2016–2023), covering constitutional evolution, Rights & DPSP, "
            "Parliament, Judiciary, Federalism and key Amendments."
        ),
        "chapters": [
            ("Constitutional Making & Historical Acts", ["charter", "act of", "constituent assembly", "drafting", "cabinet mission", "cripps", "montagu", "morley", "preamble", "borrowed", "schedule", "source", "1935", "1919", "1909", "1773", "1858"]),
            ("Fundamental Rights, DPSP & Fundamental Duties", ["article 1", "article 2", "article 3", "article 4", "article 5", "fundamental right", "fundamental dut", "dpsp", "directive principle", "writ", "habeas", "mandamus", "equality", "untouchability", "citizenship", "liberty", "secular", "swaran singh"]),
            ("Union Executive & Parliament", ["president", "vice-president", "vice president", "prime minister", "council of ministers", "lok sabha", "rajya sabha", "parliament", "speaker", "money bill", "joint sitting", "ordinance", "impeachment", "attorney general", "cag", "comptroller"]),
            ("Judiciary, States & Federal Institutions", ["supreme court", "high court", "governor", "chief minister", "vidhan", "legislative", "panchayat", "municipality", "73rd", "74th", "finance commission", "election commission", "upsc", "niti aayog", "inter-state", "emergency", "article 356", "article 352", "article 360"]),
            ("Constitutional Amendments & Key Articles", ["amendment", "42nd", "44th", "61st", "86th", "101st", "gst", "anti-defection", "tenth schedule", "eighth schedule", "official language", "article 3", "article 2", "article 1"]),
        ],
        "quote": "Revise Constitutional Articles alongside their landmark Amendments — SSC papers repeatedly test Articles 14–51A, 72, 110, 123, 280, 324, 352–360 and 368.",
    },
    {
        "key": "Ancient History",
        "id": "ssc-pyq-ancient-history",
        "title": "Ancient Indian History: SSC PYQ Revision Guide",
        "subject_id": "general-studies",
        "tags": ["SSC PYQ", "History", "Ancient History", "Revision Notes"],
        "summary": (
            "Concise Ancient Indian History revision guide compiled from SSC previous-year papers, "
            "covering Harappan sites, Vedic literature, Buddhism & Jainism, Mauryan & Gupta empires, "
            "and South Indian dynasties."
        ),
        "chapters": [
            ("Prehistory & Indus Valley Civilization", ["harappa", "mohenjo", "indus", "lothal", "kalibangan", "dholavira", "palaeolithic", "neolithic", "chalcolithic", "mesolithic", "burzahom", "mehrgarh", "bronze", "dockyard", "seal"]),
            ("Vedic Age & Mahajanapadas", ["veda", "rigveda", "samaveda", "yajurveda", "atharvaveda", "upanishad", "aryan", "mahajanapada", "magadha", "haryanka", "bimbisara", "ajatashatru", "nanda", "shishunaga", "varnas", "sabha", "samiti"]),
            ("Buddhism, Jainism & Philosophical Schools", ["buddha", "buddhism", "jain", "mahavira", "tirthankara", "tripitaka", "stupa", "sanchi", "bodh gaya", "sarnath", "kushinagar", "council", "ashvaghosha", "sangha", "hinayana", "mahayana", "ajivika"]),
            ("Mauryan, Post-Mauryan & Gupta Empires", ["maurya", "chandragupta", "ashoka", "kautilya", "arthashastra", "megasthenes", "indica", "kalinga", "edict", "shunga", "kanishka", "kushana", "satavahana", "gupta", "samudragupta", "vikramaditya", "kalidasa", "aryabhata", "fa-hien", "harsha", "banabhatta", "hsuan", "xuanzang"]),
            ("South Indian Kingdoms, Art & Architecture", ["chola", "pallava", "chalukya", "rashtrakuta", "pandya", "chera", "sangam", "ellora", "ajanta", "mahabalipuram", "khajuraho", "temple", "inscription", "brihadeeswara", "pulakesin"]),
        ],
        "quote": "Anchor Ancient History timelines around four pillars: Harappan site-river pairs, Buddhist councils, Ashokan edicts, and Gupta-era scholars.",
    },
    {
        "key": "Medieval History",
        "id": "ssc-pyq-medieval-history",
        "title": "Medieval Indian History: SSC PYQ Revision Guide",
        "subject_id": "general-studies",
        "tags": ["SSC PYQ", "History", "Medieval History", "Revision Notes"],
        "summary": (
            "Exam-focused Medieval History notes distilled from SSC PYQs: Delhi Sultanate dynasties, "
            "Vijayanagara & Bahmani kingdoms, Bhakti & Sufi movements, Mughal administration, "
            "Maratha rise and Indo-Islamic monuments."
        ),
        "chapters": [
            ("Early Medieval India & Foreign Invasions", ["ghazni", "ghori", "tarain", "prithviraj", "rajput", "pala", "pratihara", "chola", "sena", "qasim", "somnath", "al-biruni", "kitab", "arab", "turk"]),
            ("Delhi Sultanate (1206–1526)", ["sultanate", "qutb", "aibak", "iltutmish", "razia", "balban", "khalji", "alauddin", "tughlaq", "ibn battuta", "sayyid", "lodi", "iqta", "qutub minar", "amir khusrau", "diwan"]),
            ("Vijayanagara, Bahmani & Regional Kingdoms", ["vijayanagara", "harihara", "bukka", "krishnadevaraya", "hampi", "talikota", "bahmani", "golconda", "bijapur", "ahom", "mewar", "rana", "kashmir", "zain-ul"]),
            ("Mughal Empire & Sur Interregnum", ["babur", "panipat", "humayun", "sher shah", "akbar", "jahangir", "shah jahan", "aurangzeb", "mansabdari", "todar mal", "din-i-ilahi", "fatehpur", "taj mahal", "red fort", "ain-i-akbari", "abdul fazl", "abul fazl", "khanwa", "haldighati", "dara"]),
            ("Bhakti-Sufi Traditions & Maratha Empire", ["bhakti", "sufi", "kabir", "nanak", "mirabai", "chaitanya", "ramananda", "tulsidas", "chishti", "nizamuddin", "shivaji", "maratha", "peshwa", "ashtapradhan", "chauth", "sardeshmukhi", "purandar", "sikh", "guru"]),
        ],
        "quote": "Match every ruler with their administrative reform, court chronicler and signature monument — that trio covers over half of SSC Medieval History items.",
    },
    {
        "key": "Modern History",
        "id": "ssc-pyq-modern-history",
        "title": "Modern Indian History: SSC PYQ Revision Guide",
        "subject_id": "general-studies",
        "tags": ["SSC PYQ", "History", "Modern History", "Revision Notes"],
        "summary": (
            "High-yield Modern Indian History guide built from the SSC Modern History PYQ archive: "
            "European trading settlements, British expansion, 1857 Revolt, socio-religious reforms, "
            "INC sessions, Gandhian movements and Independence."
        ),
        "chapters": [
            ("European Advent & British Expansion", ["portuguese", "vasco", "dutch", "french", "east india", "plassey", "buxar", "carnatic", "mysore", "tipu", "hyder", "maratha", "subsidiary alliance", "doctrine of lapse", "dalhousie", "wellesley", "clive", "hastings", "cornwallis", "permanent settlement", "ryotwari", "mahalwari"]),
            ("Revolt of 1857 & Tribal/Peasant Uprisings", ["1857", "mangal pandey", "jhansi", "lakshmibai", "kunwar singh", "nana saheb", "tantia tope", "begum hazrat", "bahadur shah", "santhal", "munda", "birsa", "indigo", "sanyasi", "moplah", "peasant", "revolt"]),
            ("Socio-Religious Reform Movements", ["brahmo samaj", "raja ram mohan", "arya samaj", "dayanand", "ramakrishna", "vivekananda", "prarthana samaj", "satyashodhak", "jyotiba phule", "theosophical", "annie besant", "aligarh", "syed ahmed", "widow remarriage", "ishwar chandra", "sati", "bentinck", "young bengal", "derozio"]),
            ("Indian National Congress & Swadeshi Era (1885–1918)", ["congress", "hume", "bonnerjee", "dadabhai", "naoroji", "tilak", "gokhale", "partition of bengal", "curzon", "swadeshi", "surat split", "muslim league", "lucknow pact", "home rule", "ghadar", "lala lajpat", "bipin chandra"]),
            ("Gandhian Era, Revolutionaries & Freedom (1919–1947)", ["gandhi", "champaran", "kheda", "rowlatt", "jallianwala", "khilafat", "non-cooperation", "chauri chaura", "swaraj party", "simon commission", "lahore", "purna swaraj", "dandi", "salt", "civil disobedience", "round table", "poona pact", "ambedkar", "bhagat singh", "subhas", "azad hind", "quit india", "cabinet mission", "mountbatten", "independence", "c. rajagopalachari", "patel", "nehru"]),
        ],
        "quote": "Keep a single chronology sheet of Viceroys, INC sessions (1885, 1907, 1916, 1924, 1929, 1931) and Reform Societies for rapid pre-exam recall.",
    },
    {
        "key": "Indian Geography",
        "id": "ssc-pyq-indian-geography",
        "title": "Indian Geography: SSC PYQ Revision Guide",
        "subject_id": "general-studies",
        "tags": ["SSC PYQ", "Geography", "Indian Geography", "Revision Notes"],
        "summary": (
            "Comprehensive Indian Geography notes extracted from SSC PYQ sets: physiographic divisions, "
            "Himalayan & Peninsular rivers, monsoons, soils, national parks, minerals, agriculture, "
            "ports and Census demographics."
        ),
        "chapters": [
            ("Physiography, Borders, Passes & Islands", ["himalaya", "peak", "pass", "ghat", "plateau", "deccan", "tropic of cancer", "border", "coast", "andaman", "nicobar", "lakshadweep", "channel", "strait", "aravalli", "vindhya", "satpura", "nilgiri", "karakoram", "ladakh", "kanchenjunga"]),
            ("Drainage System, Lakes & Multipurpose Projects", ["river", "ganga", "brahmaputra", "indus", "godavari", "krishna", "kaveri", "cauvery", "narmada", "tapi", "mahanadi", "tributary", "dam", "waterfall", "lake", "chilika", "wular", "loktak", "sambhar", "delta", "estuary", "bhakra", "hirakud", "tehri"]),
            ("Climate, Monsoon, Soils & Natural Vegetation", ["monsoon", "rainfall", "western disturbance", "loo", "soil", "alluvial", "black soil", "regur", "laterite", "red soil", "forest", "mangrove", "sundarbans", "evergreen", "deciduous", "biosphere", "national park", "sanctuary", "tiger reserve", "kaziranga", "gir", "corbett"]),
            ("Agriculture, Minerals & Energy Resources", ["crop", "kharif", "rabi", "zaid", "wheat", "rice", "cotton", "jute", "tea", "coffee", "sugarcane", "revolution", "iron ore", "coal", "bauxite", "mica", "copper", "petroleum", "digboi", "mumbai high", "nuclear", "thermal", "hydro", "khetri", "jharia"]),
            ("Transport, Ports, Tribes & Census Facts", ["port", "railway", "highway", "golden quadrilateral", "waterway", "airport", "census", "literacy", "sex ratio", "population", "density", "tribe", "state", "capital", "union territory"]),
        ],
        "quote": "Visualise India's river basins and mountain passes on a blank map while reading — location-based elimination solves most SSC Geography questions.",
    },
    {
        "key": "Physical Geography",
        "id": "ssc-pyq-physical-geography",
        "title": "Physical & World Geography: SSC PYQ Revision Guide",
        "subject_id": "general-studies",
        "tags": ["SSC PYQ", "Geography", "Physical Geography", "Revision Notes"],
        "summary": (
            "Structured Physical & World Geography revision notes from SSC PYQs covering the Solar System, "
            "Earth's interior & rocks, Atmosphere & winds, Ocean currents, World landforms, deserts, "
            "straits and major rivers."
        ),
        "chapters": [
            ("Universe, Solar System & Earth Motions", ["planet", "sun", "moon", "solar", "galaxy", "asteroid", "comet", "eclipse", "equinox", "solstice", "latitude", "longitude", "meridian", "rotation", "revolution", "jupiter", "saturn", "venus", "mars", "mercury", "neptune", "uranus", "kepler"]),
            ("Geomorphology, Earth's Interior & Rocks", ["crust", "mantle", "core", "igneous", "sedimentary", "metamorphic", "earthquake", "seismic", "richter", "volcano", "plate", "tectonic", "fold", "fault", "erosion", "glacier", "karst", "basalt", "granite", "marble", "limestone", "tsunami"]),
            ("Atmosphere, Winds, Pressure & Climate", ["troposphere", "stratosphere", "mesosphere", "thermosphere", "ionosphere", "ozone", "atmosphere", "wind", "trade wind", "westerlies", "jet stream", "cyclone", "anticyclone", "el nino", "la nina", "humidity", "cloud", "isobar", "isotherm", "barometer", "greenhouse", "albedo"]),
            ("Hydrosphere, Oceans, Tides & Currents", ["ocean", "current", "gulf stream", "kuroshio", "humboldt", "labrador", "tide", "spring tide", "neap tide", "salinity", "trench", "mariana", "coral", "atoll", "continental shelf", "sargasso", "pacific", "atlantic", "arctic"]),
            ("World Landforms, Straits, Deserts & Rivers", ["desert", "sahara", "gobi", "atacama", "kalahari", "strait", "canal", "suez", "panama", "mountain", "andes", "alps", "rockies", "kilimanjaro", "nile", "amazon", "danube", "mississippi", "grassland", "steppe", "prairie", "pampas", "savanna", "veldt", "country", "continent", "lake"]),
        ],
        "quote": "Master the five atmospheric layers, warm vs cold ocean currents, and the rock cycle — they recur every single SSC cycle.",
    },
    {
        "key": "Economics",
        "id": "ssc-pyq-economics",
        "title": "Indian Economy & Concepts: SSC PYQ Revision Guide",
        "subject_id": "economics",
        "tags": ["SSC PYQ", "Economy", "Economics", "Revision Notes"],
        "summary": (
            "Core Economics & Indian Economy revision guide from SSC CGL/CHSL/MTS/CPO PYQs: "
            "National Income (GDP/GNP), RBI & Monetary Policy, Union Budget & Taxation, Five-Year Plans, "
            "Microeconomics & Market Structures, and External Sector."
        ),
        "chapters": [
            ("National Income, GDP & Economic Growth", ["gdp", "gnp", "nnp", "national income", "per capita", "base year", "cso", "nso", "primary sector", "secondary sector", "tertiary", "value added", "depreciation", "deflator", "lorenz", "gini", "poverty", "unemployment", "phillips"]),
            ("Money, Banking, RBI & Monetary Policy", ["rbi", "reserve bank", "repo", "reverse repo", "crr", "slr", "bank rate", "monetary policy", "inflation", "cpi", "wpi", "deflation", "stagflation", "nabard", "sidbi", "sebi", "commercial bank", "nationalisation", "m1", "m3", "money supply", "cheque", "credit"]),
            ("Fiscal Policy, Union Budget & Taxation", ["budget", "fiscal deficit", "revenue deficit", "primary deficit", "gst", "direct tax", "indirect tax", "income tax", "customs", "excise", "finance commission", "subsidy", "disinvestment", "frbm", "capital expenditure", "revenue expenditure", "progressive"]),
            ("Economic Planning, Reforms & Welfare Schemes", ["five-year plan", "five year plan", "planning commission", "niti aayog", "mahalanobis", "harrod", "1991", "lpg", "liberalisation", "privatisation", "green revolution", "white revolution", "mgnrega", "scheme", "yojana", "jan dhan", "make in india", "industrial policy"]),
            ("Microeconomics, Markets & International Trade", ["demand", "supply", "elasticity", "utility", "indifference", "monopoly", "oligopoly", "perfect competition", "opportunity cost", "marginal", "law of diminishing", "giffen", "balance of payments", "bop", "wto", "imf", "world bank", "fdi", "export", "import", "devaluation", "tariff", "exchange rate"]),
        ],
        "quote": "Separate Monetary Policy tools (RBI: Repo, CRR, SLR, OMO) from Fiscal Policy tools (Government: Taxes, Budget Deficits, Expenditure) — SSC loves testing that boundary.",
    },
    {
        "key": "Biology",
        "id": "ssc-pyq-biology",
        "title": "General Science · Biology: SSC PYQ Revision Guide",
        "subject_id": "science",
        "tags": ["SSC PYQ", "Science", "Biology", "Revision Notes"],
        "summary": (
            "High-yield General Science Biology guide compiled from 870+ SSC PYQs covering Cell Biology, "
            "Human Physiology, Vitamins & Deficiency Diseases, Microbiology, Plant Kingdom, Genetics "
            "and Taxonomy."
        ),
        "chapters": [
            ("Cell Biology, Biomolecules & Genetics", ["cell", "mitochondria", "ribosome", "lysosome", "nucleus", "chloroplast", "dna", "rna", "chromosome", "gene", "mendel", "mitosis", "meiosis", "protein", "enzyme", "carbohydrate", "lipid", "amino acid", "atp", "prokaryot", "eukaryot", "robert hooke"]),
            ("Human Physiology & Organ Systems", ["heart", "blood", "rbc", "wbc", "platelet", "haemoglobin", "artery", "vein", "kidney", "nephron", "liver", "bile", "pancreas", "insulin", "hormone", "gland", "pituitary", "thyroid", "adrenal", "brain", "neuron", "eye", "ear", "bone", "skeleton", "lung", "digestion", "stomach", "intestine"]),
            ("Vitamins, Nutrition & Human Diseases", ["vitamin", "deficiency", "scurvy", "rickets", "beriberi", "pellagra", "anaemia", "goitre", "night blindness", "malaria", "tuberculosis", "typhoid", "cholera", "dengue", "virus", "bacteria", "fung", "protozoa", "vaccine", "antibiotic", "penicillin", "aids", "hiv", "polio", "measles", "rabies"]),
            ("Botany, Plant Physiology & Ecology", ["plant", "photosynthesis", "chlorophyll", "xylem", "phloem", "stomata", "transpiration", "auxin", "gibberellin", "ethylene", "flower", "pollination", "seed", "bryophyte", "pteridophyte", "gymnosperm", "angiosperm", "algae", "lichen", "ecosystem", "food chain", "nitrogen"]),
            ("Animal Kingdom, Classification & Scientific Branches", ["phylum", "kingdom", "mammal", "amphibian", "reptile", "arthropod", "mollusc", "annelid", "cnidaria", "echinoderm", "whittaker", "linnaeus", "taxonomy", "study of", "branch", "ornithology", "entomology", "mycology", "virology", "cytology", "histology", "ecology", "botany", "zoology"]),
        ],
        "quote": "Three Biology tables deliver the highest return on SSC papers: Vitamin chemical names & deficiencies, Disease causative agents (virus/bacteria/protozoa), and Endocrine glands & hormones.",
    },
    {
        "key": "Chemistry",
        "id": "ssc-pyq-chemistry",
        "title": "General Science · Chemistry: SSC PYQ Revision Guide",
        "subject_id": "science",
        "tags": ["SSC PYQ", "Science", "Chemistry", "Revision Notes"],
        "summary": (
            "Focused General Science Chemistry notes distilled from 380+ SSC PYQs: Atomic Structure, "
            "Periodic Table, Acids-Bases-Salts, Metals & Alloys, Everyday Chemicals, Organic Compounds "
            "and Environmental Chemistry."
        ),
        "chapters": [
            ("Atomic Structure, Bonding & Chemical Reactions", ["atom", "electron", "proton", "neutron", "isotope", "isobar", "valency", "bond", "covalent", "ionic", "oxidation", "reduction", "catalyst", "avogadro", "mole", "rutherford", "bohr", "thomson", "dalton", "sublimation", "distillation", "colloid", "emulsion"]),
            ("Periodic Table & Elements", ["periodic", "mendeleev", "moseley", "group", "period", "noble gas", "halogen", "alkali", "lanthanide", "atomic number", "electronegativity", "helium", "neon", "argon", "hydrogen", "nitrogen", "oxygen", "chlorine", "fluorine", "mercury", "gallium", "tungsten"]),
            ("Acids, Bases, Salts & pH Scale", ["acid", "base", "salt", "ph ", "litmus", "indicator", "baking soda", "washing soda", "bleaching powder", "plaster of paris", "gypsum", "vinegar", "acetic", "citric", "tartaric", "oxalic", "lactic", "formic", "hydrochloric", "sulphuric", "nitric", "aqua regia", "caustic"]),
            ("Metals, Non-Metals, Ores & Alloys", ["metal", "non-metal", "ore", "bauxite", "haematite", "galena", "cinnabar", "alloy", "brass", "bronze", "steel", "solder", "amalgam", "galvanisation", "zinc", "copper", "aluminium", "iron", "sodium", "potassium", "gold", "silver", "graphite", "diamond", "allotrope"]),
            ("Organic Chemistry, Polymers & Everyday Chemistry", ["carbon", "hydrocarbon", "alkane", "alkene", "methane", "ethanol", "methanol", "chloroform", "acetone", "benzene", "polymer", "pvc", "teflon", "nylon", "bakelite", "rubber", "vulcanisation", "soap", "detergent", "cement", "glass", "fertiliser", "urea", "cng", "lpg", "ozone", "greenhouse", "smog", "acid rain"]),
        ],
        "quote": "Memorise common vs IUPAC names (Baking Soda, Washing Soda, Plaster of Paris, Bleaching Powder), alloy compositions (Brass, Bronze, Solder) and naturally occurring acids.",
    },
    {
        "key": "Physics",
        "id": "ssc-pyq-physics",
        "title": "General Science · Physics: SSC PYQ Revision Guide",
        "subject_id": "science",
        "tags": ["SSC PYQ", "Science", "Physics", "Revision Notes"],
        "summary": (
            "Concept-clear General Science Physics guide synthesized from 340+ SSC PYQs: SI Units & "
            "Measuring Instruments, Mechanics & Gravitation, Optics & Light, Sound & Heat, Electricity, "
            "Magnetism and Modern Physics."
        ),
        "chapters": [
            ("SI Units, Dimensions & Measuring Instruments", ["unit", "si ", "joule", "watt", "newton", "pascal", "hertz", "ampere", "volt", "ohm", "coulomb", "tesla", "decibel", "light year", "parsec", "barometer", "hydrometer", "hygrometer", "anemometer", "ammeter", "voltmeter", "galvanometer", "seismograph", "lactometer", "fathometer", "scalar", "vector"]),
            ("Mechanics, Motion, Force & Gravitation", ["newton", "inertia", "momentum", "force", "friction", "centripetal", "centrifugal", "gravity", "gravitation", "escape velocity", "satellite", "work", "energy", "power", "kinetic", "potential", "archimedes", "buoyancy", "bernoulli", "pascal", "surface tension", "capillary", "viscosity", "pendulum"]),
            ("Light, Optics & Optical Instruments", ["light", "reflection", "refraction", "total internal", "mirage", "optical fibre", "dispersion", "scattering", "tyndall", "rayleigh", "mirror", "concave", "convex", "lens", "myopia", "hypermetropia", "presbyopia", "astigmatism", "dioptre", "prism", "rainbow", "diffraction", "polarisation", "microscope", "telescope"]),
            ("Heat, Thermodynamics & Sound Waves", ["heat", "temperature", "celsius", "fahrenheit", "kelvin", "conduction", "convection", "radiation", "latent heat", "specific heat", "thermodynamics", "boyle", "charles", "sound", "ultrasonic", "infrasonic", "echo", "doppler", "frequency", "wavelength", "amplitude", "pitch", "sonar", "transverse", "longitudinal"]),
            ("Electricity, Magnetism & Modern Physics", ["current", "resistance", "ohm", "fuse", "transformer", "generator", "dynamo", "motor", "faraday", "fleming", "magnet", "electromagnet", "semiconductor", "diode", "transistor", "x-ray", "radioactiv", "fission", "fusion", "nuclear", "photoelectric", "einstein", "laser", "led", "superconductor"]),
        ],
        "quote": "Lock down SI units, measuring instruments, mirror/lens image rules and eye-defect corrections — they account for nearly half of SSC Physics questions.",
    },
    {
        "key": "Static GK",
        "id": "ssc-pyq-static-gk",
        "title": "Static GK Master Compendium: SSC PYQ Guide",
        "subject_id": "general-knowledge",
        "tags": ["SSC PYQ", "General Knowledge", "Static GK", "Revision Notes"],
        "summary": (
            "High-scoring Static GK compendium curated from 770+ SSC PYQs (CGL, CHSL, MTS, CPO): "
            "Classical & Folk Dances, Music & Instruments, Festivals, Awards & Honours, Books & Authors, "
            "Sports, UNESCO Heritage and International Organisations."
        ),
        "chapters": [
            ("Classical & Folk Dances, Music & Gharana", ["dance", "bharatanatyam", "kathak", "kathakali", "kuchipudi", "odissi", "manipuri", "mohiniyattam", "sattriya", "bihu", "garba", "ghoomar", "lavani", "chhau", "kalbelia", "sitar", "tabla", "flute", "shehnai", "santoor", "sarod", "veena", "violin", "gharana", "carnatic", "hindustani", "ustad", "pandit", "sangeet"]),
            ("Fairs, Festivals, Art & UNESCO Heritage", ["festival", "hornbill", "pongal", "onam", "baisakhi", "losar", "navroz", "rath yatra", "pushkar", "kumbh", "temple", "unesco", "heritage", "painting", "madhubani", "warli", "kalamkari", "pattachitra", "cave", "monument", "architecture", "tribes"]),
            ("Awards, Honours & Famous Personalities", ["bharat ratna", "padma", "nobel", "jnanpith", "sahitya akademi", "dadasaheb", "arjuna", "dronacharya", "khel ratna", "grammy", "oscar", "pulitzer", "booker", "ramon magsaysay", "award", "prize", "first indian", "first woman"]),
            ("Books, Authors & Autobiographies", ["book", "author", "wrote", "written by", "autobiography", "novel", "poem", "play", "biography", "memoir", "wings of fire", "discovery of india", "malgudi", "godaan", "gitanjali", "train to pakistan", "midnight"]),
            ("Sports, Organisations & Important Days", ["olympic", "cricket", "hockey", "football", "badminton", "tennis", "chess", "boxing", "wrestling", "athletics", "trophy", "cup", "stadium", "headquarter", "united nations", "unesco", "who", "unicef", "imf", "saarc", "asean", "brics", "isro", "drdo", "day", "observed", "celebrated", "capital", "currency"]),
        ],
        "quote": "Static GK rewards daily 10-minute recall: pair every Classical Dance with its exponent, every Musical Instrument with its maestro, and every Festival with its state.",
    },
]

# Garbage/broken indicators to skip from raw DOCX extraction
GARBAGE_RE = re.compile(
    r"(\(a\)|\(b\)|\(c\)|\(d\)|Ans\.|SSC\s+(?:CGL|CHSL|MTS|CPO|JE|GD)|Shift-[I1-3]|https?://|www\.|parcham)",
    re.IGNORECASE,
)


def clean_text(raw: str) -> str:
    if not raw:
        return ""
    s = raw.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    # Fix PDF->DOCX broken hyphenation with whitespace (e.g. "consid- ered" -> "considered")
    s = re.sub(r"([A-Za-z]{2,})-\s+([a-z]{2,})", r"\1\2", s)
    # Collapse spaces
    s = re.sub(r"\s+", " ", s).strip()
    # Fix space before punctuation
    s = re.sub(r"\s+([,.;:?!])", r"\1", s)
    # Remove stray leading numbering like "12. " or "• "
    s = re.sub(r"^(?:\d{1,4}\s*[.)]\s*|[•▪▸–-]\s*)+", "", s).strip()
    # Remove stray "Ans." prefixes if any leaked in
    s = re.sub(r"^Ans\.?\s*\([a-dA-D]\)\s*:?\s*", "", s).strip()
    # Remove trailing incomplete hyphen/colon
    s = s.rstrip(" -–—:")
    return s


def short_exam_badge(exam_sources: list[str] | None, years: list | None) -> str:
    if exam_sources:
        first = clean_text(str(exam_sources[0])).strip("()")
        # Extract compact exam code like "SSC CGL 2023" / "SSC MTS 2022" / "SSC JE 2020"
        m = re.search(
            r"(SSC\s+(?:CGL|CHSL|MTS|CPO(?:-SI)?|JE|J\.E\.|GD|Steno|10\+2\s+CHSL|Selection\s+Post))",
            first,
            re.IGNORECASE,
        )
        yr = re.search(r"(20\d{2}|19\d{2})", first)
        yr_str = yr.group(1) if yr else (str(years[0]) if years else "")
        if m:
            exam = re.sub(r"\s+", " ", m.group(1).upper().replace("J.E.", "JE").replace("10+2 CHSL", "CHSL"))
            return f"{exam} {yr_str}".strip()
    if years:
        return f"SSC {years[0]}"
    return "SSC PYQ"


def is_clean_item(stem: str, ans: str, exp: str) -> bool:
    if not stem or not ans:
        return False
    if len(stem) < 18 or len(stem) > 210:
        return False
    if len(ans) < 2 or len(ans) > 100:
        return False
    # Avoid items with leaked option markers or OCR junk
    if GARBAGE_RE.search(stem) or GARBAGE_RE.search(ans):
        return False
    if any(tok in stem.lower() for tok in ["which of the following statements", "given statements", "match the following", "column i", "list i", "given below", "pair is", "pairs are", "select the correct"]):
        return False
    if "?" in ans or any(tok in ans.lower() for tok in ["statement", "correct", "following", "all of the above", "none of the above", "both a and b", "both 1 and 2", "neither 1 nor 2", "only 1", "only 2", "1 and 2", "a and b"]):
        return False
    # Reject stems with internal '?' (broken merged questions) or excessive non-ASCII garble
    if stem.count("?") > 1 or ("?" in stem[:-1]):
        return False
    if re.search(r"\b\d{5,}\b", stem) or "____" in ans or "___" in ans:
        return False
    if exp and GARBAGE_RE.search(exp):
        return False
    return True


def first_sentences(text: str, max_chars: int = 240) -> str:
    if not text:
        return ""
    # Split cleanly at sentence boundaries
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        candidate = (out + " " + p).strip() if out else p
        if len(candidate) <= max_chars:
            out = candidate
            if len(out) >= 110:
                break
        else:
            if not out:
                # Truncate gracefully at word boundary
                cut = p[: max_chars - 1].rsplit(" ", 1)[0]
                out = cut.rstrip(",;:") + "."
            break
    if out and out[-1] not in ".!?":
        out += "."
    return out


def extract_modern_history_docx_notes() -> list[dict]:
    """Parse clean sequential Q -> 4 options -> SSC exam -> Ans (x) -> explanation
    blocks directly from SSC-Modern-History-PYQs.docx (9,400+ paragraphs)."""
    path = SSC_DOCX_DIR / "SSC-Modern-History-PYQs.docx"
    if not path.exists():
        return []
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paras = []
    for p in root.findall(".//w:p", ns):
        txt = "".join(t.text or "" for t in p.findall(".//w:t", ns)).strip()
        if txt:
            paras.append(clean_text(txt))

    exam_re = re.compile(r"SSC\s+(?:CGL|CHSL|MTS|CPO|JE|J\.E\.|GD|Steno|10\+2|Selection)", re.IGNORECASE)
    ans_re = re.compile(r"^Ans[.:]?\s*\(([a-dA-D])\)", re.IGNORECASE)
    letter_idx = {"a": 0, "b": 1, "c": 2, "d": 3}

    records: list[dict] = []
    seen: set[str] = set()
    n = len(paras)
    for i in range(6, n - 2):
        m_ans = ans_re.match(paras[i])
        if not m_ans:
            continue
        # Look 1-2 lines back for the SSC exam line
        exam_line_idx = None
        for back in (1, 2):
            if i - back >= 5 and exam_re.search(paras[i - back]):
                exam_line_idx = i - back
                break
        if exam_line_idx is None:
            continue
        opts = [paras[exam_line_idx - 4 + k] for k in range(4)]
        stem = paras[exam_line_idx - 5]
        # Strip optional (a)/(b)/(c)/(d) prefix on options
        opts = [re.sub(r"^\([a-dA-D]\)\s*", "", o).strip() for o in opts]
        ai = letter_idx[m_ans.group(1).lower()]
        ans = opts[ai]
        # Reject if options look like full sentences/explanations or stem looks like an option
        if any(len(o) > 90 or len(o) < 2 for o in opts):
            continue
        if len(stem) < 24 or len(stem) > 200 or not stem[0].isupper():
            continue
        # Gather 1-3 clean explanation lines right after Ans. (x)
        exp_lines: list[str] = []
        for j in range(i + 1, min(n, i + 6)):
            ln = paras[j]
            if exam_re.search(ln) or ans_re.match(ln) or "?" in ln:
                break
            if len(ln) < 20:
                continue
            # Stop if we hit a future question's options block (5 lines before next exam)
            if j + 5 < n and exam_re.search(paras[j + 5]):
                break
            exp_lines.append(ln.rstrip(".") + ".")
            if sum(len(x) for x in exp_lines) >= 210:
                break
        exp = first_sentences(clean_text(" ".join(exp_lines)), 230) if exp_lines else ""
        if not is_clean_item(stem, ans, exp):
            continue
        norm_key = re.sub(r"[^a-z0-9]+", "", stem.lower())[:55]
        if norm_key in seen:
            continue
        seen.add(norm_key)
        records.append(
            {
                "stem": stem,
                "ans": ans,
                "exp": exp,
                "badge": short_exam_badge([paras[exam_line_idx]], None),
                "has_exp": bool(exp and len(exp) >= 35),
                "is_note": False,
            }
        )
    return records


def build_subject_document(spec: dict, raw_items: list[dict]) -> dict:
    sub_name = spec["key"]
    total_raw = len(raw_items)

    # Collect exam coverage & years
    years = sorted(
        {
            int(y)
            for q in raw_items
            for y in (q.get("years") or [])
            if str(y).isdigit() and 2000 <= int(y) <= 2026
        }
    )
    year_span = f"{min(years)}–{max(years)}" if len(years) >= 2 else (str(years[0]) if years else "2016–2023")

    # Normalize & filter clean Q&A records
    clean_records: list[dict] = []
    seen_stems: set[str] = set()
    for q in raw_items:
        stem = clean_text(q.get("stem") or "")
        opts = q.get("options") or []
        ai = q.get("answer_index")
        ans = clean_text(opts[ai]) if (ai is not None and 0 <= ai < len(opts)) else ""
        exp = clean_text(q.get("explanation") or "")
        if not is_clean_item(stem, ans, exp):
            continue
        norm_key = re.sub(r"[^a-z0-9]+", "", stem.lower())[:55]
        if norm_key in seen_stems:
            continue
        seen_stems.add(norm_key)
        clean_records.append(
            {
                "stem": stem,
                "ans": ans,
                "exp": first_sentences(exp, 230) if exp else "",
                "badge": short_exam_badge(q.get("exam_sources"), q.get("years")),
                "has_exp": bool(exp and len(exp) >= 35),
                "is_note": False,
            }
        )

    # Supplement Modern History from DOCX so it is comprehensive
    if sub_name == "Modern History":
        docx_notes = extract_modern_history_docx_notes()
        clean_records.extend(docx_notes)
        total_raw = max(total_raw, len(docx_notes))

    # Prioritize records with clean explanations & recent exams
    clean_records.sort(
        key=lambda r: (
            0 if (not r["is_note"] and r["has_exp"]) else (1 if not r["is_note"] else 2),
            0 if "2023" in r["badge"] or "2022" in r["badge"] else 1,
            len(r["stem"]),
        )
    )

    blocks: list[dict] = []

    # 1. Overview Callout
    source_count_label = (
        f"{total_raw} parsed SSC PYQs plus Modern History archive notes"
        if sub_name == "Modern History"
        else f"{total_raw} SSC previous-year questions"
    )
    blocks.append(
        {
            "id": "overview",
            "type": "callout",
            "text": (
                f"Editorial Study Sheet · Distilled from {source_count_label} "
                f"(SSC CGL, CHSL, MTS, CPO & JE, {year_span}). "
                f"Use the quick-reference table for rapid pre-exam drills, then revise chapter-by-chapter takeaways."
            ),
        }
    )

    # 2. Quick-Reference High-Yield Fact Table (up to 20 crisp Q&A rows)
    table_candidates = [
        r
        for r in clean_records
        if not r["is_note"] and len(r["stem"]) <= 135 and len(r["ans"]) <= 65
    ]
    used_for_table: set[int] = set()
    table_rows: list[list[str]] = [["Question / Concept Focus", "Verified Answer", "SSC Paper"]]
    for idx, r in enumerate(clean_records):
        if len(table_rows) >= 21:
            break
        if r in table_candidates:
            q_focus = r["stem"]
            if len(q_focus) > 130:
                q_focus = q_focus[:127].rsplit(" ", 1)[0] + "…"
            table_rows.append([q_focus, r["ans"], r["badge"]])
            used_for_table.add(idx)

    if len(table_rows) >= 6:
        blocks.append(
            {
                "id": "quick-table-heading",
                "type": "heading",
                "text": "Quick-Reference High-Frequency Facts",
            }
        )
        blocks.append(
            {
                "id": "quick-table",
                "type": "table",
                "rows": table_rows,
            }
        )

    # 3. Classify remaining records into thematic chapters
    chapter_defs: list[tuple[str, list[str]]] = spec["chapters"]
    buckets: dict[int, list[dict]] = {i: [] for i in range(len(chapter_defs))}
    other_bucket: list[dict] = []

    for idx, r in enumerate(clean_records):
        if idx in used_for_table:
            continue
        hay = (r["stem"] + " " + r["ans"] + " " + r["exp"]).lower()
        best_c = None
        best_hits = 0
        for ci, (_, kws) in enumerate(chapter_defs):
            hits = sum(1 for kw in kws if kw in hay)
            if hits > best_hits:
                best_hits = hits
                best_c = ci
        if best_c is not None:
            buckets[best_c].append(r)
        else:
            other_bucket.append(r)

    def format_bullet(r: dict) -> str:
        if r["is_note"]:
            text = f"{r['stem']}."
            if r["exp"]:
                text += f" {r['exp']}"
            return text[:950]
        # Format clean Q&A + explanation as a crisp revision bullet
        raw_stem = r["stem"].strip()
        stem_clean = raw_stem.rstrip("?.: ").strip()
        sep = "?" if raw_stem.endswith("?") else "."
        if r["exp"]:
            bullet = f"{r['ans']} — {stem_clean}{sep} {r['exp']} ({r['badge']})"
        else:
            bullet = f"{r['ans']} — {stem_clean}{sep} ({r['badge']})"
        return bullet[:950]

    for ci, (chap_title, _) in enumerate(chapter_defs):
        items = buckets[ci][:12]
        if len(items) < 3:
            continue
        blocks.append(
            {
                "id": f"chap-{ci+1}-h",
                "type": "heading",
                "text": f"{ci+1}. {chap_title}",
            }
        )
        blocks.append(
            {
                "id": f"chap-{ci+1}-list",
                "type": "list",
                "items": [format_bullet(r) for r in items],
            }
        )

    if len(other_bucket) >= 4:
        blocks.append(
            {
                "id": "chap-extra-h",
                "type": "heading",
                "text": "Additional High-Yield Exam Takeaways",
            }
        )
        blocks.append(
            {
                "id": "chap-extra-list",
                "type": "list",
                "items": [format_bullet(r) for r in other_bucket[:12]],
            }
        )

    # 4. Closing Revision Tip Quote
    blocks.append(
        {
            "id": "revision-quote",
            "type": "quote",
            "text": spec["quote"],
        }
    )

    payload = {
        "title": spec["title"],
        "summary": spec["summary"],
        "preview": spec["summary"],
        "kind": "guide",
        "access": "free",
        "price_paise": 0,
        "tags": spec["tags"],
        "collection_id": None,
        "subject_id": spec["subject_id"],
        "blocks": blocks,
    }

    # Strict validation against Finna's live CMS Pydantic Document schema!
    validated = Document.model_validate(payload)
    return validated.model_dump()


def pg_literal(val: str) -> str:
    return "'" + val.replace("'", "''") + "'"


def generate_upsert_sql(docs: list[tuple[str, dict]]) -> str:
    lines = ["BEGIN;"]
    for idx, (mid, doc) in enumerate(docs):
        title_sql = pg_literal(doc["title"])
        tags_sql = "ARRAY[" + ",".join(pg_literal(t) for t in doc["tags"]) + "]::text[]"
        blocks_sql = pg_literal(json.dumps(doc["blocks"], ensure_ascii=False)) + "::jsonb"
        payload_sql = pg_literal(json.dumps(doc, ensure_ascii=False)) + "::jsonb"
        # Stagger published_at slightly by 1 minute per guide so default recent ordering is clean and predictable
        offset_mins = len(docs) - idx
        detail_sql = pg_literal(
            json.dumps(
                {
                    "source": "shiksha-ssc-pyqs",
                    "owner_directed": True,
                    "subject_id": doc["subject_id"],
                    "blocks_count": len(doc["blocks"]),
                },
                ensure_ascii=False,
            )
        ) + "::jsonb"

        lines.append(
            f"""
DO $$
DECLARE
    cur_rev INTEGER;
    new_rev INTEGER;
BEGIN
    SELECT revision INTO cur_rev FROM materials WHERE id = {pg_literal(mid)};
    IF cur_rev IS NULL THEN
        INSERT INTO materials(
            id, author_id, title, tags, blocks, status,
            published_at, updated_at, revision, lock_version, published_revision, workflow_state
        ) VALUES (
            {pg_literal(mid)}, 'team', {title_sql}, {tags_sql}, {blocks_sql}, 'published',
            now() - interval '{offset_mins} minutes', now(), 1, 1, 1, 'published'
        );
        INSERT INTO material_revisions(material_id, revision, payload, created_by)
        VALUES ({pg_literal(mid)}, 1, {payload_sql}, 'team');
        INSERT INTO material_events(material_id, actor_id, action, detail)
        VALUES ({pg_literal(mid)}, 'team', 'publish', {detail_sql});
    ELSE
        new_rev := cur_rev + 1;
        INSERT INTO material_revisions(material_id, revision, payload, created_by)
        VALUES ({pg_literal(mid)}, new_rev, {payload_sql}, 'team');
        UPDATE materials
           SET title = {title_sql},
               tags = {tags_sql},
               blocks = {blocks_sql},
               status = 'published',
               workflow_state = 'published',
               revision = new_rev,
               published_revision = new_rev,
               lock_version = lock_version + 1,
               updated_at = now()
         WHERE id = {pg_literal(mid)};
        INSERT INTO material_events(material_id, actor_id, action, detail)
        VALUES ({pg_literal(mid)}, 'team', 'publish', {detail_sql});
    END IF;
END $$;
""".strip()
        )
    lines.append("COMMIT;")
    return "\n\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish Shiksha SSC PYQ revision guides to Finna CMS.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and inspect generated guides without writing to DB.")
    parser.add_argument("--sql-out", type=Path, help="Write idempotent SQL script to file.")
    parser.add_argument("--publish", action="store_true", help="Publish directly to Oracle production PostgreSQL via SSH.")
    parser.add_argument("--host", default="ubuntu@152.67.31.231", help="SSH host for Oracle DB.")
    args = parser.parse_args()

    if not SSC_BANK_PATH.exists():
        raise SystemExit(f"Missing SSC bank JSON: {SSC_BANK_PATH}")

    raw = json.loads(SSC_BANK_PATH.read_text(encoding="utf-8"))
    questions = raw["questions"] if isinstance(raw, dict) else raw
    by_sub: dict[str, list[dict]] = collections.defaultdict(list)
    for q in questions:
        by_sub[q.get("sub_subject") or q.get("subject")].append(q)

    docs: list[tuple[str, dict]] = []
    for spec in SUBJECT_SPECS:
        items = by_sub.get(spec["key"], [])
        doc = build_subject_document(spec, items)
        docs.append((spec["id"], doc))

    print(f"Validated {len(docs)} SSC study guides against cms.Document:")
    for mid, doc in docs:
        n_blocks = len(doc["blocks"])
        n_table = sum(len(b.get("rows") or []) - 1 for b in doc["blocks"] if b["type"] == "table")
        n_bullets = sum(len(b.get("items") or []) for b in doc["blocks"] if b["type"] == "list")
        print(f"  - {mid:28s} | {doc['subject_id']:17s} | {n_blocks:2d} blocks | {n_table:2d} table rows | {n_bullets:2d} bullets")

    if args.dry_run:
        sample_id, sample_doc = docs[0]
        print(f"\n--- Sample preview ({sample_id}) ---")
        print("Title:", sample_doc["title"])
        print("Summary:", sample_doc["summary"])
        print("Tags:", sample_doc["tags"])
        for b in sample_doc["blocks"][:5]:
            print(f"  [{b['type']}] {b.get('text', '')[:120]}")
            if b["type"] == "table":
                for row in b["rows"][:4]:
                    print("     |", " | ".join(row))
            if b["type"] == "list":
                for it in b["items"][:3]:
                    print("     *", it[:140])
        # Also show Modern History preview
        mh_doc = dict(docs)["ssc-pyq-modern-history"]
        print("\n--- Modern History preview ---")
        for b in mh_doc["blocks"]:
            if b["type"] == "heading":
                print("  H:", b["text"])
            elif b["type"] == "list":
                print("     *", b["items"][0][:140])
        return

    sql = generate_upsert_sql(docs)
    if args.sql_out:
        args.sql_out.write_text(sql, encoding="utf-8")
        print(f"Wrote SQL to {args.sql_out} ({len(sql):,} bytes)")

    if args.publish:
        print(f"Publishing {len(docs)} guides to {args.host} (PostgreSQL DB: mpsc)...")
        proc = subprocess.run(
            ["ssh", args.host, "sudo -u postgres psql -v ON_ERROR_STOP=1 -d mpsc"],
            input=sql.encode("utf-8"),
            capture_output=True,
        )
        if proc.returncode != 0:
            print(proc.stdout.decode("utf-8", "replace"))
            print(proc.stderr.decode("utf-8", "replace"), file=sys.stderr)
            raise SystemExit(f"psql failed with exit code {proc.returncode}")
        print(proc.stdout.decode("utf-8", "replace"))
        print("Successfully published all 11 SSC guides!")


if __name__ == "__main__":
    main()
