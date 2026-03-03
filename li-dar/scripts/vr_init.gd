extends Node3D
## VR Initialization Script
## Ensures XR viewport is properly configured for OpenXR rendering

func _ready() -> void:
	# Enable XR rendering on the main viewport
	var viewport = get_viewport()
	if viewport:
		viewport.use_xr = true
		print("✓ XR Viewport enabled")
	
	# Double-check XRInterface is initialized
	if XRServer:
		var xr_interface = XRServer.find_interface("OpenXR")
		if xr_interface:
			print("✓ OpenXR interface found")
			
			if not xr_interface.is_initialized():
				print("Initializing OpenXR...")
				xr_interface.initialize()
		else:
			print("✗ OpenXR interface not found!")
	else:
		print("✗ XRServer not available!")
