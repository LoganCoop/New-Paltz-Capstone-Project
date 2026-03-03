extends Control
## Debug HUD for VR LiDAR Visualization
## Displays real-time statistics about point cloud and UDP reception

@onready var stats_label: Label = $StatsLabel
@onready var fps_label: Label = $FPSLabel

var udp_receiver: Node
var visualizer: Node
var update_interval: float = 0.5
var time_since_update: float = 0.0


func _ready() -> void:
	# Find components
	var point_cloud_system = get_node_or_null("/root/MainVR/PointCloudSystem")
	if point_cloud_system:
		udp_receiver = point_cloud_system.get_node_or_null("UDPReceiver")
		visualizer = point_cloud_system.get_node_or_null("PointCloudVisualizer")
	
	# Position HUD
	position = Vector2(20, 20)
	size = Vector2(400, 300)


func _process(delta: float) -> void:
	# Update FPS every frame
	if fps_label:
		fps_label.text = "FPS: %d" % Engine.get_frames_per_second()
	
	# Update stats at intervals
	time_since_update += delta
	if time_since_update >= update_interval:
		update_stats()
		time_since_update = 0.0


func update_stats() -> void:
	if not stats_label:
		return
	
	var text = "=== LiDAR VR Statistics ===\n\n"
	
	# UDP Receiver stats
	if udp_receiver:
		var udp_stats = udp_receiver.get_statistics()
		text += "UDP RECEIVER:\n"
		text += "  Status: %s\n" % ("Active" if udp_stats["is_listening"] else "Inactive")
		text += "  Port: %d\n" % udp_stats["port"]
		text += "  Packets Received: %d\n" % udp_stats["packets_received"]
		text += "  Packets Dropped: %d\n" % udp_stats["packets_dropped"]
		text += "  Last Sender: %s\n" % udp_stats["last_sender"]
		if udp_stats["last_error"]:
			text += "  ⚠️ Error: %s\n" % udp_stats["last_error"]
		text += "\n"
	
	# Point Cloud visualizer stats
	if visualizer:
		var vis_stats = visualizer.get_statistics()
		text += "POINT CLOUD:\n"
		text += "  Total Points: %d / %d\n" % [vis_stats["total_points"], vis_stats["max_points"]]
		text += "  Points Added: %d\n" % vis_stats["points_added"]
		text += "  Deduplicated: %d\n" % vis_stats["points_deduplicated"]
		var percent = 0.0
		if vis_stats["max_points"] > 0:
			percent = (float(vis_stats["total_points"]) / vis_stats["max_points"]) * 100.0
		text += "  Capacity: %.1f%%\n" % percent
	
	stats_label.text = text
