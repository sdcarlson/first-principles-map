# Bounded review of the detector-switching prerequisite

Review date: 2026-09-05. Reviewer: a separate Astra High model review task, as requested; configuration label is not backend attestation or human/domain certification. Target: `4e3cdbfef39ee58056362fd28c5e6a764be7174ba710f3c9352689c1e06d820a`.

## Decision and limits

The target's elementary mathematical prerequisite is supported: for finite positive half-duration delta, the supplied compact cos^4 switching has the stated support and peak, and both analytic integrals are correct. The inspected existing reproduction reran with 12/12 passing rows identical to the attached numerical rows. This is sufficient to scope a separate flat-spacetime baseline. It is not certification of the detector model, full paper, black-hole calculation, new physics, or FPM benefit. Existing assessment records and formal scientific acceptance are unchanged.

## First-principles calculation

Write u = (tau - tau_mid)/delta. Inside |u| < 1, chi = cos^4(pi u/2); otherwise chi = 0. For delta > 0 its nonzero set is the open interval (tau_mid - delta, tau_mid + delta); its mathematical support is the closure, the corresponding closed interval. The supplied strict inequality sets both endpoints to exactly zero. Since 0 <= cos^4 <= 1 and cos(0) = 1, the peak equals one at tau_mid.

Set x = pi u/2 and J_n = integral from -pi/2 to pi/2 of cos^(2n)(x) dx. Integration by parts gives J_n = ((2n-1)/(2n)) J_(n-1), starting from J_0 = pi. Thus J_2 = 3pi/8 and J_4 = 35pi/128. The Jacobian is d tau = (2delta/pi) dx, so:

- integral chi d tau = (2delta/pi)(3pi/8) = 3delta/4.
- integral chi^2 d tau = (2delta/pi)(35pi/128) = 35delta/64.

These integrals have units of proper time, whereas chi and its peak are dimensionless. Both are independent of tau_mid. Delta is a half-duration, not the full active interval length 2delta.

## Evidence verification and rerun

The review first read `../physics/C/handoff.md`, then the native source, license, reproduction, result, and manifest linked from that packet. All 11 files listed in `../physics/C/manifest.json` match their recorded SHA-256 values, including target, handoff, attempt, assessment, and both input copies. Key evidence identities:

- Switching source: `f948c9be21949f84e1679ab380dde6553183782bdc46f4be8c7a8845da732a68`.
- License: `ad85464110b1cfb21cc24cf94167fac6c2818279fc3d018c354e2ad4cce97ca1`.
- Reproduction: `96e6c41693fce24aba408931b3462a12f85becaab730669557497d52fbcc7633`.
- Original result: `a868ff6471e8f68c2887289797e89b8ce8e57852fe1acacb1fea452eeb61d7af`.

The preserved original numerical output is [the packet's native result bytes](../physics/C/history/a868ff6471e8f68c2887289797e89b8ce8e57852fe1acacb1fea452eeb61d7af), with logical evidence name `result.json`. The inspected runner is [the packet's reproduction source](../physics/C/history/96e6c41693fce24aba408931b3462a12f85becaab730669557497d52fbcc7633). This review's rerun output exists in the task's tool transcript only; there is no newly saved rerun-output file.

The rerun invoked the existing inspected `run` function directly, using the original source hash, Python 3.12.14 and NumPy 2.3.5. Bytecode writing was disabled; the rerun printed to tool output and did not create or overwrite a numerical artifact. All recorded rows were reproduced: centers 0 and 1.25, delta 0.125, 1 and 4, with 512 and 1024 panels. The two computed integral errors and peak error are zero at displayed float precision in every row. Numerical elapsed time was 0.1216681000078097 seconds, approximately 0.00203 minutes. The original elapsed time was 0.10544639997533523 seconds. These are numerical execution times, not preparation or human review times. Preparation/review wall time was not separately instrumented; human review minutes were not observed and must remain unknown.

Hashes establish internal byte consistency, not independent upstream authenticity. The asserted upstream commit `7bf91b9517cfd4f136fb13a98f0a2aee7e903ca4` was not fetched and independently compared in this review. The result's public source URL points to mutable `main`; the handoff's commit and hash supply stronger local provenance but are not a substitute for that remote comparison. The included license identifies BSD 3-Clause and Chris Shallue; no legal certification is made.

