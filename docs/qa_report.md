# QA Report — Island Deathmatch (Godot 4.7.1 web export, chunk-mode world.json)

**VERDICT: PASS (0 P0, 1 P1)**

Adversarial pass over `/workspace/out` served locally (godot-assets proxied), driven signed-in through the REAL
auth gate with the two test accounts, across 8 fresh browser sessions (single-client world tours, 2×two-client
PvP sessions, 3 vehicle sessions). All interactive evidence below is from **real input driving the real game**
(keyboard/joystick/drag/HUD buttons + `gogiGetPlayer`/`gogiSetTime`/`gogiBoard` hooks), with position/yaw
telemetry and screenshots I inspected myself. Probe sources: `/workspace/verify/qa_*.mjs`, logs `/tmp/qa2.log
/tmp/qa3.log /tmp/qamp.log /tmp/qamp2.log /tmp/qaveh*.log`, frames `/workspace/verify/qa*.png`.

---

## ❗ P1 (must-fix)

### P1-1 Rider clips through the sedan roof when driving a boardable car
- **Symptom:** boarding the Sedan (world `vehicles[0]`, spawn road) seats the player with the entire torso +
  head poking through the closed cab's roof — reads as "sitting on top of the car". Evidence:
  `qa5-boarded.png`, `qa5-driving.png`.
- **Repro:** spawn → walk ~15 m north to the red Sedan at (5,52) → USE/board → look from behind.
- **What works:** boarding via the real USE path ✔, DISMOUNT button appears ✔, car drives (5–14 m deltas) ✔,
  dismount works once the enter-choreography reaches DRIVING ✔ (`/tmp/qaveh4.log`: veh true→false on button).
- **Likely cause + fix:** chibi KayKit rig is taller than the car cab; `vehicle.gd` seat pose keeps the driver
  visible in a closed-cab profile. Either hide the driver while seated in closed cars (exit() already restores
  `driver.visible = true`, so a hide path exists) or lower the seat point / use an open profile.
- Not gameplay-blocking (cars are secondary to the deathmatch), but it's the kind of clip players screenshot.

---

## ✅ Verified (with the delta/screenshot that proves it)

