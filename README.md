# First Principles Map

**[Open the app](https://sdcarlson.github.io/first-principles-map/)** — no installation needed.

Explore evidence, explanations and open questions across physics, evolution and consciousness. Each idea includes sources, assumptions or limitations, and a question to think through.

Use the notebook to work through your own question and download your notes.

The local research-handoff prototype preserves scoped questions, attempts, assessments and original evidence. Its current example covers a published detector-switching prerequisite; formal scientific acceptance remains withheld. See the [decision and evidence](research/DECISION.md).

With Python 3.10 or later, generate a new local starting folder:

```sh
python research/start.py research/runs/my-start
```

Open `research/runs/my-start/index.html`, or read `START.md` in the same folder. Both provide original evidence links and a copyable continuation prompt. Keep the whole folder together; each output destination must be new. Generation uses the standard library and makes no network or model calls. Custom stores or targets require an explicit matching `--brief`.

[Verification](research/evidence/mvp-verification.json): 14 map tests and 37 research tests passed, including evidence integrity, safe links and copied-prompt equality. Rendered browser layout and the operating-system clipboard remain unverified because local-file navigation was blocked by the browser tool. This is a workflow prototype, not evidence of scientific value or demand.

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