As a read-only reference check after the native evidence review, the linked [paper, sections II.2 and III.1](https://arxiv.org/html/2501.06609v2#S2.SS2) was inspected. Equation 9 matches the supplied switching definition; equations 10-11 give its Fourier transform, and equation 21 supplies a vacuum inertial response benchmark. This reference check did not execute the paper's calculation.

## Weaknesses that constrain interpretation

1. The uniform-grid trapezoidal rule integrates the relevant finite Fourier harmonics exactly in exact arithmetic: cos^4 has harmonics through order 2 and cos^8 through order 4 over this interval. Both selected grids exceed those orders. Their agreement is useful reproduction evidence but does not demonstrate generic quadrature convergence or predict response-integral accuracy.
2. The numerical support check samples only the two points tau_mid +/- 2delta. Source inspection proves the intended piecewise support for finite representable inputs; the current tests do not separately assert exact endpoints, near-boundary behavior, or the whole outside domain.
3. Positive finite delta is an assumption, not validated by the upstream constructor. Nonfinite values, zero/negative delta and floating-point loss when the center dwarfs the duration are outside the tested scope.
4. The integral tolerance 1e-10 is absolute in the chosen time units; it is sufficient for the listed deltas but not a scale-independent contract. Peak tolerance is dimensionless 1e-12. The elementary identities are analytic; zero displayed numerical error is not arbitrary precision.
5. The piecewise switching is C^3, not C-infinity: near a boundary it vanishes as distance^4 and its fourth derivative jumps. Do not characterize this example as infinitely differentiable or infer full curved-spacetime convergence from it.

## Deferred flat-spacetime baseline: minimal acceptance contract

This is a planning note, not the next implementation assignment. The immediate MVP remains a static local starting page for the existing target, attempt and assessment. A later, separately authorized target may implement one inertial, pointlike, linearly coupled Unruh-DeWitt detector in the vacuum of a real massless scalar field in 3+1 Minkowski spacetime, with hbar = c = 1 and the same switching. Report leading-order response F, with coupling and detector matrix-element factors divided out; it is not itself a probability.

From the vacuum plane-wave measure, angular integration and the two proper-time integrations give the regular spectral formula F(E) = (1/(4pi^2)) integral_0^infinity omega |chi_hat(E+omega)|^2 d omega, where chi_hat(k) = integral chi(tau) exp(-ik tau) d tau. Positive E means excitation. Define a=E delta and chi_hat(k)=delta exp(-ik tau_mid) g(k delta); then F(a)=(1/(4pi^2)) integral_a^infinity (q-a)g(q)^2 d q. Derive g from the finite cosine expansion or the paper's transform, treating removable singularities at 0, +/-pi and +/-2pi explicitly.

Before implementation, freeze these acceptance requirements:

- Check g(0)=3/4, g(+/-pi)=1/2, g(+/-2pi)=1/8, evenness, and agreement with direct Fourier quadrature of the original switching. Reject nonfinite inputs and nonpositive delta.
- Evaluate a in {-4,-1,0,1,4}; require finite nonnegative F, center invariance, and scale invariance at fixed a, including at least one dimensional-form cross-check.
- Use response tolerance T=1e-8+1e-6|F|; two successive frequency-grid halvings and an independent upper-limit doubling must each change the result by at most T/4. Bound the omitted tail separately. One derived bound is tail <= 64pi^6/(75Q^8) when Q>=max(4pi,2|a|), from g(q)=3pi^4 sin(q)/[q(q^2-pi^2)(q^2-4pi^2)]. Require that bound <= T/4. Refinement alone is empirical, not rigorous quadrature certification.
- For a=1 and 4, verify F(-a)-F(a)=35a/(128pi), within the sum of response tolerances. This follows from evenness and Parseval's identity and checks energy sign and normalization. Finite-switching vacuum excitation need not vanish.
- Save source hashes, conventions, parameters, environment, timing, original output path and all acceptance evidence for fresh review. No target acceptance follows merely from implementation completion.

NumPy alone is justified for this future bounded baseline: elementary functions and a regular one-dimensional quadrature suffice. No black-hole coefficient data, SciPy, thermal sweep or horizon computation is needed. No new physics or FPM advantage is implied.

## Assignment metadata caveat

The packaged assignment contains fixture_model_tokens=0, fixture_wall_seconds=5 and frozen-corpus external-search metadata. The parent task identified these as mistakenly carried fixture budgets and separately authorized this review. This report is not an equal-budget experiment, blinded usefulness trial or execution under those fixture conditions. It includes one read-only public-paper reference check and must not be represented as frozen-corpus-only. No human/domain reviewer participated.