| # | Check | Result / evidence |
|---|-------|-------------------|
| 1 | Boot, canvas, console | Boots in ~15 s; signed-in sessions ran 5–8 min each with **zero** page errors / SCRIPT ERROR / Parse Error (`ERROR LINES: []` in qa2/qa3/mp logs). Cert/wss noise absent with the sandbox flags. |
| 2 | Auth gate | Real sign-in driven 8×; `GOGI_AUTH gate passed` every session. |
| 3 | Rule layer alive | Signed-in: `GOGI_RULE_FIRED welcome` (start), `muzzle` (weapon_fired), `hitfx` (hit_by_player, cross-client), `GOGI_TIME` on set_time. The canonical verify's single FAIL ("RULE LAYER NEVER RAN") is its inability to pass the auth gate — an artifact, not a build bug. |
| 4 | Movement + facing | KeyW deltas 12.3 m / calibrated speed 5.2–5.6 m/s; character shows its BACK walking away, FACE after 180° orbit (`qa3-lookback-west.png`). No moonwalk. |
| 5 | Camera orbit | Right-half drag: yaw delta measured every session (−90.3 px/rad, repeatable); vertical drag pitches to horizon (`qa3-*-up.png`). Never stuck staring at the floor. |
| 6 | Input-binding sanity | No `[input]` fire binding; fire ONLY on the ATTACK HUD button. Across ~100 drags/moves in 8 sessions: zero unintended `muzzle` fires, HP stayed 100, FRAGS 0. No auto-fire-on-look. |
| 7 | Weapon fires + in hand | ATTACK tap → `GOGI_RULE_FIRED muzzle`; rifle stock gripped in the right fist (zoom crop `zz-hand.png`) — attached to the hand bone, moves with the character, not floating. |
| 8 | Three distinct zones | **City**: dense tower canyons, window-grid facades, asphalt grid (`qa-city-street.png`, `qa-city-approach.png`). **Farmland**: barns/silos/water-towers/fence-lined fields, grass+dirt (`qa-weapon-front.png`, `qa-animals-*.png`). **Hills**: rolling rock/grass, dead trees, boulders, logs (`qa-hills-east.png`, `qa3-watchtower-day-down.png`). Grounds are real presets (asphalt/concrete/grass/dirt/rock), not flat colour. |
| 9 | World density | 225/225 cells authored, 124 parametric towers (concrete/glass, taper/setback, lit windows), 37 road cells, 613 farm props, ~4.2 placed items/cell + scatter. Reads as a place at street level. |
| 10 | Cars actually drive | Standing at the crossroads: a taxi + white car DROVE INTO frame between `qa-cars-0.png` → `qa-cars-1.png` (7 s apart, static camera). Real q_cars models on the streets. |
| 11 | Animals wander | Sheep visibly displaced between `qa-animals-0/1.png` (9 s apart, static camera) at cell [-2,4]. |
| 12 | Enterable hero skyscraper | Walked through the south door of [1,1] with USE: z telemetry 24.5 → 22.1 → **19.7** (inside the 11×11 footprint, wall face at z=21.5), floor slab underfoot (y +0.22), lit interior, walked back out. (`/tmp/qa2.log` "LOBBY entered: true", `qa2-lobby-inside/look.png`.) 3 more interiors authored at [-1,-1],[1,-1],[-2,1] (same mechanism, data-verified). |
| 13 | Landmarks | Hero 80 m glass tower dominates the plaza + glows at night (`zz-plaza-night.png`); TowerWindmill cluster at [-4,-4] — three bladed, textured windmill towers (`qa2-landscape.png`); watchtower at [7,0] — tall tapering steel silhouette, sunset-lit edge, visible from ~100 m during the hills walk (`zz-tower.png`, `qa-hills-east.png`). |
| 14 | Day/night cycle | Driven deterministically via `gogiSetTime` (never wall-clock waits): bright day city (`qa-city-street.png`) vs dark night with warm lit window rows (`qa-plaza-night.png`); natural cycle also observed reaching a real sunset gradient sky (`qa3-watchtower-day-up.png`). Night stays READABLE (player/ground/structures distinguishable, moonlit blue — `qa2-watchtower-night.png`); day has 0.0% clipped pixels (verify luma). Sky is a real gradient panorama — no grey ceiling in pitch-up shots. |
| 15 | World persistence / boundary (#16) | Walked EAST past the last cell: invisible wall pins the player at x=127 (grid edge 120) — contained, never falls off. Looking back from the boundary the island still renders (downtown skyline via far-proxies, `qa3-lookback-west-up.png`); minimap paints ocean east of the player (`qa3-ocean-east.png`), terrain falls away seaward. World never vanished at any point in ~700 m of walking. |
| 16 | Mobile fill | Portrait 390×844 and landscape 860×400 both fill all four corners, no letterbox; HUD refits live (FRAGS top-center both orientations, DEATHS auto-moved clear of the minimap, buttons inside the rect, no overlaps): `qa2-portrait-final.png`, `qa2-landscape.png`. |
| 17 | Multiplayer visibility | Two real signed-in clients, same room (`?room=` join): `peers=1 bodies=1` BOTH directions; remote avatar renders as the full textured Ranger (not a blob/T-pose — local idle loop confirmed), `qa-mp-A-view.png`. |
| 18 | Minimap peer blips | With 25 m separation, B appears on A's minimap as a distinct body-colour circle south of A's arrow (`zz-mm-sep-big.png`); cyan square = vehicle marker (verified against minimap.gd palette). |
| 19 | PvP damage path | A's shot → hit claim → B validated it → `GOGI_RULE_FIRED hitfx` on B (shake+hurt through the real `take_damage` door). Damage feedback is NON-modal (shake + directional arc + sound; death rule is toast + auto-respawn, no modal banner). |
| 20 | Vehicles boardable | Both `vehicles[]` are the same `car` profile; Sedan boarded/driven/dismounted (see P1-1 for the visual). |
| 21 | Winnability / goal | qgcheck green (world winnable, 225 areas); goal `reach_cell [7,0]` is a soft nav objective by design (no win-screen popup). |
| 22 | Native tier | `manifest.json`: `webOnly: false`, requires rules/hud/pvp — native-playable data build. ✔ |
| 23 | Audio presence | AudioManager + bus layout + attack/death/door SFX + battle music + wind/crickets ambients all in the export; `play_sfx("attack")` on the fire path. (Playback itself unverifiable in the muted container.) |
| 24 | Character sourcing | KayKit Ranger for player/peers = **disclosed** Meshy-unavailable fallback (free tier; recorded in `world.json.character_source`) → noted, not flagged per policy. Player/peers/animals all render textured (the static flat-tint lint does not manifest). |
| 25 | Spawn | On the south arterial, clear ground, not inside geometry (`qa-spawn.png`), city + hero tower in view up the road as designed. |

---

## ⚠️ Warns / polish (no action strictly required to ship, but worth doing)

1. **Kill→FRAGS→respawn loop not E2E-provable in this container.** 58/60 point-blank validated shots were
   vetoed by the target with `GOGI_MP_HIT rejected ... age>0.40` — the SwiftShader clock jank the coordinator
   disclosed (claims arrive stale at 4–6 Hz net loops; 1/60 landed → hitfx fired). Every component is
   individually verified: transport ✔, hit→take_damage ✔, `score`/`down` rules loaded + rule layer alive ✔,
   wiring read in code (`netsync.killed → player_killed → score`; death broadcast carries `_last_hit_by`).
   **Recommendation:** one 2-phone real-device smoke of a full frag; if real networks also show rejections,
   raise `HIT_MAX_AGE` (netsync.gd:142, 0.40 s) toward ~0.8 s together with the position-history window —
   0.40 s leaves little headroom for poor mobile links.
2. **Watchtower's red sign light not visible in my night frame** (`qa3-watchtower-night.png`, shot from the
   tower base — the light may be top-mounted/out of frame, and software-GL dims omnis). Structure + sunset-lit
   taper confirmed. Worth one look at night from 30–40 m on the preview.
