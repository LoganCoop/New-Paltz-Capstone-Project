extends Node3D
## In-headset 3D HUD for status, point-cloud metrics, UDP health, and control instructions.

@onready var stats_label: Label3D = $StatsLabel3D
@onready var help_label: Label3D = $HelpLabel3D
@onready var status_label: Label3D = $StatusLabel3D

var udp_receiver: Node
var visualizer: Node
var update_interval: float = 0.4
var time_since_update: float = 0.0
var status_clear_time: float = 0.0


func _ready() -> void:
	var point_cloud_system = get_node_or_null("/root/MainVR/PointCloudSystem")
	if point_cloud_system:
		udp_receiver = point_cloud_system.get_node_or_null("UDPReceiver")
		visualizer = point_cloud_system.get_node_or_null("PointCloudVisualizer")

	update_help_text()
	set_status_message("HUD Ready")


func _process(delta: float) -> void:
	time_since_update += delta
	if time_since_update >= update_interval:
		update_stats()
		time_since_update = 0.0

	if status_clear_time > 0.0 and Time.get_ticks_msec() / 1000.0 >= status_clear_time:
		status_label.text = ""
		status_clear_time = 0.0


func update_help_text() -> void:
	help_label.text = (
		"LEFT CONTROLLER\n"
		+ "Stick: Move\n"
		+ "Grip + Stick X: Turn\n"
		+ "Grip + Trigger: Scale +\n"
		+ "Trigger Click: Recenter\n"
		+ "X/A: Toggle Dedup\n"
		+ "Y/B: Clear Cloud\n"
		+ "Menu: Show/Hide HUD"
	)


func update_stats() -> void:
	var fps = Engine.get_frames_per_second()
	var lines: Array[String] = []
	lines.append("LiDAR VR HUD")
	lines.append("FPS: %d" % fps)

	if udp_receiver:
		var udp_stats = udp_receiver.get_statistics()
		var now_s = Time.get_ticks_msec() / 1000.0
		var age = "n/a"
		if udp_stats["last_packet_time"] > 0.0:
			age = "%.2fs" % max(now_s - float(udp_stats["last_packet_time"]), 0.0)
		lines.append("UDP: %s" % ("Active" if udp_stats["is_listening"] else "Inactive"))
		lines.append("Packets: %d (drop %d)" % [udp_stats["packets_received"], udp_stats["packets_dropped"]])
		lines.append("Last packet: %s" % age)
		if String(udp_stats["last_sender"]).length() > 0:
			lines.append("Sender: %s" % udp_stats["last_sender"])

	if visualizer:
		var vis_stats = visualizer.get_statistics()
		lines.append("Points: %d / %d" % [vis_stats["total_points"], vis_stats["max_points"]])
		lines.append("Added: %d" % vis_stats["points_added"])
		lines.append("Deduped: %d" % vis_stats["points_deduplicated"])

	stats_label.text = "\n".join(lines)


func set_status_message(message: String, seconds: float = 1.5) -> void:
	status_label.text = message
	status_clear_time = Time.get_ticks_msec() / 1000.0 + seconds


func toggle_visibility() -> void:
	visible = not visible
	if visible:
		set_status_message("HUD On")
