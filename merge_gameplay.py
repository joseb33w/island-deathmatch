#!/usr/bin/env python3
"""Merge the gameplay layer (multiplayer/PvP rules/weapons/sky/water/vehicles/traffic/populate/
director/regions) into the Architect's world.json, plus the Structures specialist's interior edits."""
import json, os, sys

W = "/workspace/world.json"
w = json.load(open(W))

# ---- Structures specialist interior edits (structures.json) ----
sp = "/workspace/structures.json"
if os.path.exists(sp):
    s = json.load(open(sp))
    def apply(edits):
        for e in edits or []:
            tgt = tuple(e["cell"]); idx = e["index"]
            for c in w["cells"]:
                if tuple(c["cell"]) == tgt:
                    c["structures"][idx] = e["structure"]
                    print("applied structure edit", tgt, idx)
    apply(s.get("edits"))
    apply(s.get("neighbor_adjustments"))
else:
    print("WARN: structures.json not present — interiors not merged")

# ---- identity / avatar (disclosed library fallback: Meshy not provisioned, free tier) ----
w["hero_model"] = "characters/kk_Ranger.glb"
w["character_source"] = "library-fallback: Meshy not provisioned this session (free tier) - KayKit Ranger (Rig_Medium, engine-retargeted clips) as player/peer avatar"

# ---- multiplayer (engine-owned netsync; build id is the default room) ----
w["multiplayer"] = {
    "enabled": True,
    "max_players": 16,
    "supabase_url": "https://xhhmxabftbyxrirvvihn.supabase.co",
    "supabase_anon_key": "sb_publishable_NZHoIxqqpSvVBP8MrLHCYA_gmg1AbN-",
}

# ---- armament: one ranged weapon, equipped at spawn (3 body-shots on a 100 HP player) ----
w["weapons"] = {
    "scout_rifle": {
        "name": "Scout Rifle", "kind": "ranged", "damage": 34, "rate": 2.2,
        "range": 34.0, "projectile": {"speed": 42.0, "arc": False},
        "model": "parametric:rifle",
    }
}
w["start_weapon"] = "scout_rifle"

# ---- day/night cycle ----
w["sky"] = {"loop": True, "cycle": [
    {"time": "day", "weather": "clear", "seconds": 150},
    {"time": "sunset", "weather": "clear", "seconds": 35},
    {"time": "night", "weather": "clear", "seconds": 110},
    {"time": "sunrise", "weather": "clear", "seconds": 35},
]}

# ---- island: terrain falloff into a sea bed + ocean water ----
w["terrain"]["island"] = {"radius": 168, "shore": 70, "depth": 12}
w["water"] = {"level": -6.0, "depth": 6, "shallow": [0.22, 0.50, 0.55],
              "deep": [0.03, 0.12, 0.25], "wave_amp": 0.22}

# ---- rides: two drivable cars near the arterials (parametric bodies) ----
w["vehicles"] = [
    {"pos": [5, 52], "profile": "car", "name": "Sedan", "color": [0.75, 0.2, 0.15]},
    {"pos": [-5, -52], "profile": "car", "name": "Coupe", "color": [0.15, 0.35, 0.75]},
]

# ---- ambient traffic on the CITY road cells (r<=2 with roads) ----
CARS = ["props/q_cars/NormalCar1.glb", "props/q_cars/Taxi.glb", "props/q_cars/SUV.glb"]
tcells = 0
for c in w["cells"]:
    gx, gz = c["cell"]
    if max(abs(gx), abs(gz)) <= 2 and c.get("roads"):
        c["traffic"] = {"set": CARS, "count": 2, "speed": 8}
        tcells += 1
print("traffic cells:", tcells)

# ---- grazing herds on a spread of farmland cells (ring 4) ----
HERDS = [
    ((-4, -3), "animals/farm_Cow.glb", 3), ((4, -4), "animals/farm_Sheep.glb", 4),
    ((-4, 2), "animals/farm_Horse.glb", 2), ((3, 4), "animals/farm_Cow.glb", 3),
    ((-2, 4), "animals/farm_Sheep.glb", 4), ((4, 1), "animals/farm_Horse.glb", 2),
    ((0, -4), "animals/farm_Cow.glb", 2), ((-4, 4), "animals/farm_Sheep.glb", 3),
]
placed = 0
for (cell, model, n) in HERDS:
    for c in w["cells"]:
        if tuple(c["cell"]) == cell:
            c.setdefault("populate", []).append(
                {"set": [model], "count": n, "vary": True,
                 "behaviour": "wander", "radius": 6, "speed": 1.0})
            placed += 1
print("herd cells:", placed)

# ---- zone regions (brief entry toast + ambience switch handled by the engine shell) ----
w["regions"] = [
    {"name": "Downtown", "center": [0, 0], "radius": 42, "ambient": "town_crowd"},
    {"name": "Windmill Farms", "center": [-64, -64], "radius": 40, "ambient": "auto_isle"},
    {"name": "Watchtower Ridge", "center": [112, 0], "radius": 36, "ambient": "auto_isle"},
]

# ---- PvP state + rules + HUD ----
w["vars"] = {
    "kills":  {"init": 0, "scope": "player"},
    "deaths": {"init": 0, "scope": "player"},
}
w["rules"] = [
    {"id": "welcome", "when": {"event": "start"},
     "then": [{"toast": "ISLAND DEATHMATCH - 16-player PvP. Hostiles show on your minimap."},
              {"subtitle": {"text": "Left: move joystick  |  Right: drag to look  |  ATTACK to fire", "hold": 8}},
              {"ambient": "wind_real"}]},
    {"id": "score", "when": {"event": "player_killed"},
     "then": [{"add": "kills", "value": 1}, {"toast": "FRAG! Total: {kills}"}, {"sound": "hit"}]},
    {"id": "muzzle", "when": {"event": "weapon_fired"}, "then": [{"shake": 0.08}]},
    {"id": "hitfx", "when": {"event": "hit_by_player"},
     "then": [{"shake": 0.25}, {"sound": "hurt"}]},
    {"id": "down", "when": {"event": "player_died"},
     "then": [{"add": "deaths", "value": 1}, {"sound": "death"},
              {"toast": "Fragged - respawning... (deaths: {deaths})"}, {"respawn": True}]},
]
# ONE readout: a second top-band counter gets shoved to the bottom edge on narrow portrait
# (gamefeel P1 - the HUD placer's vertical escape); deaths surface in the death toast instead.
w["hud"] = [
    {"bind": "kills", "format": "int", "pos": "top_center", "label": "FRAGS"},
]

# ---- director: title screen + music (one mode -> one shared room, no map matchmaking split) ----
w["director"] = {
    "hide_hud": ["stable", "weapon", "potion"],
    "music": {"default": "battle_pursuit"},
    "ambient_auto": {"auto_isle": {"day": "wind_real", "night": "night_crickets"}},
}

json.dump(w, open(W, "w"), indent=1)
print("world.json merged OK:", len(json.dumps(w)) // 1024, "KB")
