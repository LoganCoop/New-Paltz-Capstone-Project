extends XRController3D
## VR Controller for Quest 3 LiDAR Point Cloud Visualization
## Handles movement, point cloud manipulation, and UI interactions

enum ControllerSide { LEFT, RIGHT }

@export var controller_side: ControllerSide = ControllerSide.RIGHT
@export var movement_speed: float = 2.0
@export var rotation_speed: float = 45.0
@export var point_cloud_scale_speed: float = 0.5

var is_grip_pressed: bool = false
var is_trigger_pressed: bool = false
var point_cloud_system: Node3D
var visualizer: Node


func _ready() -> void:
	# Connect button signals
	button_pressed.connect(_on_button_pressed)
	button_released.connect(_on_button_released)
	
	# Find point cloud system
	point_cloud_system = get_node("/root/MainVR/PointCloudSystem")
	if point_cloud_system:
		visualizer = point_cloud_system.get_node("PointCloudVisualizer")
		print("✓ VR Controller connected to Point Cloud System (%s hand)" % ["Left" if controller_side == ControllerSide.LEFT else "Right"])


func _process(delta: float) -> void:
	handle_movement(delta)
	handle_point_cloud_controls(delta)
	update_visual_feedback()


func _on_button_pressed(button_name: String) -> void:
	match button_name:
		"grip_click":
			is_grip_pressed = true
			print("Grip pressed (%s)" % ["Left" if controller_side == ControllerSide.LEFT else "Right"])
		
		"trigger_click":
			is_trigger_pressed = true
			print("Trigger pressed (%s)" % ["Left" if controller_side == ControllerSide.LEFT else "Right"])
		
		"by_button":  # B or Y button
			if visualizer:
				visualizer.clear_point_cloud()
				print("Point cloud cleared")
		
		"ax_button":  # A or X button
			toggle_spatial_deduplication()


func _on_button_released(button_name: String) -> void:
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
	
	# Thumbstick movement (only on left controller)
	if controller_side == ControllerSide.LEFT:
		var thumbstick = get_vector2("primary")
		
		if thumbstick.length() > 0.1:
			# Forward/backward movement
			var forward = -xr_origin.global_transform.basis.z * thumbstick.y
			forward.y = 0
			forward = forward.normalized()
			
			# Strafe left/right movement
			var right = xr_origin.global_transform.basis.x * thumbstick.x
			right.y = 0
			right = right.normalized()
			
			var movement = (forward + right) * movement_speed * delta
			xr_origin.global_position += movement
	
	# Rotation (right controller)
	if controller_side == ControllerSide.RIGHT:
		var thumbstick = get_vector2("primary")
		
		if abs(thumbstick.x) > 0.3:
			# Snap rotation by thumbstick left/right
			xr_origin.rotate_y(deg_to_rad(-thumbstick.x * rotation_speed * delta))


func handle_point_cloud_controls(delta: float) -> void:
	if not visualizer:
		return
	
	# Right grip + trigger: Scale point cloud
	if controller_side == ControllerSide.RIGHT and is_grip_pressed:
		var trigger_value = get_float("trigger")
		
		if trigger_value > 0.1:
			var scale_change = trigger_value * point_cloud_scale_speed * delta
			if point_cloud_system:
				var current_scale = point_cloud_system.scale
				var new_scale = current_scale + Vector3.ONE * scale_change
				new_scale = new_scale.clamp(Vector3.ONE * 0.1, Vector3.ONE * 10.0)
				point_cloud_system.scale = new_scale


func toggle_spatial_deduplication() -> void:
	if visualizer:
		visualizer.use_spatial_deduplication = not visualizer.use_spatial_deduplication
		print("Spatial deduplication: ", "ON" if visualizer.use_spatial_deduplication else "OFF")


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
