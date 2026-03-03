extends Node3D
## Point Cloud Visualizer for LiDAR Data
## Creates and updates a mesh-based point cloud from incoming UDP packets

@export var max_points: int = 50000
@export var point_scale: float = 0.5
@export var scale_meters: float = 0.01
@export var use_spatial_deduplication: bool = true
@export var voxel_size: float = 0.03
@export var min_distance_meters: float = 0.1
@export var max_distance_meters: float = 5.0
@export var min_strength: int = 100
@export var flip_x: bool = true
@export var flip_y: bool = true
@export var ignore_orientation: bool = false
@export var orientation_smoothing: float = 0.5
@export var max_distance_jump: float = 0.15
@export var distance_median_window: int = 5
@export var use_pos_field: bool = true

# Color gradient for distance visualization
@export var min_color: Color = Color(0.0, 0.0, 1.0)  # Blue for close
@export var max_color: Color = Color(1.0, 0.0, 0.0)  # Red for far

var mesh_instance: MeshInstance3D
var array_mesh: ArrayMesh
var vertices: PackedVector3Array = PackedVector3Array()
var colors: PackedColorArray = PackedColorArray()
var mesh_needs_update: bool = false

# Spatial deduplication
var occupied_voxels: Dictionary = {}  # Vector3i -> int (vertex index)
var voxel_colors: Dictionary = {}     # Vector3i -> Color

# Smoothing and filtering
var smoothed_orientation: Quaternion = Quaternion.IDENTITY
var has_smoothed_orientation: bool = false
var calibration: Quaternion = Quaternion.IDENTITY
var has_calibration: bool = false
var distance_samples: Array[float] = []

# Statistics
var total_points: int = 0
var points_added: int = 0
var points_deduplicated: int = 0


func _ready() -> void:
	# Create mesh instance for point cloud
	mesh_instance = MeshInstance3D.new()
	add_child(mesh_instance)
	
	# Create array mesh
	array_mesh = ArrayMesh.new()
	mesh_instance.mesh = array_mesh
	
	# Find UDP receiver and connect signal
	var udp_receiver = get_parent().get_node("UDPReceiver")
	if udp_receiver:
		udp_receiver.packet_received.connect(_on_packet_received)
		print("✓ Point Cloud Visualizer connected to UDP Receiver")
	else:
		push_error("UDP Receiver not found!")
	
	# Set up material (will be created separately)
	setup_material()


func setup_material() -> void:
	# Load or create material for point rendering
	var material = load("res://materials/point_cloud_material.tres")
	
	if material == null:
		# Fallback: Create a basic material
		material = StandardMaterial3D.new()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.vertex_color_use_as_albedo = true
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		material.point_size = 20.0
	
	mesh_instance.material_override = material


func _on_packet_received(packet_data: Dictionary) -> void:
	# Extract sensor data
	var tfluna = packet_data["tfluna"]
	var bno055 = packet_data["bno055"]
	
	# Get distance and filter
	var distance_cm: float = tfluna["distance_cm"]
	var distance_m: float = distance_cm / 100.0
	var strength: int = tfluna["strength"]
	
	# Apply distance filtering
	if distance_m < min_distance_meters or distance_m > max_distance_meters:
		return
	
	if strength < min_strength:
		return
	
	# Median filter for distance
	distance_samples.append(distance_m)
	if distance_samples.size() > distance_median_window:
		distance_samples.pop_front()
	
	var filtered_distance = calculate_median(distance_samples)
	
	# Check for distance jumps
	if distance_samples.size() > 1:
		var prev_distance = distance_samples[-2]
		if abs(filtered_distance - prev_distance) > max_distance_jump:
			return
	
	# Get orientation from quaternion
	var quat = Quaternion(
		bno055["qx"],
		bno055["qy"],
		bno055["qz"],
		bno055["qw"]
	)
	
	# Apply calibration and smoothing
	if not has_calibration:
		calibration = quat.inverse()
		has_calibration = true
	
	quat = calibration * quat
	
	if orientation_smoothing > 0.0 and has_smoothed_orientation:
		smoothed_orientation = smoothed_orientation.slerp(quat, 1.0 - orientation_smoothing)
	else:
		smoothed_orientation = quat
		has_smoothed_orientation = true
	
	# Calculate point position
	var point_pos: Vector3
	
	# Check if packet has pre-calculated position
	if use_pos_field and packet_data.has("pos_m"):
		var pos_array = packet_data["pos_m"]
		if typeof(pos_array) == TYPE_ARRAY and pos_array.size() == 3:
			point_pos = Vector3(pos_array[0], pos_array[1], pos_array[2]) * scale_meters
		else:
			# Fallback to orientation-based calculation
			point_pos = calculate_point_from_orientation(filtered_distance)
	else:
		point_pos = calculate_point_from_orientation(filtered_distance)
	
	# Apply flips
	if flip_x:
		point_pos.x = -point_pos.x
	if flip_y:
		point_pos.y = -point_pos.y
	
	# Calculate color based on distance
	var color = calculate_point_color(filtered_distance, strength)
	
	# Add point to cloud
	add_point(point_pos, color)


