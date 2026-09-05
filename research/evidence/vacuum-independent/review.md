# Review of the inertial vacuum baseline

Astra review, 2026-09-05. Mathematical checks are supported; formal acceptance is withheld.

The candidate implements the frozen five-gap calculation for an inertial, pointlike, linearly coupled detector in the vacuum of a real massless scalar field in 3+1 flat spacetime. Positive gap means excitation. The reported quantity is the dimensionless leading-order response with coupling and detector matrix-element factors removed, not probability. This is a bounded reproduction, not a black-hole calculation or a new result.

## Mathematical evidence

The inspected plane-wave measure gives `omega d omega / (4 pi^2)`. Applying the negative-sign Fourier convention to the proper-time integrals gives `|chi_hat(E+omega)|^2`. Substitution of `a=E delta` and `q=(E+omega)delta` gives the frozen dimensionless integral. The candidate's stable sinc expansion follows directly from expanding the compact cos^4 switching into three cosines. These conventions agree with [the source paper, equations 2, 6, 9–11, 14–16 and 21](https://arxiv.org/html/2501.06609v2#S3.SS1).

[The saved comparison](candidate-audit.json) passes 75 checks. At gaps -4, -1, 0, 1 and 4, candidate responses are respectively 0.3517447795284938, 0.1337275982191029, 0.08317814081187816, 0.04668973871573702 and 0.003593341515030186. The largest discrepancy from the independent method is 2.267e-12. The candidate source and original result hashes are recorded in that comparison.

The [independent calculation](result.json) used the unchanged upstream ChiFn at Gauss-Legendre time nodes and separate composite Gauss-Legendre frequency integration. It did not import the candidate transform. Its original source, output, stdout/stderr and process receipt remain unchanged. No independent response calculation was repeated for this review.

The saved comparison recomputes both Simpson refinement differences, cutoff doubling, panel counts, tail bounds and Parseval response differences from raw candidate values. All five gaps meet the frozen tolerances. All 30 duration/center combinations agree within T/4. Source inspection confirms that these cases integrate dimensional omega and evaluate the full complex phase. Analytically, the phase has unit modulus; the two powers of delta in the transform cancel the inverse powers from omega and its measure at fixed E delta. This proves the stated scale relation under the model assumptions; it is not invariance when E alone is held fixed.

The candidate's own pole-neighbor check records finiteness; it does not directly compare those neighbors with original ChiFn. This review closes that gap by comparing its saved values at all 19 frozen transform points, including every displaced pole, with the already-preserved independent direct Fourier values at absolute tolerance 1e-10. Exact pole values meet 1e-12. The inspected boundary also passes 40 explicit nonfinite-input and nonpositive-duration rejection cases.

The analytic tail bound is 2.915e-12 at Q=64 and satisfies every T/4 threshold. Its assumptions hold for all five gaps. Quadrature refinements are empirical evidence, not rigorous quadrature error bounds. Nonzero finite-time excitation in vacuum is consistent with the time-varying coupling; these values do not establish thermal equilibrium or Hawking radiation.

## Execution and provenance limits

The frozen full-decision hash is c730771bdfd12f7ec2f48c6f5d20475b105c0b2927fb800a3cfc503ff7ceb3c9. The original frozen bytes predate the numerical outputs. The contract file contains an exact extracted text section with a metadata header; its whole-file digest and excerpt digest intentionally differ.

The retained native candidate run used an externally enforced 60-second timeout, with 0.03563 seconds of numerical work and 0.20129 seconds enclosing process time. The independent run used the same cap and took 0.26211 and 0.43377 seconds respectively. Human preparation/review time and monetary cost are unknown.

The execution protocol was not fully followed during preparation. Direct test invocations performed calculations before the new target export and did not show an external 60-second cap for the whole test process. After the initial missing-module test, two executed test batches failed before the seven-test batch passed; the worker's final description of one correction does not fully describe those two repair stages. Later, the native saved result was produced after export with the required process cap, and 44 research tests passed. Original tool events and failures are retained privately. No thresholds were enlarged, and no additional numerical correction or reproduction is authorized by this review. These limitations cannot be repaired retroactively by rerunning the result.

The original candidate output contains a local machine path. Its complete native store, submission and generated handoff are retained locally without editing those bytes. Public evidence includes the candidate source, independent raw reference and this comparison, which identifies the original candidate result by digest. It is not presented as a public copy of every native artifact.

## Assessment and next action

Use `withhold` for formal acceptance: the store has no registered independent physics checker, and the preparation protocol has the limitations above. The mathematical evidence is narrower than external domain certification. Neither this calculation nor the model handoff proves that structured records outperform an excellent Markdown note or that anyone wants a product.

Generate the local native handoff with this reviewed result and its limits. The next scoped action is the owner's existing usability check: read the result and withheld assessment, open an original-evidence link, and copy the continuation prompt into an empty note. No further physics calculation is part of that check. Rendered visual and operating-system clipboard acceptance remain unverified.
