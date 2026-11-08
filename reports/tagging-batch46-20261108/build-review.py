"""Build review packet and findings for Batch 46: Inspector of Statistics & MPE & SS Mathematics (47 items)."""
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

# Proposals mapped by appearance_id
proposals = {
    # --- PAPER 1: Inspector of Statistics Paper-III (Mathematics) (20 MCQs) ---
    "213d227428ac0f947748": ("Q1", 1, "Combinatorics (Surjections / Onto Functions)", "reasoning-and-aptitude/numerical-ability", "retag", "Calculates number of surjective mappings from n-element set onto 2-element set (2^n - 2)."),
    "80eab07e31f959d5643e": ("Q2", 1, "Polynomial Roots (Descartes' Rule of Signs)", "mathematics/algebra", "retag", "Applies Descartes' rule of signs to count positive real roots of x^5 - 6x + 2 = 0."),
    "23092d9cc4fda055f8de": ("Q3", 1, "Definite Integrals (Modulus Function)", "mathematics", "keep", "Confirms active subject for evaluating piecewise definite integral of |x - 1| from 0 to 2."),
    "94b79c8650f019e05d96": ("Q4", 1, "Partial Derivatives (Laplace's Equation)", "mathematics", "keep", "Confirms active subject for evaluating Laplacian ∂²u/∂x² + ∂²u/∂y² of u = log(x² + y²)."),
    "69c3514868d89ef87746": ("Q5", 1, "Coordinate Geometry (Pair of Straight Lines)", "mathematics/geometry/lines-and-angles", "retag", "Evaluates angle between pair of intersecting straight lines represented by homogeneous quadratic ax² + 2hxy + by² = 0."),
    "38bd8a65b3352e812f33": ("Q6", 2, "Vector Calculus (Divergence of Constant Vectors)", "mathematics", "keep", "Confirms active subject for gradient/divergence product rule on constant vectors ∇·(a·b) = 0."),
    "ff37ae1bb0ea01541f24": ("Q7", 2, "3D Coordinate Geometry (Sphere Radius)", "mathematics/geometry", "retag", "Finds radius of general sphere equation x² + y² + z² - 2ux - 2vy - 2wz + d = 0."),
    "189ead70589a3d203356": ("Q8", 2, "Differential Equations (Integrating Factor)", "mathematics", "keep", "Confirms active subject for finding integrating factor of exact differential equation y dx + x dy = 0."),
    "8521b6f4edc19acbf184": ("Q9", 2, "Partial Differential Equations (Complete Integral)", "mathematics", "keep", "Confirms active subject for finding complete integral of non-linear first-order PDE p² = zq."),
    "4ff341e55847f3f3c9bf": ("Q10", 2, "Parametric Equations & Kinematics", "mathematics", "keep", "Confirms active subject for determining trajectory/path of particle with parametric motion x = a cos t, y = a sin ωt."),
    "d1d19dc9ca5818cda540": ("Q11", 2, "Classical Mechanics (Projectile Motion)", "mathematics", "retag", "Rectifies erroneous 'science' misclassification: evaluates least projection velocity √(gR) for horizontal range R."),
    "b7f1fe71938d9c56975d": ("Q12", 2, "Statics (Equilibrium & Lami's Theorem)", "mathematics/geometry/lines-and-angles", "retag", "Rectifies erroneous 'engineering-mechanics' misclassification: applies Lami's theorem for three equal coplanar forces in equilibrium (angle 120°)."),
    "f1cb0ffd5a8d5290ffba": ("Q13", 2, "Statics (Centre of Gravity)", "mathematics", "keep", "Confirms active subject for centre of gravity of uniform semi-circular lamina (4a / 3π)."),
    "2a3f59dd2d61d27ff6db": ("Q14", 2, "Operations Research (Linear Programming Duality)", "mathematics", "keep", "Confirms active subject for fundamental theorem of duality (equality of objective values at optimality)."),
    "d753fd9390f073d0f14e": ("Q15", 3, "Operations Research (Integer Programming)", "mathematics", "keep", "Confirms active subject for Gomory's cutting plane method generating cut constraints from fractional variables."),
    "cdc4261b47c5b8ebaa77": ("Q16", 3, "Operations Research (Simplex Big-M Method)", "mathematics", "keep", "Confirms active subject for penalty coefficient -M of artificial variables in maximization LPP."),
    "add55e7263189dfbc468": ("Q17", 3, "Operations Research (Transportation Problem)", "mathematics", "keep", "Confirms active subject for basic feasible allocation condition (m + n - 1) in transportation problem."),
    "401934645d48141ea49b": ("Q18", 3, "Numerical Methods (Root Isolation)", "mathematics", "keep", "Confirms active subject for applying intermediate value theorem to isolate real root of cos x = 3x - 1."),
    "7e319b3091b5f6a562eb": ("Q19", 3, "Numerical Analysis (Quadrature Formulas)", "mathematics", "keep", "Confirms active subject for Newton-Cotes quadrature formula specialization to Simpson's 1/3rd rule (n = 2)."),
    "8385604109b3f47f10d5": ("Q20", 3, "Probability & Statistics (Binomial Distribution)", "reasoning-and-aptitude/numerical-ability", "retag", "Rectifies inactive 'statistics' baseline: calculates parameters n = 25 and p = 1/5 from mean E[X] = 5 and variance Var[X] = 4."),

    # --- PAPER 2: Jr. Grade of MPE & SS, Mathematics-I (27 items) ---
    "desc-ef2243ad88a407d45ba8": ("Q1(a)", 1, "Real Analysis (Function Continuity)", "mathematics", "keep", "Confirms active subject for epsilon-delta continuity definition and discontinuity analysis at origin."),
    "desc-b75159ef4f723a33a1a3": ("Q1(b)", 1, "Multivariable Analysis (Mean Value Theorem)", "mathematics", "keep", "Confirms active subject for partial derivatives existence and Mean Value Theorem in ℝ²."),
    "desc-b3edb327a9414b436bb4": ("Q2", 1, "Real Analysis (Function Sequences & Uniform Convergence)", "mathematics", "keep", "Confirms active subject for pointwise versus uniform convergence of sequence f_n(x) = nx/(1+n²x²)."),
    "desc-dfc19799ce4f1240e265": ("Q3(b)", 1, "Multivariable Calculus (Taylor's Theorem)", "mathematics", "keep", "Confirms active subject for two-variable Taylor expansion of sin(xy)."),
    "desc-8b3b3578fc395102e686": ("Q3(a)", 1, "Multivariable Calculus (Directional Derivative)", "mathematics", "keep", "Confirms active subject for directional derivative ∇f · u of multivariable function f(x,y)."),
    "desc-7d741454e284ffec03c1": ("Q4(a)", 2, "Functional Analysis (Equivalence of Norms)", "mathematics", "keep", "Confirms active subject for explicit calculation proving equivalence of l₁ and l₂ norms on ℝ²."),
    "desc-7d829660918fae181a90": ("Q4(b)", 2, "Functional Analysis (Metric Topologies)", "mathematics", "keep", "Confirms active subject for proving equivalence of induced metric topologies from equivalent norms."),
    "desc-a4c14407d49c99aa3e11": ("Q5(b)", 2, "Functional Analysis (Hahn-Banach Theorem)", "mathematics", "keep", "Confirms active subject for applying Hahn-Banach extension theorem on bounded sequence space l^∞."),
    "desc-7f4e7e460d68f1af79ba": ("Q5(a)", 2, "Functional Analysis (Bounded Linear Functional)", "mathematics", "keep", "Confirms active subject for proving limit functional on convergent bounded sequences is linear and finding norm."),
    "desc-a1c886e68ef69aeea68a": ("Q6(a)", 2, "Functional Analysis (Hilbert Space & Inner Product)", "mathematics", "keep", "Confirms active subject for L²([0,1]) inner product space and completeness properties."),
    "desc-af009f80c84405adc2cf": ("Q6(b)", 2, "Functional Analysis (Self-Adjoint Operators)", "mathematics", "keep", "Confirms active subject for proving multiplication operator Tf(x) = x f(x) on L²([0,1]) is self-adjoint."),
    "desc-7b0ff2f75a069d561310": ("Q7", 2, "Abstract Algebra (Group Theory & Lagrange's Theorem)", "mathematics/algebra", "retag", "Refines general subject to active topic: defines group and proves Lagrange's theorem on subgroup order dividing group order."),
    "desc-b9d295e9dc66be645830": ("Q8", 2, "Abstract Algebra (Ring Theory & Euclidean Domains)", "mathematics/algebra", "retag", "Refines general subject to active topic: defines Euclidean ring and proves every Euclidean domain is a principal ideal domain (PID)."),
    "desc-57e9e6d5e6729b71a11d": ("Q9(b)", 2, "Abstract Algebra (Field Theory & Tower Law)", "mathematics/algebra", "retag", "Refines general subject to active topic: proves tower law [L:F] = [L:K][K:F] for finite field extensions."),
    "desc-2004009167b22b8f5d68": ("Q9(a)", 2, "Abstract Algebra (Field & Integral Domain)", "mathematics/algebra", "retag", "Refines general subject to active topic: proves that every field is an integral domain (zero-divisor absence)."),
    "desc-71f1405ce0b69eed7c62": ("Q10(b)", 2, "General Topology (Continuous Mapping & Closure)", "mathematics", "keep", "Confirms active subject for topological characterization of continuity via closure inclusion f(cl(A)) ⊆ cl(f(A))."),
    "desc-f3626f6a90d37bcaa58a": ("Q10(a)(ii)", 2, "General Topology (Open & Closed Sets)", "mathematics", "keep", "Confirms active subject for determining topological status (neither open nor closed) of interval union [0,1) ∪ (1,2]."),
    "desc-435d54bac064833205ac": ("Q10(a)(i)", 2, "General Topology (Closure, Interior, Boundary)", "mathematics", "keep", "Confirms active subject for computing closure, interior, and boundary of set in standard Euclidean topology."),
    "desc-4ea33ec97d8915b7badc": ("Q11(iii)", 3, "General Topology (Topology Comparison)", "mathematics", "keep", "Confirms active subject for comparing lower limit topology (Sorgenfrey line) with standard Euclidean topology (strictly finer)."),
    "desc-24412c42512de5245706": ("Q11(i)", 3, "General Topology (Hausdorff Property)", "mathematics", "keep", "Confirms active subject for proving lower limit topology satisfies T₂ (Hausdorff) separation axiom."),
    "desc-13ae53a67ac585d4645b": ("Q11(ii)", 3, "General Topology (Countability Axioms)", "mathematics", "keep", "Confirms active subject for determining first and second countability of the Sorgenfrey line."),
    "desc-e4c5e3eec1dc49cbdf3a": ("Q12(iii)", 3, "General Topology (Compactness & Connectedness)", "mathematics", "keep", "Confirms active subject for compactness, connectedness, and path-connectedness analysis of subspace."),
    "desc-facfbc02e6163fd237b1": ("Q12(ii)", 3, "General Topology (Path-Connectedness)", "mathematics", "keep", "Confirms active subject for proving product space [0,1]² is connected and path-connected."),
    "desc-56e70ee0171443fdb19e": ("Q12(i)", 3, "General Topology (Product Space Topology)", "mathematics", "keep", "Confirms active subject for analyzing product topology on Euclidean subspace."),
    "desc-d887399a6ed50a50a010": ("Q13", 3, "Classical Mechanics (Lagrangian Formulation)", "mathematics", "retag", "Rectifies erroneous 'engineering-mechanics' misclassification: derives simple pendulum equation of motion using Lagrangian formulation."),
    "desc-7c0870494bad0d439026": ("Q14", 3, "Calculus of Variations (Euler-Lagrange Equation)", "mathematics", "keep", "Confirms active subject for using calculus of variations to prove shortest distance between two points on plane is straight line."),
    "desc-94323692194c92a36f61": ("Q15", 3, "Classical Mechanics (Canonical Transformation)", "mathematics", "keep", "Confirms active subject for proving phase space transformation (q,p) -> (Q,P) is canonical using Poisson brackets.")
}

