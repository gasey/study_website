# Pending source-reviewed tagging — Batch 46: Inspector of Statistics & MPE & SS Mathematics (47 items)

Policy: `study-tagging-v1`. **47 existing questions reviewed: 12 retag proposals, 35 keep decisions, 0 tag holds. All 47 remain pending. Zero live changes, submissions or publications.**

## Target Papers & 100% Paper Completion Milestone

This batch achieves 100% source review of the extracted items across two specialized departmental / gazetted Mathematics examination booklets:
1. *Technical Competitive Examinations for Recruitment to Inspector of Statistics under Planning & Programme Implementation Department (February 2017) — Paper-III (Mathematics)* (`Old_Questions/Direct_2014-2018/5.Paper-III (Mathematics).pdf`, `doc_baa7d3e36313750a22acdc00`, 20 MCQs, 100% paper completion).
2. *General Competitive Examination for Recruitment to the Post of Junior Grade of Mizoram Planning, Economic & Statistical Service (December 2025) — Mathematics-I* (`Old_Questions/Direct_2025-2027/Jr. Grade of MPE & SS, Mathematics-I..pdf`, `doc_cceff4af00fc9b8c74f9e2ab`, 27 items, 100% paper completion).

## Single-Booklet Deduplication Status

- **Booklet Status:** Both papers are standalone single-booklet examinations with zero permuted booklet series or duplicate folder ingestions in the repository.

## Misclassification & Inactive Baseline Rectifications

