# Game-Feel / Mobile-UX report — Island Deathmatch (Godot 4.7.1 nothreads web export)

**VERDICT: PASS (0 P0) — 3 ❗P1 must-fix, 4 ⚠️ polish**

Method: drove the real export from `/workspace/out` (static server + `/godot-assets/*` proxy), signed in with both test accounts, portrait **390x844** and landscape **860x400**. All gameplay input verified through the **real touch path** (CDP `Input.dispatchTouchEvent`, not mouse/keyboard emulation) except where noted. Evidence frames in `/tmp/feel/*.png`; full console logs in `/tmp/feel/logs*.txt`. Cross-checked against the coordinator's earlier 2-client captures in `/workspace/verify/mp-*.png`.

---

## ❗ P1 — must fix

### 1. DEATHS counter is dumped at the bottom screen edge in portrait (declared `top_right`)
- **Symptom:** in portrait the "DEATHS 0" readout renders at the very bottom edge of the screen, directly below the ATTACK button (under the firing thumb), while FRAGS stays top-center. Reproduced **3/3 boots** at 390x844; console logs `GOGI_HUD_FIT deaths moved 518,47 -> 518,1508` on the second relayout pass every time (first pass places it correctly at 465,47). Landscape is fine (both counters top). Evidence: `p-spawn-toast.png`, `crop-deaths.png` vs `l-hud.png`.
- **Root cause:** `world.json` declares `deaths: pos top_right`, but at a 720-unit-wide portrait viewport the top strip is crowded (stats block + FRAGS label at x372 + the minimap's 187px square at top-right). `rules.gd _place_clear()`'s sideways escape is blocked by the FRAGS rect, so it falls through to the vertical candidate list and commits the bottom-most spot (y=1508/1558). No `UNRESOLVED` log fires because the overlap *was* technically resolved.
- **Fix direction:** treat FRAGS/DEATHS as one clustered readout (e.g. a single top-center "FRAGS n  ·  DEATHS n" label, or stack DEATHS directly under FRAGS), or bound `_place_clear`'s vertical escape for top-anchored items to the top band, or exclude the minimap band by placing `top_right` readouts *below* it like the STABLE/WEAPON> stack already does.

### 2. Remote players get NO near-camera fade — a point-blank peer fills the frame like a popup
- **Symptom:** another player standing against your camera fills the bottom half of the screen with a giant face/torso (coordinator's 2-client capture `verify/mp-A-aiming.png`: a T-posed peer wall-to-wall across the lower ~45% of the frame). In a 16-player melee-range deathmatch, an opponent pressing the lens is the *common* case, not the corner case.
- **Root cause (code-confirmed):** `main.gd _fade_near_camera_enemies()` iterates `streamer.enemies` only; `enemy.gd set_camera_near()` (with its hysteresis band) exists precisely for this, but `peer_body.gd` has no `set_camera_near` and its only fade path is death translucency (`set_dead`). The SpringArm masks world-only, so it never pulls back off a peer either.
- **Fix direction:** in `_fade_near_camera_enemies()`, also walk the netsync peer bodies and apply the same distance/hysteresis fade (add a `set_camera_near`/fade to `peer_body.gd`, reusing enemy.gd's `CAM_FADE_NEAR`/0.45·body_h logic).

### 3. Camera pull-in near solids collapses to "walled" frames (giant head, or player invisible over a ground smear)
- **Symptom A:** standing next to a fence with the camera across it, one right-half look-drag left the camera ~1.4–2m from the hero — the head fills ~40% of the frame and stays that way while you stand there (`p-after-touchlook.png`). This reproduces the frame the coordinator saw; it is **situational, not chronic** (a full 8-step 360° orbit in the open at spawn produced 8/8 clean frames, `c-orbit-spawn-*.png`).
- **Symptom B:** orbiting while pressed against a structure (watchtower/silo at 37,76), **2 of 4** orbit stops rendered *only grass* with the player completely invisible (`c-wall-orbit-1/2.png`) — the avatar hard-hides at cam-dist < 1.35m with no in-between, so the mid-collapse band (1.4–3m) shows either a full-frame head or an empty ground smear. Both recover as soon as you orbit/move on (hence not P0).
- **Root cause:** SpringArm world-collision pull-in is instant and unmitigated; the avatar-hide guard in `main.gd _process` is a binary `visible = cd > 1.35`.
- **Fix direction:** progressively fade (transparency) the hero from ~3m down instead of a 1.35m hard hide; optionally add a min-arm floor with a pivot lift when blocked, so a blocked camera rides up over the obstacle rather than into the player's skull.

---

## ⚠️ Polish

- **Pitch extremes are both degenerate poses.** Pitch min (−1.05) is still a scalp-and-road view (`e-field-pitchmin.png`); pitch max (+0.25) grounds the SpringArm to ~3m — in the open it's a usable low shot with horizon (`e-field-pitchmax.png`), but next to the spawn road it produced a frame that is ~40% featureless black road seen edge-on with no player visible (`c-pitch-max.png`). The code comment says the range was already narrowed for exactly this; consider a slow auto-recenter toward −0.4 while moving, or shortening the arm on pitch-up instead of letting it ground-collide.
- **HP bar reads as a red underline of the "Inv:" text.** It sits flush under (touching descenders of) the third stats line with no gap and no label (`crop-statsblock.png` / `crop-statsblock-land.png`, both orientations). Add ~10px gap between the stats block and the bar (bar_y is `mt+100` but three 22px lines run to ~118).
- **RPG-template stats clutter in a PvP deathmatch.** Top-left shows `Lv/XP/Gold`, `Wpn: Scout Rifle`, `Inv: Rusty Sword, [Scout Rifle]` on a 390px-wide phone. It's engine furniture, not debug text, but XP/Gold/Inv are meaningless in this mode and the bracket notation looks developer-facing. The world already uses `hide_hud` for buttons — consider hiding these lines too (keep HP).
- **Default framing is tight.** At the default pitch (−0.55) the chibi hero occupies ~30–35% of screen height in portrait (`c-open-field.png` baseline, no collision), hiding a lot of the battlefield ahead in a game about spotting other players. Deliberate style, but a touch more distance or a lower head-pivot would help portrait.

---

## ✅ Verified passing

- **Touch controls (P0 class — clean):** real-touch left-half joystick moved the player 25.1m portrait / 11.8m landscape; real-touch right-half drag orbits the camera; ATTACK tap fired the weapon (`GOGI_RULE_FIRED muzzle` + shake); JUMP tap lifted the player 1.67m. One-handed layout: single right-thumb column (JUMP/USE/ATTACK), joystick anywhere in the left half. Button-vs-gesture ownership is correct — drags starting on a HUD button do not orbit the camera (observed live).
- **Transient vs persistent UI:** "Downtown" region entry is a 2.2s toast that was **gone 4s later** (`p-region-toast.png` → `p-region-toast-gone.png`); welcome toast and the 8s control-hint subtitle both fade (`p-spawn-toast.png` → `p-spawn-later.png`). No region name or stale status is ever pinned.
- **No debug text ships:** `mp_debug`/`hud_debug` overlays are gated behind `?mpdebug=1`/`?hudgrid=1` URL flags; all `GOGI_*` telemetry goes to the JS console, not the screen.
- **Damage/feedback is non-modal:** hits are shake (0.08 fire / 0.25 hurt) + red flash + sound via rules; death is a "Fragged - respawning..." toast + auto-respawn — no dialogs anywhere. Coordinator's `mp-B-after-hits.png` (HP 66/100) shows a normal HUD, no popup.
- **Landscape 860x400 relayout:** all controls on-screen and thumb-side, FRAGS + DEATHS both top, stats readable, minimap square; the HUD grid log confirms rows fit (`bh 94, rows 345/457/568`).
- **Camera basics:** yaw orbit works both directions; pitch is clamped (never stares past ±limits); 360° orbit in open ground never clipped inside a mesh; no full-frame mesh on attacks (ranged weapon, projectile + spark feedback).
- **Auth gate on phone:** centered 320px box, 44pt fields, worked at the documented tap points. (One benign web console error: `setSelectionRange` on the email input — engine/browser quirk, no user impact observed.)

## Could not verify (sandbox limits)
- True **multi-touch** feel (simultaneous move + look + button with 2–3 fingers) — single synthetic touch stream only; the index-based `move_idx/look_idx/_gui_touch_idx` code is correct by inspection.
- Real-device **notch/safe-area** insets (`_safe_insets` returns zero on web; code path untestable here) and haptics.
- Frame pacing / worst-frame ms on a real phone GPU (software-GL numbers are meaningless).
- Known/accepted (not re-filed): KayKit Ranger fallback avatar; remote peers' animation state not network-synced (the T-pose in `mp-A-aiming.png` is that limitation — but its *near-camera framing* is P1 #2 above).
