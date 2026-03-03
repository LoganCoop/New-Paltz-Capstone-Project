# LiDAR Quest 3 VR Point Cloud Visualization

This is a **Godot 4.x** project for visualizing LiDAR point clouds in VR using the Meta Quest 3 headset.

## 🎯 Purpose

This VR application replaces the original PiCam 3 approach with Quest 3's superior tracking capabilities, allowing for more accurate and immersive 3D point cloud visualization.

## 📁 Project Structure

```
li-dar/
├── materials/              # Custom materials for rendering
│   └── point_cloud_material.tres
├── scenes/                 # Godot scene files
│   └── main_vr.tscn       # Main VR scene
├── scripts/                # GDScript files
│   ├── lidar_udp_receiver.gd
│   ├── point_cloud_visualizer.gd
│   └── vr_controller.gd
├── shaders/                # Custom shaders
│   └── point_cloud.gdshader
├── icon.svg                # Project icon
├── project.godot           # Godot project configuration
├── QUEST3_VR_SETUP_GUIDE.md    # Complete setup instructions
└── QUEST3_QUICK_START.md        # Quick start checklist
```

## 🚀 Quick Start

1. **Install Godot 4.3+** from [godotengine.org](https://godotengine.org)
2. **Open this project** in Godot
3. **Connect Quest 3** via USB (Developer Mode enabled)
4. **Export to Quest 3** (Project → Export → Android)
5. **Run Python sensor scripts** from parent directory
6. **Launch the app** on Quest 3

**Full instructions**: See [QUEST3_VR_SETUP_GUIDE.md](QUEST3_VR_SETUP_GUIDE.md)

## 🎮 Features

- ✅ Real-time LiDAR point cloud visualization in VR
- ✅ UDP receiver for TFLuna + BNO055 sensor data
- ✅ Mesh-based rendering (up to 50,000 points)
- ✅ Spatial deduplication for cleaner clouds
- ✅ Color-coded distance visualization
- ✅ VR controller support for navigation
- ✅ 6DOF tracking using Quest 3
- ✅ 90Hz refresh rate
- ✅ Custom point cloud shader

## 🔗 How It Connects to Parent Project

This Godot project receives data from:
- **`tools/send_sensor_data_udp.py`** - Sends sensor data via UDP
- **`hal/`** - Hardware abstraction layer for sensors
- **TFLuna LiDAR sensor** - Distance measurements
- **BNO055 IMU** - Orientation quaternions

## 🛠️ Requirements

- **Meta Quest 3** VR headset
- **Godot 4.3+**
- **Android SDK & NDK**
- **Python 3.x** (for sensor scripts)
- **WiFi network** (PC and Quest 3 must be on same network)

## 📚 Documentation

- **[QUEST3_VR_SETUP_GUIDE.md](QUEST3_VR_SETUP_GUIDE.md)** - Complete setup guide
- **[QUEST3_QUICK_START.md](QUEST3_QUICK_START.md)** - Quick start checklist
- **[../UNITY_SETUP_GUIDE.md](../UNITY_SETUP_GUIDE.md)** - Original Unity version (alternative)

## 🎨 Customization

### Change Point Size
Edit `shaders/point_cloud.gdshader`:
```gdshader
uniform float point_size = 8.0;  // Change this value
```

### Change Colors
Edit `scripts/point_cloud_visualizer.gd`:
```gdscript
@export var min_color: Color = Color(0, 0, 1)  # Blue
@export var max_color: Color = Color(1, 0, 0)  # Red
```

## 🐛 Troubleshooting

**No points appearing?**
- Check UDP port 5005 is open in firewall
- Verify Python scripts are running
- Ensure PC and Quest 3 are on same WiFi

**Low frame rate?**
- Reduce `max_points` to 30000
- Increase `voxel_size` to 0.05
- Disable deduplication temporarily

**App crashes?**
- Check Godot console for errors
- Verify Android export templates installed
- Update Quest 3 firmware

## 🎯 Advantages Over Unity/PiCam Approach

1. **No camera required** - Uses Quest 3's built-in tracking
2. **More accurate** - Inside-out tracking beats IMU-only
3. **Real-time immersion** - See the scan as you create it
4. **6DOF freedom** - Walk around the point cloud
5. **No Aruco markers** - Simpler setup
6. **Higher refresh** - 90Hz vs typical 60Hz

## 📊 Performance

- **Target**: 90 FPS on Quest 3
- **Max Points**: 50,000 (configurable)
- **Latency**: < 50ms from sensor to display
- **Resolution**: 1832×1920 per eye

## 🔮 Future Enhancements

- [ ] Point cloud export to PLY/OBJ
- [ ] Multiple TFLuna sensor support
- [ ] Hand tracking instead of controllers
- [ ] Spatial anchors for persistent clouds
- [ ] WiFi direct instead of UDP broadcast
- [ ] Quest 3 passthrough mode integration

---

**Created**: March 2026  
**Godot Version**: 4.3+  
**Target Platform**: Meta Quest 3 (Android)  
**License**: See parent project