Source inspection identified and cleanly rectified multiple legacy ingestion bugs:
- **Rectification of Inactive 'statistics' Baseline Subject:** Question Q20 in Inspector of Statistics (Binomial distribution mean and variance) was tagged in production under inactive subject `statistics:None`. Rectified to active taxonomy `reasoning-and-aptitude/numerical-ability`.
- **Rectification of 'science' Misclassification:** Question Q11 in Inspector of Statistics (projectile least velocity √(gR)) was misclassified under `science`. Rectified to `mathematics`.
- **Rectification of 'engineering-mechanics' Misclassifications:**
  - Question Q12 in Inspector of Statistics (three coplanar equilibrium forces / Lami's theorem) was misclassified under `engineering-mechanics`. Rectified to active taxonomy `mathematics/geometry/lines-and-angles`.
  - Question Q13 in MPE & SS (simple pendulum equation of motion using Lagrangian formulation) was misclassified under `engineering-mechanics`. Rectified to `mathematics`.
- **Refinement to Active Algebra Subtopics:**
  - Inspector of Statistics Q2 (Descartes' rule of signs) refined to `mathematics/algebra`.
  - MPE & SS Q7 (groups & Lagrange's theorem), Q8 (Euclidean rings & PID), Q9(a) (fields & integral domains), and Q9(b) (field extension tower law) refined to `mathematics/algebra`.
- **Higher Mathematics Scope Confirmation (35 KEEPs):** Verified 35 university-level items under active subject `mathematics` covering Real Analysis (continuity, MVT, uniform convergence), Multivariable Calculus (Taylor's theorem, directional derivatives, partial derivatives), Functional Analysis (equivalence of norms, Hahn-Banach theorem, Hilbert spaces, self-adjoint operators), General Topology (open/closed sets, closure/interior/boundary, Sorgenfrey lower-limit line, countability, product topologies, compactness, path-connectedness), Differential Equations (integrating factor, complete integrals), Vector Calculus, Kinematics, Operations Research (duality, integer programming, Big-M simplex, transportation problem), Numerical Methods (root isolation, Simpson's quadrature), and Calculus of Variations / Canonical Transformations.
- **Fresh Oracle read-only export:** `2026-11-07T20:51:57.493719+00:00`. Readback validation (`2026-11-07T20:58:00.786585+00:00`) confirmed 100% source fingerprint consistency, zero live mutations, and 100% compliance with active taxonomy nodes.

## Before / after table

| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | Q1 (p. 1) | Combinatorics (Surjections / Onto Functions) | `mathematics` | `reasoning-and-aptitude/numerical-ability` | **retag** — Calculates number of surjective mappings from n-element set onto 2-element set (2^n - 2). |
| 2 | Q2 (p. 1) | Polynomial Roots (Descartes' Rule of Signs) | `mathematics` | `mathematics/algebra` | **retag** — Applies Descartes' rule of signs to count positive real roots of x^5 - 6x + 2 = 0. |
| 3 | Q3 (p. 1) | Definite Integrals (Modulus Function) | `mathematics` | `mathematics` | **keep** — Confirms active subject for evaluating piecewise definite integral of |x - 1| from 0 to 2. |
| 4 | Q4 (p. 1) | Partial Derivatives (Laplace's Equation) | `mathematics` | `mathematics` | **keep** — Confirms active subject for evaluating Laplacian ∂²u/∂x² + ∂²u/∂y² of u = log(x² + y²). |
| 5 | Q5 (p. 1) | Coordinate Geometry (Pair of Straight Lines) | `mathematics` | `mathematics/geometry/lines-and-angles` | **retag** — Evaluates angle between pair of intersecting straight lines represented by homogeneous quadratic ax² + 2hxy + by² = 0. |
| 6 | Q6 (p. 2) | Vector Calculus (Divergence of Constant Vectors) | `mathematics` | `mathematics` | **keep** — Confirms active subject for gradient/divergence product rule on constant vectors ∇·(a·b) = 0. |
| 7 | Q7 (p. 2) | 3D Coordinate Geometry (Sphere Radius) | `mathematics` | `mathematics/geometry` | **retag** — Finds radius of general sphere equation x² + y² + z² - 2ux - 2vy - 2wz + d = 0. |
| 8 | Q8 (p. 2) | Differential Equations (Integrating Factor) | `mathematics` | `mathematics` | **keep** — Confirms active subject for finding integrating factor of exact differential equation y dx + x dy = 0. |
| 9 | Q9 (p. 2) | Partial Differential Equations (Complete Integral) | `mathematics` | `mathematics` | **keep** — Confirms active subject for finding complete integral of non-linear first-order PDE p² = zq. |
| 10 | Q10 (p. 2) | Parametric Equations & Kinematics | `mathematics` | `mathematics` | **keep** — Confirms active subject for determining trajectory/path of particle with parametric motion x = a cos t, y = a sin ωt. |
| 11 | Q11 (p. 2) | Classical Mechanics (Projectile Motion) | `science` | `mathematics` | **retag** — Rectifies erroneous 'science' misclassification: evaluates least projection velocity √(gR) for horizontal range R. |
| 12 | Q12 (p. 2) | Statics (Equilibrium & Lami's Theorem) | `engineering-mechanics` | `mathematics/geometry/lines-and-angles` | **retag** — Rectifies erroneous 'engineering-mechanics' misclassification: applies Lami's theorem for three equal coplanar forces in equilibrium (angle 120°). |
| 13 | Q13 (p. 2) | Statics (Centre of Gravity) | `mathematics` | `mathematics` | **keep** — Confirms active subject for centre of gravity of uniform semi-circular lamina (4a / 3π). |
| 14 | Q14 (p. 2) | Operations Research (Linear Programming Duality) | `mathematics` | `mathematics` | **keep** — Confirms active subject for fundamental theorem of duality (equality of objective values at optimality). |
| 15 | Q15 (p. 3) | Operations Research (Integer Programming) | `mathematics` | `mathematics` | **keep** — Confirms active subject for Gomory's cutting plane method generating cut constraints from fractional variables. |
| 16 | Q16 (p. 3) | Operations Research (Simplex Big-M Method) | `mathematics` | `mathematics` | **keep** — Confirms active subject for penalty coefficient -M of artificial variables in maximization LPP. |
| 17 | Q17 (p. 3) | Operations Research (Transportation Problem) | `mathematics` | `mathematics` | **keep** — Confirms active subject for basic feasible allocation condition (m + n - 1) in transportation problem. |
| 18 | Q18 (p. 3) | Numerical Methods (Root Isolation) | `mathematics` | `mathematics` | **keep** — Confirms active subject for applying intermediate value theorem to isolate real root of cos x = 3x - 1. |
| 19 | Q19 (p. 3) | Numerical Analysis (Quadrature Formulas) | `mathematics` | `mathematics` | **keep** — Confirms active subject for Newton-Cotes quadrature formula specialization to Simpson's 1/3rd rule (n = 2). |
| 20 | Q20 (p. 3) | Probability & Statistics (Binomial Distribution) | `statistics` | `reasoning-and-aptitude/numerical-ability` | **retag** — Rectifies inactive 'statistics' baseline: calculates parameters n = 25 and p = 1/5 from mean E[X] = 5 and variance Var[X] = 4. |
| 21 | Q1(a) (p. 1) | Real Analysis (Function Continuity) | `mathematics` | `mathematics` | **keep** — Confirms active subject for epsilon-delta continuity definition and discontinuity analysis at origin. |
| 22 | Q1(b) (p. 1) | Multivariable Analysis (Mean Value Theorem) | `mathematics` | `mathematics` | **keep** — Confirms active subject for partial derivatives existence and Mean Value Theorem in ℝ². |
| 23 | Q2 (p. 1) | Real Analysis (Function Sequences & Uniform Convergence) | `mathematics` | `mathematics` | **keep** — Confirms active subject for pointwise versus uniform convergence of sequence f_n(x) = nx/(1+n²x²). |
| 24 | Q3(b) (p. 1) | Multivariable Calculus (Taylor's Theorem) | `mathematics` | `mathematics` | **keep** — Confirms active subject for two-variable Taylor expansion of sin(xy). |
| 25 | Q3(a) (p. 1) | Multivariable Calculus (Directional Derivative) | `mathematics` | `mathematics` | **keep** — Confirms active subject for directional derivative ∇f · u of multivariable function f(x,y). |
| 26 | Q4(a) (p. 2) | Functional Analysis (Equivalence of Norms) | `mathematics` | `mathematics` | **keep** — Confirms active subject for explicit calculation proving equivalence of l₁ and l₂ norms on ℝ². |
| 27 | Q4(b) (p. 2) | Functional Analysis (Metric Topologies) | `mathematics` | `mathematics` | **keep** — Confirms active subject for proving equivalence of induced metric topologies from equivalent norms. |
| 28 | Q5(b) (p. 2) | Functional Analysis (Hahn-Banach Theorem) | `mathematics` | `mathematics` | **keep** — Confirms active subject for applying Hahn-Banach extension theorem on bounded sequence space l^∞. |
| 29 | Q5(a) (p. 2) | Functional Analysis (Bounded Linear Functional) | `mathematics` | `mathematics` | **keep** — Confirms active subject for proving limit functional on convergent bounded sequences is linear and finding norm. |
| 30 | Q6(a) (p. 2) | Functional Analysis (Hilbert Space & Inner Product) | `mathematics` | `mathematics` | **keep** — Confirms active subject for L²([0,1]) inner product space and completeness properties. |
| 31 | Q6(b) (p. 2) | Functional Analysis (Self-Adjoint Operators) | `mathematics` | `mathematics` | **keep** — Confirms active subject for proving multiplication operator Tf(x) = x f(x) on L²([0,1]) is self-adjoint. |
| 32 | Q7 (p. 2) | Abstract Algebra (Group Theory & Lagrange's Theorem) | `mathematics` | `mathematics/algebra` | **retag** — Refines general subject to active topic: defines group and proves Lagrange's theorem on subgroup order dividing group order. |
| 33 | Q8 (p. 2) | Abstract Algebra (Ring Theory & Euclidean Domains) | `mathematics` | `mathematics/algebra` | **retag** — Refines general subject to active topic: defines Euclidean ring and proves every Euclidean domain is a principal ideal domain (PID). |
| 34 | Q9(b) (p. 2) | Abstract Algebra (Field Theory & Tower Law) | `mathematics` | `mathematics/algebra` | **retag** — Refines general subject to active topic: proves tower law [L:F] = [L:K][K:F] for finite field extensions. |
| 35 | Q9(a) (p. 2) | Abstract Algebra (Field & Integral Domain) | `mathematics` | `mathematics/algebra` | **retag** — Refines general subject to active topic: proves that every field is an integral domain (zero-divisor absence). |
| 36 | Q10(b) (p. 2) | General Topology (Continuous Mapping & Closure) | `mathematics` | `mathematics` | **keep** — Confirms active subject for topological characterization of continuity via closure inclusion f(cl(A)) ⊆ cl(f(A)). |
| 37 | Q10(a)(ii) (p. 2) | General Topology (Open & Closed Sets) | `mathematics` | `mathematics` | **keep** — Confirms active subject for determining topological status (neither open nor closed) of interval union [0,1) ∪ (1,2]. |
| 38 | Q10(a)(i) (p. 2) | General Topology (Closure, Interior, Boundary) | `mathematics` | `mathematics` | **keep** — Confirms active subject for computing closure, interior, and boundary of set in standard Euclidean topology. |
| 39 | Q11(iii) (p. 3) | General Topology (Topology Comparison) | `mathematics` | `mathematics` | **keep** — Confirms active subject for comparing lower limit topology (Sorgenfrey line) with standard Euclidean topology (strictly finer). |
| 40 | Q11(i) (p. 3) | General Topology (Hausdorff Property) | `mathematics` | `mathematics` | **keep** — Confirms active subject for proving lower limit topology satisfies T₂ (Hausdorff) separation axiom. |
| 41 | Q11(ii) (p. 3) | General Topology (Countability Axioms) | `mathematics` | `mathematics` | **keep** — Confirms active subject for determining first and second countability of the Sorgenfrey line. |
| 42 | Q12(iii) (p. 3) | General Topology (Compactness & Connectedness) | `mathematics` | `mathematics` | **keep** — Confirms active subject for compactness, connectedness, and path-connectedness analysis of subspace. |
| 43 | Q12(ii) (p. 3) | General Topology (Path-Connectedness) | `mathematics` | `mathematics` | **keep** — Confirms active subject for proving product space [0,1]² is connected and path-connected. |
| 44 | Q12(i) (p. 3) | General Topology (Product Space Topology) | `mathematics` | `mathematics` | **keep** — Confirms active subject for analyzing product topology on Euclidean subspace. |
| 45 | Q13 (p. 3) | Classical Mechanics (Lagrangian Formulation) | `engineering-mechanics` | `mathematics` | **retag** — Rectifies erroneous 'engineering-mechanics' misclassification: derives simple pendulum equation of motion using Lagrangian formulation. |
| 46 | Q14 (p. 3) | Calculus of Variations (Euler-Lagrange Equation) | `mathematics` | `mathematics` | **keep** — Confirms active subject for using calculus of variations to prove shortest distance between two points on plane is straight line. |
| 47 | Q15 (p. 3) | Classical Mechanics (Canonical Transformation) | `mathematics` | `mathematics` | **keep** — Confirms active subject for proving phase space transformation (q,p) -> (Q,P) is canonical using Poisson brackets. |

## Totals & Summary Breakdown

- **Total existing questions reviewed:** 47
- **Retag candidates proposed:** 12
- **Keep decisions:** 35
- **Holds:** 0
- **Unextracted written items preserved:** 7
- **Conventional marks preserved:** 45
- **Live database writes:** 0 (strictly read-only)

### Breakdown by Proposed Taxonomy Path

- `mathematics`: 37 questions
- `mathematics/algebra`: 5 questions
- `mathematics/geometry`: 1 questions
- `mathematics/geometry/lines-and-angles`: 2 questions
- `reasoning-and-aptitude/numerical-ability`: 2 questions

## Physical Element Inspection Evidence

Direct visual inspection of rendered PNG page images across both papers (8 pages total):
- **Paper 1 (`doc_baa7d3e36313750a22acdc00`):** Inspected Pages 1 to 5. Verified MCQs Q1–Q20 on pages 1–3 (surjection counting, Descartes' signs, definite integral |x-1|, Laplacian of log(x²+y²), pair of straight lines angle, vector divergence, sphere radius, integrating factor, complete PDE integral, parametric kinematics, projectile velocity, coplanar forces equilibrium, semi-circular lamina CG, LPP duality, Gomory cut, Big-M coefficient, transportation feasible allocations, root isolation, Simpson's 1/3rd quadrature, Binomial distribution mean/variance). Preserved conventional descriptive questions 21–35 (80 marks) on pages 4–5 in `pending-written-intake.json`.
- **Paper 2 (`doc_cceff4af00fc9b8c74f9e2ab`):** Inspected Pages 1 to 3. Verified 27 structured items: Page 1 (Q1(a) continuity, Q1(b) MVT in ℝ², Q2 uniform convergence, Q3(b) Taylor expansion, Q3(a) directional derivative); Page 2 (Q4(a) norm equivalence, Q4(b) metric topologies, Q5(b) Hahn-Banach, Q5(a) bounded linear functional, Q6(a) Hilbert space, Q6(b) self-adjoint operator, Q7 group theory, Q8 Euclidean ring, Q9(b) field extensions, Q9(a) integral domain, Q10(b) continuous mapping, Q10(a)(ii) open/closed sets, Q10(a)(i) closure/interior/boundary); Page 3 (Q11(iii) topology comparison, Q11(i) Hausdorff lower limit, Q11(ii) countability, Q12(iii) compactness, Q12(ii) connectedness, Q12(i) product topology, Q13 simple pendulum Lagrangian, Q14 calculus of variations shortest curve, Q15 canonical transformation).

## Documented Source, Extraction & Option Defects

1. **Rectification of Inactive 'statistics' Subject Baseline:** Rectified Paper 1 Q20 from inactive `statistics` to `reasoning-and-aptitude/numerical-ability`.
2. **Rectification of 'science' Subject Baseline:** Rectified Paper 1 Q11 from `science` to `mathematics`.
3. **Rectification of 'engineering-mechanics' Baseline:** Rectified Paper 1 Q12 to `mathematics/geometry/lines-and-angles` and Paper 2 Q13 to `mathematics`.
4. **Preservation of 80 Marks of Conventional Descriptive Problems:** Documented Paper 1 descriptive problems (difference operators, exact differential equations, particle kinematics, friction on inclined planes, simplex method, transportation problem) in `pending-written-intake.json`.
