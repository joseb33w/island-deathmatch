# Godot RPG Streaming Starter (`godot-tmpl-rpg`)

A **data-driven, full-world** base for Zelda/RPG/adventure games: multiple areas streamed
from R2 at runtime, action combat, NPCs + dialogue, chests, quest-flag-gated doors, and an
RPG state layer — all described by a `world.json` + `quests.json` the agent authors and a
chat edit can rewrite. Render config is identical to `godot-templates/3d` (Compatibility /
WebGL2 / nothreads / 720×1280 portrait), so no engine/export change vs the 3D base.

Reach for this base when the request implies a **multi-area world**: a dungeon crawl, an
overworld with towns, a Zelda-like, an adventure/RPG. For a single-screen arcade game use
the `2d`/`3d` base instead.

## How it's put together

| File | Role |
|---|---|
| `main.gd` | orchestration: fetches `world.json`/`quests.json` + the asset manifest, wires the systems, persistent player/combat/HUD, and **polls `world.json` to hot-reload chat edits** |
| `scene_manager.gd` | zone streaming — free the current area, build the next behind a fade; exactly ONE area resident |
| `area_builder.gd` | streams an area's `.glb` from R2 at runtime (`GLTFDocument.append_from_buffer`), shared cache, named-prop `PALETTE`, derived box colliders |
| `interaction.gd` | chests / NPCs (live hints from `npc.myapping.com/chat`) / seam-doors with locks |
| `enemy.gd` | RVO-avoidance enemies that encircle (not clump); **retargets** the clip-less streamed skeleton via `AnimRig` |
| `anim_rig.gd` | shared KayKit `Rig_Medium` retarget — copies clips from the packed `kk_rig_medium_*` libraries onto the clip-less hero/NPC/skeletons (they ship with NO embedded clips). Pack `kk_rig_medium_{general,movementbasic,combatmelee}.glb` into `res://models/` |
| `quest.gd` | quests.json objectives → completion → rewards → **flags that open gated seams** |
| `rpg_systems.gd` | HP / level / XP / gold / inventory / flags |
| `world.json`, `quests.json` | the world data (a sample winnable world ships here) |

## The key trick: assets stream, data is loose

The `.pck` binds only **scripts + shaders**. Every area's `.glb` **streams from R2 at
runtime** from `/godot-assets/…`, and `world.json` + `quests.json` are **loose files served
next to `index.html`** — NOT relied upon from the `.pck`. This is what lets a chat edit
rewrite the world with **no re-export**.

So after exporting, copy the data files into the export so the preview (and the verifier)
can fetch them loose:

```bash
/workspace/godot --headless --path "$GAME" --export-release "Web" "$GAME/out/index.html"
cp "$GAME/world.json" "$GAME/quests.json" "$GAME/out/"     # loose, fetched over HTTP
```

When the build is deployed (`<BUILD_ID>/*` uploaded to the previews bucket), `world.json`
lands at `preview.myapping.com/<BUILD_ID>/world.json` and the game fetches it from its own
URL dir. A chat edit overwrites that one object; the running game's poll hot-reloads it.

## world.json / quests.json schema + the named-prop PALETTE

Documented in full in the `world-streaming` playbook (fetched each session). In short, each
area has `id`, `name`, `ground`/`ambient` `[r,g,b]`, `size`, `scatter`, `enemies`,
`enemy_type`, `spawns`, `seams` (with a `lock`/`requires` gate), optional `chest`, `npc`,
and `props: [{kind, pos}]`. `props.kind` must be one of the `PALETTE` kinds in
`area_builder.gd` (`tree rock barrel crate`/`box` `torch stump log pillar bush banner plant`). A
seam `lock` is opened by holding that item key **or** by a quest `on_complete_flags` flag
(e.g. `dungeon_cleared` → the vault door).

## Winnability is gated — you cannot ship a softlock

The verifier runs **qgcheck** over `world.json` + `quests.json`: a deterministic
quest-graph check that proves the goal is reachable through the lock-and-key graph. A FAIL
(`UNREACHABLE_GOAL`, `CONSUMED_KEY_SOFTLOCK`, `UNSATISFIABLE_REQUIRE`, …) is a build
blocker — fix the graph (the witness names the blocking token); don't re-export to chase it.
The same validator gates chat edits server-side, so an edit can never make the world
unwinnable either.
