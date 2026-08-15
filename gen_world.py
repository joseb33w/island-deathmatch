#!/usr/bin/env python3
"""Generator for "Island Deathmatch" — 15x15 chunk-mode PvP island.

Zones by Chebyshev ring r = max(|gx|,|gz|):
  r <= 2 : URBAN CORE   (5x5, road grid, parametric structures, asphalt/concrete)
  r == 3 : OUTSKIRTS    (farm + 1-2 small structures, transition)
  r == 4 : FARMLAND     (barns/silos/fenced fields, grass/dirt)
  r == 5 : FARM->HILL   (sparse fields, more trees)
  r >= 6 : HILLS        (rocky/grassy wilderness, scatter only)

Landmarks: hero skyscraper @ cell [1,1]; windmill cluster @ [-4,-4];
steel watchtower (goal) @ [7,0].
Emits /workspace/world.json. Deterministic (seeded per cell).
"""
import json, random

CS = 16          # cell_size
HALF = 8.0
CITY_R = 2
FARM_URL = "props/q_farmbuild/"
BARNS = ["Barn.glb", "BigBarn.glb", "SmallBarn.glb", "OpenBarn.glb", "Silo_House.glb"]

def rng_for(gx, gz):
    return random.Random(1000003 * (gx + 50) + 7919 * (gz + 50) + 42)

def ring(gx, gz):
    return max(abs(gx), abs(gz))

def roads_for(gx, gz):
    r = ring(gx, gz)
    if r <= CITY_R:
        ns = gx in (-2, 0, 2)
        ew = gz in (-2, 0, 2)
        if ns and ew: return [{"dir": "x", "width": 7}]
        if ns:        return [{"dir": "ns", "width": 7}]
        if ew:        return [{"dir": "ew", "width": 7}]
        return []
    # arterials out of the city: N/S along gx=0, E/W along gz=0, to ring 6
    if gx == 0 and 3 <= abs(gz) <= 6: return [{"dir": "ns", "width": 6}]
    if gz == 0 and 3 <= abs(gx) <= 6: return [{"dir": "ew", "width": 6}]
    return []

# ---------------- city structures ----------------
def mk_struct(rng, x, z, fp, r):
    floors = max(4, min(20, int(16 - 1.9 * r + rng.uniform(-4, 5))))
    mat = rng.choice(["concrete", "glass", "concrete", "glass", "concrete"])
    if floors >= 13:
        profile = rng.choice(["vertical", "taper", "setback", "vertical"])
    else:
        profile = "vertical"
    cap = "flat" if floors >= 7 else rng.choice(["flat", "flat", "hip"])
    s = {"pos": [round(x, 2), round(z, 2)],
         "footprint": [round(fp[0], 2), round(fp[1], 2)],
         "floors": floors, "profile": profile, "cap": cap,
         "facade": "windows", "material": mat,
         "rot": rng.choice([0, 90, 180, 270])}
    return s

