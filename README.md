# First Principles Map

A small, source-backed guide to evidence, explanations and open questions in physics, evolution and consciousness.

Start with a question. Inspect a measured result, follow the connections, and ask what the evidence does **and does not** establish.

## Explore

- Does measurement require a mind?
- Can two good clocks disagree?
- How do we infer matter we cannot see?
- Does forgetting have a physical cost?
- Could evolution have turned out differently?
- What would test a theory of consciousness?

The map has 20 ideas, 17 explained connections and ten source records. Search the whole map or follow a short reading path. Each idea includes its scope, limitations, sources and a question to think through. The notebook helps turn a question into observations, assumptions, competing explanations and a test; notes can be downloaded as Markdown.

## Run locally

Requires Python 3.10 or later. No packages or build step.

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000. Opening `index.html` directly from disk will usually block loading `graph.json`.

The files remain compatible with GitHub Pages. `viz.html` redirects to the main page. No hosting migration is needed.

## Check changes

```sh
python check.py
python -m unittest -v
node --check app.js
node --check think.js
```

Node is only needed for the optional JavaScript syntax checks. The Python checks validate reference integrity and editorial structure; they do not establish scientific truth or verify that remote links are still live.

## Content rules

`graph.json` is the source of truth for the explorer. Schema version 3 separates observations, models, mechanisms, principles and open questions. It replaces the previous axiom/model/gap schema; external consumers must migrate.

1. Write a specific claim, not a whole discipline or an inspirational slogan.
2. State where it applies and what it does not establish.
3. Attach a research paper, scholarly review or institutional source and explain what it supports.
4. Name model assumptions. Do not assign invented numerical confidence scores.
5. Explain and source each connection. Evidence can support or challenge a prediction; it does not automatically prove an entire theory.
6. Include the idea in a connected reading path. Reading order is not a mathematical deduction.
7. Frame thought prompts and takeaways as editorial questions or synthesis, not as quotes or new discoveries.

Source selection is deliberately small. This is an introductory map, not an exhaustive literature review, a consensus ranking, or a substitute for reading the papers. Source scope notes show why each reference is included. The reviewed date records editorial review, not a guarantee that every research frontier is current.

## What changed in version 3

Removed unsupported derivation arrows, universal “stuff is conserved” claims, and language that conflated quantum measurement with conscious observation. Replaced the fixed nine-box diagram with question paths and inspectable, typed connections. The consciousness path distinguishes competing theories and their tested predictions. The notebook no longer promotes a user's unchecked belief into an axiom.

The app uses plain HTML, CSS and JavaScript. No analytics, accounts, external fonts or client libraries. Notebook notes are not transmitted or automatically saved.
