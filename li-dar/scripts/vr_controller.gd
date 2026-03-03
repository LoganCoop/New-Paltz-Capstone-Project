extends XRController3D
## VR Controller for Quest 3 LiDAR Point Cloud Visualization
## Handles movement, point cloud manipulation, and UI interactions

enum ControllerSide { LEFT, RIGHT }

@export var controller_side: ControllerSide = ControllerSide.RIGHT
@export var enable_controls: bool = true
@export var movement_speed: float = 2.0
@export var rotation_speed: float = 45.0
@export var point_cloud_scale_speed: float = 0.5
@export var recenter_height: float = 1.7

var is_grip_pressed: bool = false
var is_trigger_pressed: bool = false
var point_cloud_system: Node3D
var visualizer: Node
var vr_hud: Node


func _ready() -> void:
	# Connect button signals
	button_pressed.connect(_on_button_pressed)
	button_released.connect(_on_button_released)
	
	# Find point cloud system
	point_cloud_system = get_node("/root/MainVR/PointCloudSystem")
	if point_cloud_system:
		visualizer = point_cloud_system.get_node("PointCloudVisualizer")
	
	vr_hud = get_node_or_null("/root/MainVR/XROrigin3D/XRCamera3D/VRHUD")
	print("✓ VR Controller connected to Point Cloud System (%s hand)" % ["Left" if controller_side == ControllerSide.LEFT else "Right"])


func _process(delta: float) -> void:
	if not enable_controls:
		return

	handle_movement(delta)
	handle_point_cloud_controls(delta)
	update_visual_feedback()


func _on_button_pressed(button_name: String) -> void:
	if not enable_controls:
		return
	
	print("DEBUG: Button pressed: ", button_name)  # Debug logging

	match button_name:
		"grip_click":
			is_grip_pressed = true
		
		"trigger_click":
			is_trigger_pressed = true
			recenter_player()
		
		"by_button":  # B or Y button
			if visualizer:
				visualizer.clear_point_cloud()
				show_status("Point cloud cleared")
		
		"ax_button":  # A or X button
			toggle_spatial_deduplication()

		"menu_button":
			toggle_hud_visibility()


func _on_button_released(button_name: String) -> void:
	if not enable_controls:
		return

	match button_name:
		"grip_click":
			is_grip_pressed = false
		
		"trigger_click":
			is_trigger_pressed = false


func handle_movement(delta: float) -> void:
	if not is_instance_valid(get_parent()):
		return
	
	var xr_origin = get_parent() as XROrigin3D
	if not xr_origin:
		return
	
	# All controls are mapped to the LEFT controller.
	if controller_side != ControllerSide.LEFT:
		return

	var thumbstick = get_vector2("primary")
	if thumbstick.length() <= 0.1:
		return

	# Hold grip to switch thumbstick from movement mode to rotation mode.
	if is_grip_pressed:
		if abs(thumbstick.x) > 0.2:
			xr_origin.rotate_y(deg_to_rad(-thumbstick.x * rotation_speed * delta))
		return

	# Normal movement mode.
	var forward = -xr_origin.global_transform.basis.z * thumbstick.y
	forward.y = 0
	forward = forward.normalized()

	var right = xr_origin.global_transform.basis.x * thumbstick.x
	right.y = 0
	right = right.normalized()

	var movement = (forward + right) * movement_speed * delta
	xr_origin.global_position += movement


func handle_point_cloud_controls(delta: float) -> void:
	if not visualizer:
		return

	if controller_side != ControllerSide.LEFT:
		return

	# Left grip + trigger scales point cloud up.
	if is_grip_pressed:
		var trigger_value = get_float("trigger")
		if trigger_value > 0.1 and point_cloud_system:
			var scale_change = trigger_value * point_cloud_scale_speed * delta
			var current_scale = point_cloud_system.scale
			var new_scale = current_scale + Vector3.ONE * scale_change
			new_scale = new_scale.clamp(Vector3.ONE * 0.1, Vector3.ONE * 10.0)
			point_cloud_system.scale = new_scale


func toggle_spatial_deduplication() -> void:
	if visualizer:
		visualizer.use_spatial_deduplication = not visualizer.use_spatial_deduplication
		show_status("Spatial deduplication: %s" % ["ON" if visualizer.use_spatial_deduplication else "OFF"])


func recenter_player() -> void:
	if not is_instance_valid(get_parent()):
		return

	var xr_origin = get_parent() as XROrigin3D
	if not xr_origin:
		return

	xr_origin.global_position = Vector3(0.0, 0.0, 0.0)
	if xr_origin.get_node_or_null("XRCamera3D"):
		xr_origin.get_node("XRCamera3D").position.y = recenter_height
	show_status("Recentered")


func toggle_hud_visibility() -> void:
	if vr_hud and vr_hud.has_method("toggle_visibility"):
		vr_hud.toggle_visibility()


func show_status(message: String) -> void:
	if vr_hud and vr_hud.has_method("set_status_message"):
		vr_hud.set_status_message(message)


func update_visual_feedback() -> void:
	# Update controller visual state based on button presses
	# This can be enhanced with custom hand models or particle effects
	pass


func show_stats_overlay() -> void:
	if visualizer:
		var stats = visualizer.get_statistics()
		print("=== Point Cloud Statistics ===")
		print("Total Points: ", stats["total_points"])
		print("Points Added: ", stats["points_added"])
		print("Points Deduplicated: ", stats["points_deduplicated"])
		print("Max Points: ", stats["max_points"])