def city_cell(gx, gz, rng):
    r = ring(gx, gz)
    rd = roads_for(gx, gz)
    kind = rd[0]["dir"] if rd else "block"
    cell = {"cell": [gx, gz],
            "ground": "asphalt" if rd else "concrete",
            "roads": rd, "structures": [], "props": [], "scatter": []}

    # HERO SKYSCRAPER plaza cell
    if (gx, gz) == (1, 1):
        cell["ground"] = "concrete"
        cell["structures"].append({
            "pos": [0, 0], "footprint": [9, 9], "floors": 25,
            "profile": "taper", "cap": "flat", "facade": "windows",
            "material": "glass",
            "window_glow": [1.0, 0.9, 0.6],
            "sign_light": {"color": [0.25, 0.85, 1.0], "energy": 3, "range": 26}})
        for px, pz in [(-6.5, -6.5), (6.5, -6.5), (-6.5, 6.5), (6.5, 6.5)]:
            cell["props"].append({"kind": "plant", "pos": [px, pz]})
        cell["props"].append({"kind": "crate", "pos": [-6.5, 0]})
        cell["props"].append({"kind": "barrel", "pos": [6.5, 0.8]})
        return cell

    slots = []
    if kind == "ns":     # road strip x in [-3.5,3.5]; build east/west
        for sx in (-5.8, 5.8):
            for sz in (-5.2, 0.0, 5.2):
                slots.append((sx, sz, (rng.uniform(3.2, 4.0), rng.uniform(3.2, 4.0))))
    elif kind == "ew":
        for sz in (-5.8, 5.8):
            for sx in (-5.2, 0.0, 5.2):
                slots.append((sx, sz, (rng.uniform(3.2, 4.0), rng.uniform(3.2, 4.0))))
    elif kind == "x":    # crossroads: 4 corner towers
        for sx in (-5.8, 5.8):
            for sz in (-5.8, 5.8):
                slots.append((sx, sz, (rng.uniform(3.4, 4.2), rng.uniform(3.4, 4.2))))
    else:                # full block, no road
        for sx in (-4.4, 4.4):
            for sz in (-4.4, 4.4):
                slots.append((sx, sz, (rng.uniform(4.6, 5.4), rng.uniform(4.6, 5.4))))

    n = min(len(slots), rng.randint(4, 6))
    rng.shuffle(slots)
    for sx, sz, fp in slots[:n]:
        cell["structures"].append(mk_struct(rng, sx, sz, fp, r))

    # neon sign_lights on exactly two designated non-hero buildings
    if (gx, gz) == (2, -2) and cell["structures"]:
        cell["structures"][0]["sign_light"] = {"color": [1.0, 0.25, 0.65], "energy": 2.5, "range": 20}
    if (gx, gz) == (-2, 1) and cell["structures"]:
        cell["structures"][0]["sign_light"] = {"color": [1.0, 0.65, 0.15], "energy": 2.5, "range": 20}

    # street dressing (kept clear of road strips: |axis| >= 4.6)
    dress = rng.randint(2, 4)
    opts = ["crate", "barrel", "plant", "tree"]
    for i in range(dress):
        k = rng.choice(opts)
        if kind == "ns":
            px, pz = rng.choice([-4.8, 4.8]), rng.uniform(-7, 7)
        elif kind == "ew":
            px, pz = rng.uniform(-7, 7), rng.choice([-4.8, 4.8])
        elif kind == "x":
            px, pz = rng.choice([-4.8, 4.8]), rng.choice([-4.8, 4.8])
            px += rng.uniform(-0.6, 0.6); pz += rng.uniform(-0.6, 0.6)
        else:
            px, pz = rng.uniform(-1.4, 1.4), rng.uniform(-1.4, 1.4)
        cell["props"].append({"kind": k, "pos": [round(px, 2), round(pz, 2)]})
    return cell

# ---------------- farm helpers ----------------
def fence_row(x0, z0, dx, dz, n, rot, url="Fence.glb"):
    return [{"url": FARM_URL + url, "pos": [round(x0 + i * dx, 2), round(z0 + i * dz, 2)], "rot": rot}
            for i in range(n)]

