shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_always;

// Point cloud shader for VR LiDAR visualization
// Renders individual points with size and color control

uniform float point_size : hint_range(1.0, 20.0) = 8.0;
uniform float brightness : hint_range(0.0, 3.0) = 1.0;
uniform bool use_distance_fade = true;
uniform float fade_distance : hint_range(0.1, 100.0) = 10.0;
uniform float near_fade_distance : hint_range(0.01, 5.0) = 0.5;

varying vec3 world_position;
varying vec4 point_color;

void vertex() {
	// Pass through vertex color
	point_color = COLOR;
	
	// Calculate world position for distance-based effects
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	
	// Set point size based on distance to camera
	vec3 camera_position = INV_VIEW_MATRIX[3].xyz;
	float distance_to_camera = length(world_position - camera_position);
	
	// Scale point size inversely with distance for consistent perceived size
	POINT_SIZE = point_size / max(distance_to_camera, 0.5);
}

void fragment() {
	// Get base color from vertex color
	vec3 color = point_color.rgb * brightness;
	float alpha = point_color.a;
	
	// Calculate distance fade if enabled
	if (use_distance_fade) {
		vec3 camera_position = INV_VIEW_MATRIX[3].xyz;
		float distance_to_camera = length(world_position - camera_position);
		
		// Fade out points that are too far
		float far_fade = 1.0 - smoothstep(fade_distance * 0.7, fade_distance, distance_to_camera);
		
		// Fade out points that are too close (prevent overwhelming the view)
		float near_fade = smoothstep(0.0, near_fade_distance, distance_to_camera);
		
		alpha *= far_fade * near_fade;
	}
	
	// Create circular point shape
	vec2 point_coord = POINT_COORD * 2.0 - 1.0;
	float dist = length(point_coord);
	
	// Smooth edge antialiasing
	float circle = 1.0 - smoothstep(0.8, 1.0, dist);
	alpha *= circle;
	
	// Discard fully transparent pixels
	if (alpha < 0.01) {
		discard;
	}
	
	ALBEDO = color;
	ALPHA = alpha;
	
	// Add slight glow effect in the center
	float glow = exp(-dist * 3.0) * 0.3;
	EMISSION = color * glow;
}