func calculate_point_from_orientation(distance_m: float) -> Vector3:
	var direction: Vector3
	
	if ignore_orientation:
		# Simple forward direction
		direction = Vector3.FORWARD
	else:
		# Use smoothed orientation
		direction = smoothed_orientation * Vector3.FORWARD
	
	return direction * distance_m * scale_meters


func calculate_median(samples: Array[float]) -> float:
	if samples.size() == 0:
		return 0.0
	
	var sorted = samples.duplicate()
	sorted.sort()
	
	var mid: int = sorted.size() >> 1  # Bit shift for integer division
	if sorted.size() % 2 == 0:
		return (sorted[mid - 1] + sorted[mid]) / 2.0
	else:
		return sorted[mid]


func calculate_point_color(distance_m: float, strength: int) -> Color:
	# Normalize distance to 0-1 range
	var t = (distance_m - min_distance_meters) / (max_distance_meters - min_distance_meters)
	t = clamp(t, 0.0, 1.0)
	
	# Interpolate between min and max color
	var base_color = min_color.lerp(max_color, t)
	
	# Modulate by strength (brightness)
	var strength_factor = remap(strength, min_strength, 1000.0, 0.5, 1.0)
	strength_factor = clamp(strength_factor, 0.5, 1.0)
	
	return base_color * strength_factor


func add_point(point_pos: Vector3, color: Color) -> void:
	if use_spatial_deduplication:
		add_point_with_deduplication(point_pos, color)
	else:
		add_point_simple(point_pos, color)


func add_point_simple(point_pos: Vector3, color: Color) -> void:
	if vertices.size() >= max_points:
		# Remove oldest point
		vertices.remove_at(0)
		colors.remove_at(0)
	
	vertices.append(point_pos)
	colors.append(color)
	points_added += 1
	mesh_needs_update = true


func add_point_with_deduplication(point_pos: Vector3, color: Color) -> void:
	# Calculate voxel grid position
	var voxel = Vector3i(
		int(floor(point_pos.x / voxel_size)),
		int(floor(point_pos.y / voxel_size)),
		int(floor(point_pos.z / voxel_size))
	)
	
	# Check if voxel is occupied
	if occupied_voxels.has(voxel):
		# Update existing point color (average with new color)
		var existing_index = occupied_voxels[voxel]
		colors[existing_index] = colors[existing_index].lerp(color, 0.3)
		points_deduplicated += 1
		mesh_needs_update = true
		return
	
	# Add new point
	if vertices.size() >= max_points:
		# Remove oldest point and its voxel entry
		var old_pos = vertices[0]
		var old_voxel = Vector3i(
			int(floor(old_pos.x / voxel_size)),
			int(floor(old_pos.y / voxel_size)),
			int(floor(old_pos.z / voxel_size))
		)
		occupied_voxels.erase(old_voxel)
		vertices.remove_at(0)
		colors.remove_at(0)
		
		# Update all voxel indices
		for v in occupied_voxels.keys():
			occupied_voxels[v] -= 1
	
	var new_vertex_index = vertices.size()
	vertices.append(point_pos)
	colors.append(color)
	occupied_voxels[voxel] = new_vertex_index
	points_added += 1
	total_points = vertices.size()
	mesh_needs_update = true


func _process(_delta: float) -> void:
	if mesh_needs_update:
		update_mesh()
		mesh_needs_update = false


func update_mesh() -> void:
	if vertices.size() == 0:
		return
	
	# Clear existing mesh
	array_mesh.clear_surfaces()
	
	# Create arrays for mesh
	var arrays = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_COLOR] = colors
	
	# Add surface to mesh with PRIMITIVE_POINTS
	array_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_POINTS, arrays)


func clear_point_cloud() -> void:
	vertices.clear()
	colors.clear()
	occupied_voxels.clear()
	array_mesh.clear_surfaces()
	points_added = 0
	points_deduplicated = 0
	total_points = 0
	has_smoothed_orientation = false
	has_calibration = false
	distance_samples.clear()


func get_statistics() -> Dictionary:
	return {
		"total_points": total_points,
		"points_added": points_added,
		"points_deduplicated": points_deduplicated,
		"max_points": max_points
	}