candidates = []
findings = []
breakdown = {}
action_counts = {"retag": 0, "keep": 0}

for it in packet["items"]:
    aid = it["appearance_id"]
    qn_str, page, skill, path_str, action, rationale = proposals[aid]
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
        "batch_id": 46,
        "policy": "study-tagging-v1"
    }
    candidates.append(cand)
    
    finding = {
        "index": len(candidates),
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "printed_question": qn_str,
        "physical_page": page,
        "tested_skill": skill,
        "current_path": cur_path,
        "proposed_path": prop_path,
        "action": action,
        "rationale": rationale
    }
    findings.append(finding)

assert len(candidates) == 47
assert len(findings) == 47

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Conventional written items for Paper 1 (descriptive section of Inspector of Statistics)
written_intake = [
    {
        "paper_id": "Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf",
        "section": "CONVENTIONAL / DESCRIPTIVE SECTION (80 Marks)",
        "question_number": "26",
        "physical_page": 4,
        "marks": 5,
        "task_type": "finite_differences",
        "prompt": "Show that Δ^n e^x = (e^h - 1)^n e^x, where Δ denotes the forward difference operator.",
        "taxonomy_target": {
            "subject_id": "mathematics",
            "topic_id": None,
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive proof on finite difference operators, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf",
        "section": "CONVENTIONAL / DESCRIPTIVE SECTION (80 Marks)",
        "question_number": "27",
        "physical_page": 4,
        "marks": 5,
        "task_type": "differential_equations_proof",
        "prompt": "Show that the differential equation (1 + e^(x/y)) dx + e^(x/y) (1 - x/y) dy = 0 is exact.",
        "taxonomy_target": {
            "subject_id": "mathematics",
            "topic_id": None,
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional descriptive proof of exactness condition ∂M/∂y = ∂N/∂x, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf",
        "section": "CONVENTIONAL / DESCRIPTIVE SECTION (80 Marks)",
        "question_number": "28",
        "physical_page": 4,
        "marks": 5,
        "task_type": "particle_kinematics",
        "prompt": "If a particle moves so that its normal acceleration is always zero, show that the path is a straight line.",
        "taxonomy_target": {
            "subject_id": "mathematics",
            "topic_id": None,
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional kinematics proof relating normal acceleration v²/ρ = 0 to straight-line curvature, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf",
        "section": "CONVENTIONAL / DESCRIPTIVE SECTION (80 Marks)",
        "question_number": "29",
        "physical_page": 4,
        "marks": 5,
        "task_type": "particle_kinematics",
        "prompt": "If a particle moves in a plane with constant speed, prove that its acceleration is perpendicular to its velocity.",
        "taxonomy_target": {
            "subject_id": "mathematics",
            "topic_id": None,
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional vector calculus proof differentiating v · v = c² to yield v · a = 0, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf",
        "section": "CONVENTIONAL / DESCRIPTIVE SECTION (80 Marks)",
        "question_number": "30",
        "physical_page": 4,
        "marks": 5,
        "task_type": "statics_friction",
        "prompt": "Prove that if a body be on the point of sliding down an inclined plane under its own weight, the inclination of the plane is equal to the angle of friction.",
        "taxonomy_target": {
            "subject_id": "mathematics",
            "topic_id": None,
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional statics proof establishing limiting friction condition tan λ = μ, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf",
        "section": "CONVENTIONAL / DESCRIPTIVE SECTION (80 Marks)",
        "question_number": "35(a)",
        "physical_page": 5,
        "marks": 10,
        "task_type": "simplex_method",
        "prompt": "Using simplex method solve the given LPP: Maximize Z = 5x₁ + 4x₂ + 3x₃ subject to constraints x₁ + 2x₂ + x₃ ≤ 10, 3x₁ + x₂ + 2x₃ ≤ 12, x₁ + 2x₂ + 3x₃ ≤ 15, x₁,x₂,x₃ ≥ 0.",
        "taxonomy_target": {
            "subject_id": "mathematics",
            "topic_id": None,
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional multi-variable simplex tableau calculation, excluded from automated MCQ database ingestion."
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf",
        "section": "CONVENTIONAL / DESCRIPTIVE SECTION (80 Marks)",
        "question_number": "35(b)",
        "physical_page": 5,
        "marks": 10,
        "task_type": "transportation_problem",
        "prompt": "Three factories ship goods to three warehouses with supplies 50, 40, 60 and demands 20, 95, 35. Find initial basic feasible solution using (i) Northwest-corner rule and (ii) Least-cost method.",
        "taxonomy_target": {
            "subject_id": "mathematics",
            "topic_id": None,
            "subtopic_id": None
        },
        "reason_unextracted": "Conventional transportation problem matrix calculations, excluded from automated MCQ database ingestion."
    }
]

(batch_dir / "pending-written-intake.json").write_text(json.dumps(written_intake, indent=2) + "\n")

summary = {
    "batch": 46,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf",
            "paper_title": "Technical Competitive Examinations for Recruitment to Inspector of Statistics (February, 2017) — Paper-III (Mathematics)",
            "document_id": "doc_baa7d3e36313750a22acdc00",
            "sha256": "a3c2ee980e28c7f40199042b1029e1c3e34b17e4f165e31c77f0a1ea3ec6378e",
            "targets": 20
        },
        {
            "paper_id": "Old_Questions/Direct_2025-2027/Jr. Grade of MPE & SS, Mathematics-I..pdf",
            "paper_title": "General Competitive Examination for Recruitment to the Post of Junior Grade of Mizoram Planning, Economic & Statistical Service (December, 2025) — Mathematics-I",
            "document_id": "doc_cceff4af00fc9b8c74f9e2ab",
            "sha256": "f4a4642ab97082928812c8a7c29eec014b21d5a71dfa9d8ae8db80029b35bc52",
            "targets": 27
        }
    ],
    "single_booklet_deduplication": {
        "enforced": True,
        "primary_booklet": "Single booklet examinations for both targets",
        "bypassed_siblings": [],
        "redundant_reviews_saved": 0
    },
    "targets": 47,
    "completion": "100% of extracted items reviewed across both Inspector of Statistics and MPE & SS Mathematics papers",
    "actions": action_counts,
    "unextracted_items_preserved": len(written_intake),
    "conventional_marks_preserved": 45,
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved {len(written_intake)} unextracted conventional items.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
