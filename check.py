#!/usr/bin/env python3
import json
import sys
from pathlib import Path

g = json.loads(Path(__file__).with_name("graph.json").read_text())
nodes = {n["id"]: n for n in g["nodes"]}
kinds = {i: n["kind"] for i, n in nodes.items()}


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


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

banned = {"physics-we-can-write", "cosmology"}
if banned & set(nodes):
    fail(f"junk drawer present: {banned & set(nodes)}")

need = [
    "conservation",
    "causality",
    "test-against-nature",
    "baryons-plus-gravity",
    "quantum-mechanics",
    "observers-as-described",
    "dark-matter",
    "measurement",
    "consciousness",
]
for i in need:
    if i not in nodes:
        fail(f"missing {i}")


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

obs_assump = {a.lower() for a in nodes["observers-as-described"]["assumptions"]}
if obs_assump <= {"conservation", "causality", "test against nature", "test-against-nature"}:
    fail("observers model is a junk drawer")

print("ok", len(nodes), "nodes", len(g["edges"]), "edges")