def farm_cell(gx, gz, rng, outskirt=False, sparse=False):
    rd = roads_for(gx, gz)
    on_ns = any(r["dir"] == "ns" for r in rd)
    on_ew = any(r["dir"] == "ew" for r in rd)
    ground = rng.choice(["grass", "grass", "dirt"]) if not sparse else "grass"
    cell = {"cell": [gx, gz], "ground": ground, "roads": rd,
            "structures": [], "props": [], "scatter": []}

    # keep buildings off the road strip: roads are on x (ns) or z (ew) center
    def clear(px, pz):
        if on_ns and abs(px) < 5.0: px = 5.8 if px >= 0 else -5.8
        if on_ew and abs(pz) < 5.0: pz = 5.8 if pz >= 0 else -5.8
        return px, pz

    if not sparse:
        main = rng.choice(BARNS)
        mx, mz = clear(rng.choice([-4.5, 4.5]), rng.choice([-4.5, 4.5]))
        cell["props"].append({"url": FARM_URL + main, "pos": [mx, mz], "rot": rng.choice([0, 90, 180, 270])})
        side = rng.choice(["Silo.glb", "WaterTower.glb", "Windmill.glb", "Silo.glb"])
        sx, sz = clear(-mx, mz + rng.choice([-1.5, 1.5]))
        cell["props"].append({"url": FARM_URL + side, "pos": [round(sx, 2), round(sz, 2)]})
        # fenced field rectangle: two fence rows framing a crop strip
        fz = 6.4 if mz < 0 else -6.4
        cell["props"] += fence_row(-6.0, fz, 2.4, 0, 6, 0)
        cell["scatter"].append({"kind": "plant", "count": rng.randint(18, 30), "collider": False})
        cell["scatter"].append({"kind": "bush", "count": rng.randint(5, 9)})
        cell["scatter"].append({"kind": "tree", "count": rng.randint(2, 4)})
    else:
        # sparse transition meadow: a fence remnant + trees
        if rng.random() < 0.55:
            rot = rng.choice([0, 90])
            if rot == 0:
                cell["props"] += fence_row(-4.8, rng.choice([-5.5, 5.5]), 2.4, 0, 4, 0, "Fence2.glb")
            else:
                cell["props"] += fence_row(rng.choice([-5.5, 5.5]), -4.8, 0, 2.4, 4, 90, "Fence2.glb")
        if rng.random() < 0.25:
            px, pz = clear(rng.choice([-5.0, 5.0]), rng.choice([-5.0, 5.0]))
            cell["props"].append({"url": FARM_URL + "SmallBarn.glb", "pos": [px, pz], "rot": rng.choice([0, 90])})
        cell["scatter"].append({"kind": "tree", "count": rng.randint(6, 12)})
        cell["scatter"].append({"kind": "bush", "count": rng.randint(4, 8)})
        cell["scatter"].append({"kind": "rock", "count": rng.randint(2, 5)})

    if outskirt and rng.random() < 0.5:
        # 1-2 small edge-of-town structures, clear of road strips
        for i in range(rng.randint(1, 2)):
            px, pz = clear(rng.choice([-5.6, 5.6]), -5.6 if i == 0 else 5.6)
            cell["structures"].append({
                "pos": [px, pz], "footprint": [rng.uniform(4.0, 5.0), rng.uniform(4.0, 5.0)],
                "floors": rng.randint(2, 4), "profile": "vertical",
                "cap": rng.choice(["flat", "gable"]), "facade": "windows",
                "material": "concrete", "rot": rng.choice([0, 90])})
            cell["structures"][-1]["footprint"] = [round(v, 2) for v in cell["structures"][-1]["footprint"]]
    return cell

# ---------------- hill cells ----------------
def hill_cell(gx, gz, rng):
    r = ring(gx, gz)
    rd = roads_for(gx, gz)
    w = ["grass", "grass", "rock", "dirt"] if r < 7 else ["rock", "rock", "grass", "dirt"]
    cell = {"cell": [gx, gz], "ground": rng.choice(w), "roads": rd,
            "props": [], "scatter": []}
    dense = 1.0 if r == 5 else (0.75 if r == 6 else 0.55)
    cell["scatter"].append({"kind": "tree", "count": max(3, int(rng.randint(8, 16) * dense))})
    cell["scatter"].append({"kind": "rock", "count": rng.randint(5, 9)})
    cell["scatter"].append({"kind": "bush", "count": max(2, int(rng.randint(4, 8) * dense))})
    for _ in range(rng.randint(1, 3)):
        k = rng.choice(["rock", "stump", "log"])
        px, pz = rng.uniform(-7, 7), rng.uniform(-7, 7)
        if rd:  # keep placed props off arterial strips
            if any(x["dir"] == "ns" for x in rd) and abs(px) < 4.2: px = 5.5 if px >= 0 else -5.5
            if any(x["dir"] == "ew" for x in rd) and abs(pz) < 4.2: pz = 5.5 if pz >= 0 else -5.5
        cell["props"].append({"kind": k, "pos": [round(px, 2), round(pz, 2)]})
    return cell

