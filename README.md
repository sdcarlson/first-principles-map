# First Principles Map

**[Open the educational map](https://sdcarlson.github.io/first-principles-map/)** — no installation needed.

Explore evidence, explanations and open questions across physics, evolution and consciousness. Each idea includes sources, assumptions or limitations, and a question to think through.

Use the notebook to work through your own question and download your notes.

The educational map and the local research-handoff prototype are different jobs. The map is this public page. The handoff is a separate local folder for recovering one scoped question, inspecting original evidence, and returning attributable bytes. It is not a deployment of the map, and publishing the map does not publish a handoff package.

## Local research-handoff reference

The bundled public example is the original published-code **detector-switching normalization** record. Treat it as a historical reference example. A later bounded flat-spacetime vacuum-response reproduction is already complete and independently reviewed as a **different target**; see the [vacuum review](research/evidence/vacuum-independent/review.md). Formal scientific acceptance remains withheld. Do not treat the default switching example as that vacuum calculation.

Decision record: [research/DECISION.md](research/DECISION.md).

### Generate a local starting folder

With Python 3.10 or later:

```sh
python research/start.py research/runs/my-start
```

Open `research/runs/my-start/index.html`, or read `START.md` in the same folder. Custom stores or targets require an explicit matching `--brief`. Each destination must be new. Generation uses the standard library and makes no network or model calls. A plain `start.py` export does **not** include `toolkit/` or `store/`; the owner keeps the original `research/handoff.py`, `research/fixture_checker.py`, and the matching owner store. Custom exports are not a public-reference demonstration.

### Build the public-reference release candidate

From any working directory, one command packages only the already-public default reference example (not arbitrary private or custom stores, and not the whole workspace):

```sh
python /path/to/research/release.py NEW_DIRECTORY
```

Example from this repository:

```sh
python research/release.py research/runs/my-reference-release
```

That writes `NEW_DIRECTORY` and a deterministic `NEW_DIRECTORY.zip` beside it, and refuses to overwrite either. It packages only the frozen public owner-store snapshot `d8941ef06f00c8e927a9aeba33d372770f251c668235a5eb5f146ca89791a954` and its exact reachable records; extra same-target attempts or unused files are rejected before any output is written. The folder includes the starting page, A/B/C/D packages, that matching owner store, `toolkit/handoff.py`, `toolkit/fixture_checker.py`, `USE.md`, and `submission-template.json`. Leave any earlier candidate folder in place.

### Use and return a package

Give the recipient the **whole folder**, not only a copied prompt. Open `USE.md`. To return work, create a **new** folder with `submission.json` (from `submission-template.json`) plus original result/source attachments; preserve `target`, `base_snapshot`, and scope.

From a **plain** `start.py` export, the owner imports with the original tools and matching store:

```sh
python research/handoff.py --store PATH_TO_OWNER_STORE submit RETURN_FOLDER/submission.json
```

From the **self-contained public-reference release**, run these from the package directory:

```sh
python toolkit/handoff.py --store store submit RETURN_FOLDER/submission.json
python toolkit/handoff.py --store store inspect TARGET
python toolkit/handoff.py --store store check ATTEMPT
python toolkit/handoff.py --store store assess ATTEMPT --reviewer REVIEWER --status withhold --rationale TEXT --limitations TEXT
```

`check` must refuse fixture-checker acceptance for this physics target (`external checker not registered`). Then a distinct reviewer records `withhold`. Do not accept without a passing independent check. A stale snapshot needs owner reconciliation and a new request id. A candidate cannot choose or weaken the checker. Submitted code is not executed.

The packaged `fixture_checker.py` only verifies the software-mechanics graph fixture. It cannot accept this physics target. That is not an independent physics check; none is registered.

### Limits

This is a local reference demonstration, not a deployment. It is not a privacy guarantee for arbitrary stores, not a security sandbox, and not independent human certification of science or identity. Rendered browser layout and the operating-system clipboard remain unverified. Do not claim scientific acceptance from fixture verification.

Python 3.10+ is enough to generate and inspect a handoff. NumPy is needed only for optional vacuum reproduction, not to read a downloaded static package. The reviewed native vacuum invocation was externally limited to 60 seconds; callers must enforce their own process limit.

[Release verification](research/evidence/release-verification.json): 14 map tests and 63 research tests passed. The entire research test process was externally limited to 60 seconds and completed in 5.391 seconds. Independent review also passed 249 package assertions and 12 source-boundary rejection probes, including real Windows directory junctions. A file-symlink probe could not run because Windows denied creation privileges; that branch was reviewed in source. Original evidence, matching templates/snapshots, deterministic ZIP bytes, extracted owner commands, retry/staleness behavior and withheld acceptance were checked. Rendered browser layout and the operating-system clipboard remain unverified. The [earlier verification](research/evidence/mvp-verification.json) is preserved. Commands:

```sh
python check.py
python -m unittest test_check
python -m unittest discover -s research -p "test_*.py" -v
```

When running the full suite, enforce a 60-second external timeout around the entire process; the command above does not set that cap by itself. The reviewed reference release has 66 files and 65 manifest entries. ZIP SHA-256: `80060336db7d388bdb7035cb8337477659f81f8ba8f506469c617bfdc6e321a6`. Identical source bytes and runtime produced identical archives at separate destinations. The release archive remains a local review candidate; it has not been deployed.

Current decision: keep the local handoff tool and hold product expansion until real use supports it. User acceptance is pending; structured records have not demonstrated an advantage over the readable Markdown handoff.

The [vacuum review](research/evidence/vacuum-independent/review.md) compares five detector-response values with independent integration of the original published switching function. All 75 review checks passed; the largest response discrepancy was 2.267e-12. Preparatory execution-protocol limitations are disclosed, and this does not validate Hawking radiation or product value. The complete native handoff stays local because its original result includes a machine path; public evidence contains the source, independent raw reference and a comparison pinned to the original result digest.

To reproduce the bounded candidate with Python and NumPy, using a new output file:

```sh
python research/vacuum_baseline.py research/physics/C/inputs/switching.py f948c9be21949f84e1679ab380dde6553183782bdc46f4be8c7a8845da732a68 vacuum-result.json
```

The script records raw checks; it does not grant scientific acceptance.

## Development

Plain HTML, CSS and JavaScript. No build step or dependencies.

To run locally with Python 3.10 or later:

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000.

Edit `graph.json` to update the map. Include sources, explain connections, and distinguish evidence from assumptions and open questions.

Check changes with:

```sh
python check.py
python -m unittest
```
