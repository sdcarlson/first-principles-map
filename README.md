# First Principles Map

**[Open the app](https://sdcarlson.github.io/first-principles-map/)** — no installation needed.

Explore evidence, explanations and open questions across physics, evolution and consciousness. Each idea includes sources, assumptions or limitations, and a question to think through.

Use the notebook to work through your own question and download your notes.

The local research-handoff experiment is documented in [research/DECISION.md](research/DECISION.md). It is research-only and separate from the educational map.

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
