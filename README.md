# First Principles Map

**[Open the app](https://sdcarlson.github.io/first-principles-map/)** — no installation needed.

Explore evidence, explanations and open questions across physics, evolution and consciousness. Each idea includes sources, assumptions or limitations, and a question to think through.

Use the notebook to work through your own question and download your notes.

The local research-handoff prototype preserves scoped questions, attempts, assessments and original evidence. The original example covers a published detector-switching prerequisite. A bounded flat-spacetime vacuum baseline now has a separate mathematical review; formal scientific acceptance remains withheld. See the [decision and evidence](research/DECISION.md).

With Python 3.10 or later, generate a new local starting folder:

```sh
python research/start.py research/runs/my-start
```

Open `research/runs/my-start/index.html`, or read `START.md` in the same folder. Both provide original evidence links and a copyable continuation prompt. Keep the whole folder together; each output destination must be new. Generation uses the standard library and makes no network or model calls. Custom stores or targets require an explicit matching `--brief`.

[Verification](research/evidence/mvp-verification.json): 14 map tests and 37 research tests passed, including evidence integrity, safe links and copied-prompt equality. Rendered browser layout and the operating-system clipboard remain unverified because local-file navigation was blocked by the browser tool. This is a workflow prototype, not evidence of scientific value or demand.

Current decision: keep the local handoff tool and hold product expansion until real use supports it. User acceptance is pending; structured records have not demonstrated an advantage over the readable Markdown handoff. The next check is to read the generated page, open an evidence link and try copying its prompt into an empty note. See the [canonical decision](research/DECISION.md) for the acceptance criteria and remaining validation dependencies.

The [vacuum review](research/evidence/vacuum-independent/review.md) compares five detector-response values with independent integration of the original published switching function. All 75 review checks passed; the largest response discrepancy was 2.267e-12. Preparatory execution-protocol limitations are disclosed, and this does not validate Hawking radiation or product value. The complete native handoff stays local because its original result includes a machine path; public evidence contains the source, independent raw reference and a comparison pinned to the original result digest.

To reproduce the bounded candidate with Python and NumPy, using a new output file:

```sh
python research/vacuum_baseline.py research/physics/C/inputs/switching.py f948c9be21949f84e1679ab380dde6553183782bdc46f4be8c7a8845da732a68 vacuum-result.json
```

The script records raw checks; it does not grant scientific acceptance. The reviewed native invocation was externally limited to 60 seconds; callers must enforce their own process limit. Seven vacuum tests and the 44-test research suite passed before the final path-only portability change, which used a byte-identical committed source and passed parse/compile checks.

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
