#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class Fail(Exception):
    pass


def fail(msg):
    raise Fail(msg)


def check(g):
    nodes = {n["id"]: n for n in g["nodes"]}
    kinds = {i: n["kind"] for i, n in nodes.items()}

    for n in g["nodes"]:
        if n["kind"] not in {"axiom", "model", "gap"}:
            fail(f"bad kind {n['id']}")
        if n["kind"] == "gap" and n.get("axiom_slot") != "UNKNOWN":
            fail(f"gap {n['id']} must have axiom_slot UNKNOWN")
        if n["kind"] == "model" and not n.get("assumptions"):
            fail(f"model {n['id']} needs named assumptions")

    for e in g["edges"]:
        if e["src"] not in nodes or e["dst"] not in nodes:
            fail(f"dangling {e}")
        if e["type"] not in g["edge_types"]:
            fail(f"bad type {e}")
        if e["type"] == "unexplained-by":
            if kinds[e["src"]] != "gap" or kinds[e["dst"]] != "model":
                fail(f"unexplained-by must be gap -> model: {e}")
        if e["type"] == "derives":
            if kinds[e["src"]] not in {"axiom", "model"} or kinds[e["dst"]] != "model":
                fail(f"derives must be axiom|model -> model: {e}")
        if e["type"] == "constrains":
            if kinds[e["src"]] != "gap" or kinds[e["dst"]] != "model":
                fail(f"constrains must be gap -> model: {e}")

    axiom_label = {
        "conservation": "Stuff is conserved",
        "causality": "Cause and effect",
        "test-against-nature": "Test it in the real world",
    }
    for n in g["nodes"]:
        if n["kind"] == "axiom":
            if n["id"] not in axiom_label:
                fail(f"new starting rule {n['id']}")
            if n["label"] != axiom_label[n["id"]]:
                fail(f"starting rule label drifted {n['id']}")

    fields = {
        "physics-we-can-write",
        "cosmology",
        "physics",
        "chemistry",
        "biology",
        "thermodynamics",
        "ai",
        "artificial-intelligence",
        "neuroscience",
        "psychology",
        "computer-science",
    }
    hit = fields & set(nodes)
    if hit:
        fail(f"field as box: {hit}")

    need = {
        "conservation": "axiom",
        "causality": "axiom",
        "test-against-nature": "axiom",
        "baryons-plus-gravity": "model",
        "quantum-mechanics": "model",
        "observers-as-described": "model",
        "dark-matter": "gap",
        "measurement": "gap",
        "consciousness": "gap",
    }
    for i, k in need.items():
        if i not in nodes:
            fail(f"missing {i}")
        if nodes[i]["kind"] != k:
            fail(f"{i} must be {k}")

    attached = {e["src"] for e in g["edges"] if e["type"] == "unexplained-by"}
    for n in g["nodes"]:
        if n["kind"] == "gap" and n["id"] not in attached:
            fail(f"gap {n['id']} must hang off a current story")

    def has(src, typ, dst):
        return any(e["src"] == src and e["type"] == typ and e["dst"] == dst for e in g["edges"])

    if not has("dark-matter", "unexplained-by", "baryons-plus-gravity"):
        fail("dark-matter must unexplained-by baryons-plus-gravity")
    if not has("measurement", "unexplained-by", "quantum-mechanics"):
        fail("measurement must unexplained-by quantum-mechanics")
    if not has("consciousness", "unexplained-by", "observers-as-described"):
        fail("consciousness must unexplained-by observers-as-described")
    if has("consciousness", "unexplained-by", "baryons-plus-gravity"):
        fail("consciousness must not hang off gravity")
    if has("measurement", "constrains", "baryons-plus-gravity"):
        fail("the blur leftover must not also hang off ordinary matter")

    obs_assump = {a.lower() for a in nodes["observers-as-described"]["assumptions"]}
    if obs_assump <= {"conservation", "causality", "test against nature", "test-against-nature"}:
        fail("observers model is a junk drawer")

    jargon = ("baryon", "born rule", "unitary", "axiom slot", "collapse postulate")
    for n in g["nodes"]:
        blob = " ".join(
            [n["label"], n.get("note", ""), *n.get("assumptions", [])]
        ).lower()
        for w in jargon:
            if w in blob:
                fail(f"jargon in {n['id']}: {w}")
        if "<" in blob:
            fail(f"html in {n['id']}")


def clone(g):
    return json.loads(json.dumps(g))


def must_fail(g, needle):
    try:
        check(g)
    except Fail as e:
        if needle.lower() not in str(e).lower():
            fail(f"wrong fail ({e}), wanted {needle}")
        return
    fail(f"attack not caught: {needle}")


def attacks(base):
    g = clone(base)
    g["nodes"].append(
        {
            "id": "hoffman",
            "kind": "axiom",
            "label": "Experience is more basic than space and time",
        }
    )
    must_fail(g, "starting rule")

    g = clone(base)
    g["nodes"].append({"id": "thermodynamics", "kind": "axiom", "label": "Heat and energy flow"})
    must_fail(g, "starting rule")

    g = clone(base)
    g["nodes"].append({"id": "physics", "kind": "axiom", "label": "Physics"})
    must_fail(g, "starting rule")

    g = clone(base)
    g["nodes"].append(
        {"id": "symmetry", "kind": "axiom", "label": "Nature looks the same from every angle"}
    )
    must_fail(g, "starting rule")

    g = clone(base)
    next(n for n in g["nodes"] if n["id"] == "conservation")["label"] = "Thermodynamics"
    must_fail(g, "label")

    g = clone(base)
    g["nodes"].append(
        {
            "id": "entropy-arrow",
            "kind": "gap",
            "label": "Why time has an arrow",
            "axiom_slot": "UNKNOWN",
        }
    )
    must_fail(g, "hang off")

    g = clone(base)
    g["nodes"].append(
        {"id": "chemistry", "kind": "model", "label": "Chemistry", "assumptions": ["atoms stick"]}
    )
    must_fail(g, "field")

    g = clone(base)
    g["nodes"].append(
        {
            "id": "ai",
            "kind": "model",
            "label": "Artificial intelligence",
            "assumptions": ["computers can think"],
        }
    )
    must_fail(g, "field")

    g = clone(base)
    next(n for n in g["nodes"] if n["id"] == "dark-matter")["label"] = "<img src=x>"
    must_fail(g, "html")


def pages():
    think = (ROOT / "think.html").read_text()
    if ".catch(" not in think:
        fail("think fetch must fail out loud")
    if "esc(t)" not in think:
        fail("think chips must escape labels")
    if "Example:" not in think:
        fail("think needs one worked example")
    index = (ROOT / "index.html").read_text()
    if "t.textContent = text" not in index:
        fail("map must put labels in textContent")
    if "graph.edge_types" in index:
        fail("legend must list edges that exist, not every type name")


def main():
    g = json.loads((ROOT / "graph.json").read_text())
    try:
        check(g)
        attacks(g)
        pages()
    except Fail as e:
        print("FAIL:", e)
        sys.exit(1)
    print("ok", len(g["nodes"]), "nodes", len(g["edges"]), "edges")


if __name__ == "__main__":
    main()