3. **Rendered ocean surface not seen from the boundary** — minimap paints water east and the terrain falls
   away, but no visible water plane in my edge frames (`qa3-ocean-east.png` shows the pale falloff slope +
   sky). If the sea should read from the hills, check the water plane extent vs the island falloff distance.
4. **Off-grid skirt terrain renders bare pale-grey** (no grass tint) — only visible past the boundary wall
   (`qa2-edge-*.png`), so cosmetic.
5. **One-weapon fiction leaks template RPG defaults:** inventory ships a "Rusty Sword" (HUD `Inv:` line) and a
   landscape "WEAPON >" cycle button lets players swap to melee; HUD also shows Lv/XP/Gold, meaningless in a
   deathmatch. Consider stripping the sword + hiding the RPG stat line for fiction polish.
6. **DISMOUNT button silently no-ops during the multi-second boarding choreography** (`vehicle.exit()` requires
   S_DRIVING); under load my first clicks did nothing. Fine once settled; consider queueing the exit.
7. **Perf:** canonical verify measured a worst frame of 117 ms (device-independent one-frame stall, likely a
   streaming build spike). Average fps is a container artifact; the spike is real but mild.
8. **Remote peers idle-animate while moving** — disclosed engine limitation (anim state not synced). Visible
   as gliding peers; acceptable per disclosure.
9. Canonical `verify.mjs` exits 1 solely on "RULE LAYER NEVER RAN" — auth-gate artifact (see ✅ #3); its FEEL
   probes all skipped for the same reason. Signed-in probes supersede them.

## Could not verify (sandbox limits)
Real-GPU fidelity/colour, audio playback, touch feel, real-network hit-claim latency (see Warn 1), 16-player
scale (2 clients tested), native iOS runtime, cross-device persistence.

---

**Bottom line:** the island is a real, dense, three-zone place that streams, persists, and cycles day/night;
combat inputs, PvP visibility, blips, HUD, boundary and landmarks all check out with hard deltas. Fix P1-1
(rider-through-roof), ideally sanity-check the frag loop on real devices, and ship.
