extends Node
## UDP Receiver for LiDAR Data
## Receives JSON packets containing TFLuna distance data and BNO055 orientation data

signal packet_received(packet_data: Dictionary)
signal marker_packet_received(marker_data: Dictionary)

@export var port: int = 5005
@export var debug_overlay: bool = true
@export var max_timestamp_delta: float = 0.05

var udp_socket: PacketPeerUDP
var is_listening: bool = false
var packet_count: int = 0
var last_packet_time: float = 0.0
var last_sender: String = ""

# Packet statistics
var packets_received: int = 0
var packets_dropped: int = 0
var last_error: String = ""


func _ready() -> void:
	start_listening()
	

func start_listening() -> void:
	udp_socket = PacketPeerUDP.new()
	var result = udp_socket.bind(port)
	
	if result == OK:
		is_listening = true
		print("✓ UDP Receiver started on port ", port)
	else:
		is_listening = false
		last_error = "Failed to bind to port %d: Error %d" % [port, result]
		push_error(last_error)


func stop_listening() -> void:
	if udp_socket:
		udp_socket.close()
		is_listening = false
		print("UDP Receiver stopped")


func _process(_delta: float) -> void:
	if not is_listening or not udp_socket:
		return
	
	# Process all available packets
	while udp_socket.get_available_packet_count() > 0:
		var packet = udp_socket.get_packet()
		var sender_ip = udp_socket.get_packet_ip()
		var sender_port = udp_socket.get_packet_port()
		
		if packet.size() > 0:
			process_packet(packet, sender_ip, sender_port)


func process_packet(packet: PackedByteArray, sender_ip: String, sender_port: int) -> void:
	var json_string = packet.get_string_from_utf8()
	
	# Try to parse JSON
	var json = JSON.new()
	var error = json.parse(json_string)
	
	if error != OK:
		packets_dropped += 1
		last_error = "JSON Parse Error at line %d: %s" % [json.get_error_line(), json.get_error_message()]
		if debug_overlay:
			print("UDP Parse Error: ", last_error)
		return
	
	var data = json.get_data()
	
	if typeof(data) != TYPE_DICTIONARY:
		packets_dropped += 1
		return
	
	# Update statistics
	packets_received += 1
	packet_count += 1
	last_packet_time = Time.get_ticks_msec() / 1000.0
	last_sender = "%s:%d" % [sender_ip, sender_port]
	
	# Check if this is a marker packet or regular sensor packet
	if data.has("markers"):
		emit_signal("marker_packet_received", data)
	else:
		# Validate sensor packet structure
		if validate_packet(data):
			emit_signal("packet_received", data)
		else:
			packets_dropped += 1
			if debug_overlay:
				print("Invalid packet structure")


func validate_packet(data: Dictionary) -> bool:
	# Check for required fields
	if not data.has("tfluna") or not data.has("bno055"):
		return false
	
	var tfluna = data["tfluna"]
	var bno055 = data["bno055"]
	
	if typeof(tfluna) != TYPE_DICTIONARY or typeof(bno055) != TYPE_DICTIONARY:
		return false
	
	# Validate TFLuna data
	if not (tfluna.has("distance_cm") and tfluna.has("strength") and tfluna.has("timestamp")):
		return false
	
	# Validate BNO055 data
	if not (bno055.has("qw") and bno055.has("qx") and bno055.has("qy") and bno055.has("qz") and bno055.has("timestamp")):
		return false
	
	# Check timestamp synchronization
	var time_delta = abs(tfluna["timestamp"] - bno055["timestamp"])
	if time_delta > max_timestamp_delta:
		if debug_overlay:
			print("Timestamp mismatch: ", time_delta, "s")
		return false
	
	return true


func get_statistics() -> Dictionary:
	return {
		"is_listening": is_listening,
		"port": port,
		"packets_received": packets_received,
		"packets_dropped": packets_dropped,
		"packet_count": packet_count,
		"last_sender": last_sender,
		"last_packet_time": last_packet_time,
		"last_error": last_error
	}


func _exit_tree() -> void:
	stop_listening()