# ---------------- assemble ----------------
cells = []
for gz in range(-7, 8):
    for gx in range(-7, 8):
        rng = rng_for(gx, gz)
        r = ring(gx, gz)
        if (gx, gz) == (0, 4):
            # START CELL — farmland, center clear (arterial road runs through it)
            c = {"cell": [0, 4], "ground": "grass", "roads": roads_for(0, 4),
                 "props": [], "scatter": [{"kind": "bush", "count": 6},
                                           {"kind": "plant", "count": 12, "collider": False}]}
            c["props"].append({"url": FARM_URL + "SmallBarn.glb", "pos": [5.8, -5.5], "rot": 270})
            c["props"] += fence_row(-6.4, -6.0, 0, 2.4, 6, 90)
            cells.append(c)
            continue
        if (gx, gz) == (-4, -4):
            # FARM LANDMARK — tall windmill cluster
            c = {"cell": [-4, -4], "ground": "grass", "roads": [],
                 "landmark": {"url": FARM_URL + "TowerWindmill.glb", "pos": [0, 0]},
                 "props": [
                     {"url": FARM_URL + "TowerWindmill.glb", "pos": [-5.5, 3.5]},
                     {"url": FARM_URL + "TowerWindmill.glb", "pos": [5.0, -4.0]},
                     {"url": FARM_URL + "WaterTower.glb", "pos": [5.5, 5.5]},
                 ] + fence_row(-6.0, 6.6, 2.4, 0, 6, 0),
                 "scatter": [{"kind": "plant", "count": 24, "collider": False},
                             {"kind": "bush", "count": 6}]}
            cells.append(c)
            continue
        if (gx, gz) == (7, 0):
            # GOAL CELL — hill watchtower (radio mast), center kept clear
            c = {"cell": [7, 0], "ground": "rock", "roads": [],
                 "structures": [{
                     "pos": [0, -4.5], "footprint": [3, 3], "height": 24,
                     "profile": "taper", "cap": "spire", "material": "steel",
                     "facade": "plain",
                     "sign_light": {"color": [1.0, 0.15, 0.1], "energy": 3, "range": 30}}],
                 "props": [{"kind": "rock", "pos": [-5, 3]}, {"kind": "rock", "pos": [4, 4]},
                            {"kind": "stump", "pos": [-4, -6]}],
                 "scatter": [{"kind": "rock", "count": 8}, {"kind": "tree", "count": 5},
                             {"kind": "bush", "count": 4}]}
            cells.append(c)
            continue
        if r <= CITY_R:
            cells.append(city_cell(gx, gz, rng))
        elif r == 3:
            cells.append(farm_cell(gx, gz, rng, outskirt=True))
        elif r == 4:
            cells.append(farm_cell(gx, gz, rng))
        elif r == 5:
            cells.append(farm_cell(gx, gz, rng, sparse=True))
        else:
            cells.append(hill_cell(gx, gz, rng))

world = {
    "mode": "chunk",
    "title": "Island Deathmatch",
    "grid": {"cell_size": CS},
    "start_cell": [0, 4],
    "goal": {"type": "reach_cell", "target": [7, 0]},
    "terrain": {"amplitude": 7, "frequency": 0.012, "seed": 1177, "octaves": 4, "material": "grass"},
    "cells": cells,
}

# strip empty keys for compactness
for c in cells:
    for k in ("roads", "structures", "props", "scatter"):
        if k in c and not c[k]:
            del c[k]

with open("/workspace/world.json", "w") as f:
    json.dump(world, f, indent=1)

# ---------------- self-checks ----------------
errs = []
assert len(cells) == 225, len(cells)
coords = {tuple(c["cell"]) for c in cells}
assert len(coords) == 225
for gx in range(-7, 8):
    for gz in range(-7, 8):
        assert (gx, gz) in coords, (gx, gz)

urls = set()
for c in cells:
    props = c.get("props", [])
    if len(props) > 12:
        errs.append(f"cell {c['cell']}: {len(props)} props > 12")
    for s in c.get("scatter", []):
        if s["count"] > 40:
            errs.append(f"cell {c['cell']}: scatter {s['count']} > 40")
    for p in props:
        if "url" in p: urls.add(p["url"])
    if "landmark" in c: urls.add(c["landmark"]["url"])
    # structure overlap + road-strip checks
    boxes = []
    for s in c.get("structures", []):
        x, z = s["pos"]; w, d = s["footprint"]
        boxes.append((x - w/2, x + w/2, z - d/2, z + d/2))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]:
                errs.append(f"cell {c['cell']}: structures {i},{j} overlap")
    for rd in c.get("roads", []):
        hw = rd["width"] / 2.0
        for i, (x0, x1, z0, z1) in enumerate(boxes):
            if rd["dir"] in ("ns", "x") and x0 < hw and x1 > -hw:
                errs.append(f"cell {c['cell']}: structure {i} on ns road strip")
            if rd["dir"] in ("ew", "x") and z0 < hw and z1 > -hw:
                errs.append(f"cell {c['cell']}: structure {i} on ew road strip")

n_struct = sum(len(c.get("structures", [])) for c in cells)
print(f"cells: {len(cells)}  structures: {n_struct}  distinct GLB urls: {len(urls)}")
print("urls:", sorted(urls))
if errs:
    print("ERRORS:"); [print(" ", e) for e in errs]
    raise SystemExit(1)
print("self-checks OK")
