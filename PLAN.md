# Goal
"Island Deathmatch" — an open-world 16-player multiplayer PvP deathmatch, built as a Godot 4.7.1
data-driven world (`world.json` on the rpg chunk-mode template, nothreads web export, native-playable).
One island, three zones flowing into each other: a dense urban core (parametric concrete/glass towers,
lit windows, real roads with ambient traffic, a few enterable buildings), farmland (barns, silos,
windmills, fenced fields, grazing cows/horses/sheep), and hills at the edges (terrain). One landmark
per zone (hero skyscraper / tower windmill / hill watchtower). Engine-owned multiplayer (Supabase
Realtime, 16-player room, peers on the minimap), one ranged start weapon, respawn on death, frag
counter in the HUD, day/night sky cycle. Style: stylized realistic (quaternius kits + parametric
structures + realistic audio tier).

# Files to touch
- `world.json` — the whole game as data: chunk grid (15x15 cells), terrain, zones, structures,
  landmarks, roads+traffic, populate (farm animals), weapons + start_weapon, multiplayer block,
  vars/rules/hud (frags, deaths, respawn), sky day/night cycle, director (title screen).
- `quests.json` — minimal (no quest chain; goal is a reach_cell landmark for the winnability gate).
- `audio/` — realistic-tier music + ambient beds fetched from the CC0 library.
- No game-authored `.gd` — behavior stays data so the game keeps the native tier.

# Verification approach
qgcheck (winnability) + canonical verify.mjs smoke (boot, console, frames, FEEL probes, pck/VRAM
gates) + 2-client Supabase Realtime transport loopback (Node) + targeted checks per verify-checks.md.
Specialists: Architect (macro layout, ran first), Structures (enterable interiors), Game-Feel and QA
(final gates) — findings remediated before ship.

# Out of scope
- Meshy / AI-generated assets (free tier: not provisioned) — library + parametric only, disclosed.
- Server-authoritative anti-cheat (Realtime broadcast is friends-play, shooter-authoritative + veto).
- Persistence/leaderboard beyond the match session (not requested).
