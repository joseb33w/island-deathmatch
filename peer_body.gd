extends AnimatableBody3D
## ANOTHER PLAYER, as this client sees them.
##
## Two jobs the old display-only Node3D could not do, and neither was a networking problem:
##
##   SOLID. Peers had no collision shape at all, so players walked through each other. This is an
##   AnimatableBody3D on its own layer (L_PEER) with mask 0 — it is moved by the network and never
##   pushed by the world, so a laggy remote body can never shove itself through terrain.
##
##   SHOOTABLE. `projectile.gd` resolves a hit by proximity against a list it is HANDED, and calls
##   `take_hit` on whatever it finds. Peers were simply never in that list. Being in it, and
##   answering `take_hit`, is the whole of what made them targetable — no hitboxes, no layer masks.
##
## A hit here is NOT applied locally. We do not own this player's health; their client does. All we
## do is claim it on the wire, and they decide whether to believe us (see netsync `_validate_hit`).

var peer_id := ""
var sync: Node = null
## Read by projectile.gd via `e.get("dead")` to skip corpses. Set from the owner's own death
## broadcast — we never infer it from damage we think we dealt, because we cannot see their health.
var dead := false

var _tint: StandardMaterial3D = null


func setup(id: String, ns: Node, layer: int) -> void:
	peer_id = id
	sync = ns
	collision_layer = layer
	collision_mask = 0          # network-driven: we push the player, nothing pushes us
	sync_to_physics = false     # we teleport this every frame; physics must not fight the interpolator
	var shape := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.4
	cap.height = 1.6
	shape.shape = cap
	shape.position.y = 0.85
	add_child(shape)


## Called by projectile.gd through the same `take_hit` door melee and AI damage use — which is why
## nothing in the weapon or projectile code needed to learn what a player is.
func take_hit(dmg: float) -> void:
	if dead or sync == null:
		return
	sync.report_hit(peer_id, dmg, global_position)


## Their client says they died. Go translucent and stop being a target until they say otherwise.
func set_dead(v: bool) -> void:
	dead = v
	# Recursive: the visible mesh is a GRANDCHILD (body -> avatar root -> MeshInstance), and with a
	# streamed hero_model it can be deeper still. A one-level scan would silently fade nothing.
	_fade(self, v)


func _fade(n: Node, v: bool) -> void:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if mi.material_override is StandardMaterial3D:
			var m := mi.material_override as StandardMaterial3D
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if v else BaseMaterial3D.TRANSPARENCY_DISABLED
			m.albedo_color.a = 0.35 if v else 1.0
	for c in n.get_children():
		_fade(c, v)
