# Godot Quest 3 VR LiDAR Point Cloud Setup Guide

## Overview
This Godot 4.x project provides a VR-based LiDAR point cloud visualization system for Meta Quest 3. It uses Quest 3 positional tracking to create accurate point cloud visualizations in VR with a black background.

## What This Setup Does
- Receives LiDAR data via UDP (TFLuna distance sensor + BNO055 orientation)
- Visualizes real-time point clouds in VR with color-coded distance
- Uses Quest 3's superior tracking for accurate spatial mapping
- Provides VR controller-based navigation and point cloud manipulation
- Supports spatial deduplication for cleaner point clouds
- Renders up to 50,000 points with optimized mesh-based rendering

---

## Prerequisites

### Hardware
- **Meta Quest 3** VR headset
- **TFLuna LiDAR sensor** (connected to your PC/Raspberry Pi)
- **BNO055 IMU sensor** (for orientation data)
- **PC with WiFi/USB connection** to Quest 3

### Software
- **Godot 4.3+** (download from godotengine.org)
- **Android SDK and NDK** (for Quest 3 builds)
- **OpenXR support** (included in Godot 4+)
- **Python 3.x** (for sensor data streaming)
- **ADB (Android Debug Bridge)** (for deploying to Quest 3)

---

## Part 1: Install Godot and Android Export Templates

### Step 1.1: Download Godot
1. Go to https://godotengine.org/download
2. Download **Godot 4.3 Standard** (not .NET version)
3. Extract and run `Godot_v4.3-stable_win64.exe`

### Step 1.2: Install Android Export Templates
1. In Godot, go to **Editor → Manage Export Templates**
2. Click **Download and Install**
3. Wait for templates to download (this may take several minutes)

### Step 1.3: Configure Android SDK
1. Go to **Editor → Editor Settings**
2. Navigate to **Export → Android**
3. Set paths:
   - **Android SDK Path**: `C:\Users\YourName\AppData\Local\Android\Sdk`
   - **Debug Keystore**: Auto-generated or use existing
   
   If you don't have Android SDK installed:
   - Download Android Studio from https://developer.android.com/studio
   - Install Android Studio and open it
   - Go to **Tools → SDK Manager**
   - Install **Android SDK Platform-Tools** and **NDK**

---

## Part 2: Open the Project

### Step 2.1: Launch Godot
1. Open **Godot 4.3**
2. Click **Import**
3. Navigate to: `C:\Users\lpcoo\OneDrive\Desktop\Capstone Project - LiDAR\li-dar`
4. Select `project.godot`
5. Click **Import & Edit**

### Step 2.2: Verify Project Structure
In the **FileSystem** panel, you should see:
```
li-dar/
├── materials/
│   └── point_cloud_material.tres
├── scenes/
│   └── main_vr.tscn
├── scripts/
│   ├── lidar_udp_receiver.gd
│   ├── point_cloud_visualizer.gd
│   └── vr_controller.gd
└── shaders/
    └── point_cloud.gdshader
```

---

## Part 3: Configure Quest 3 Export Settings

### Step 3.1: Create Android Export Preset
1. Go to **Project → Export**
2. Click **Add...** → **Android**
3. Name it: `Quest 3`

### Step 3.2: Configure Export Options
In the Export window, set:

**Options Tab:**
- **Name**: `LiDAR VR Point Cloud`
- **Runnable**: ✓ (checked)

**Resources Tab:**
- **Export Mode**: Export all resources

**Features Tab:**
- Custom Build: Use Custom Build (Optional, for plugins)

**Permissions Tab:**
Enable these permissions:
- ✓ INTERNET
- ✓ ACCESS_NETWORK_STATE
- ✓ ACCESS_WIFI_STATE

**XR Features Tab:**
- **XR Mode**: OpenXR
- **Hand Tracking**: V2.0 (Quest 3 feature)
- **Passthrough**: Disabled
- **Foveation Level**: High (for performance)

### Step 3.3: Set Android Manifest
In **Android → Manifest** section, add:
```xml
<category android:name="com.oculus.intent.category.VR" />
<uses-feature android:name="android.hardware.vr.headtracking" android:version="1" android:required="true" />
```

---

## Part 4: Configure Python UDP Streaming

### Step 4.1: Ensure Python Scripts are Running
Your existing Python scripts should be streaming data. Verify they're running:

```powershell
cd "C:\Users\lpcoo\OneDrive\Desktop\Capstone Project - LiDAR"
python tools/send_sensor_data_udp.py
```

Or run all components:
```powershell
python run_all_components.py
```

### Step 4.2: Configure Network Settings
**Important**: Quest 3 and PC must be on the same WiFi network!

1. Get your PC's IP address:
   ```powershell
   ipconfig
   ```
   Look for **IPv4 Address** (e.g., `192.168.1.100`)

2. Update the UDP destination in your Python script to broadcast:
   ```python
   UDP_IP = "0.0.0.0"  # Listen on all interfaces
   UDP_PORT = 5005
   ```

### Step 4.3: Configure Firewall
Allow UDP port 5005 through Windows Firewall:

```powershell
netsh advfirewall firewall add rule name="LiDAR UDP" dir=in action=allow protocol=UDP localport=5005
```

---

## Part 5: Testing in Godot Editor (PC VR Preview)

### Step 5.1: Test Without VR First
1. In Godot, open `scenes/main_vr.tscn`
2. Press **F5** or click **Run Project**
3. You should see the scene load (no VR yet)
4. Check the **Output** panel for:
   ```
   ✓ UDP Receiver started on port 5005
   ✓ Point Cloud Visualizer connected to UDP Receiver
   ```

### Step 5.2: Verify UDP Reception
1. Start your Python sensor streaming script
2. Watch the **Output** panel for incoming packets
3. You should see points appearing in the viewport

---

## Part 6: Deploy to Quest 3

### Step 6.1: Enable Developer Mode on Quest 3
1. Open **Meta Quest mobile app** on your phone
2. Go to **Menu → Devices → Quest 3**
3. Select **Developer Mode**
4. Toggle **Developer Mode ON**

### Step 6.2: Connect Quest 3 to PC
1. Connect Quest 3 to PC via **USB-C cable**
2. Put on the headset
3. You'll see a prompt: **Allow USB debugging?** → Select **Always Allow**

### Step 6.3: Verify ADB Connection
Open PowerShell and run:
```powershell
adb devices
```

You should see:
```
List of devices attached
1WMHH1234567    device
```

### Step 6.4: Export and Install
1. In Godot, go to **Project → Export**
2. Select **Quest 3** preset
3. Click **Export Project**
4. Choose a location and filename: `lidar_quest3.apk`
5. Click **Save**

Or **Remote Deploy**:
1. With Quest 3 connected, click **Remote Debug** or **Export → Install & Run**
2. The app will install and launch automatically

---

## Part 7: Using the App on Quest 3

### Controls

**Left Controller (Thumbstick):**
- **Up/Down**: Move forward/backward
- **Left/Right**: Strafe left/right

**Right Controller:**
- **Thumbstick Left/Right**: Rotate view
- **Grip + Trigger**: Scale point cloud size
- **A Button**: Toggle spatial deduplication
- **B Button**: Clear point cloud

**Both Controllers:**
- Walk around to see the point cloud from different angles
- Quest 3's tracking provides accurate positioning

### What You Should See
1. Point cloud appears in 3D space
2. Points are color-coded:
   - **Blue**: Close objects (< 1m)
   - **Red**: Far objects (> 4m)
   - **Green/Yellow**: Mid-range
3. Brighter points = stronger signal
4. Smooth, real-time updates

---

## Part 8: Optimization and Troubleshooting

### Performance Optimization

**If framerate is low:**
1. Open `scenes/main_vr.tscn`
2. Select **PointCloudVisualizer** node
3. In Inspector, reduce:
   - **Max Points**: 30000 (from 50000)
   - **Voxel Size**: 0.05 (from 0.03)

**Enable Fixed Foveated Rendering:**
- Already enabled in project.godot
- Quest 3 will render center of view at higher quality

### Common Issues

**Issue: "No UDP packets received"**
- Verify PC and Quest 3 are on same WiFi
- Check Windows Firewall allows UDP 5005
- Ensure Python script is running
- Try increasing UDP send rate in Python

**Issue: "App crashes on Quest 3"**
- Check Godot output for errors before exporting
- Ensure Android export templates are installed
- Verify OpenXR is enabled in export settings
- Check Quest 3 has latest firmware

**Issue: "Point cloud is jittery"**
- Increase **Orientation Smoothing** (0.5 → 0.8)
- Increase **Distance Median Window** (5 → 10)
- Check BNO055 calibration

**Issue: "Colors look wrong"**
- Adjust **Min Color** and **Max Color** in visualizer
- Check **Min/Max Distance Meters** range
- Verify TFLuna is reporting correct distances

**Issue: "Too many duplicated points"**
- Enable **Use Spatial Deduplication**
- Decrease **Voxel Size** (0.03 → 0.02)

---

## Part 9: Customization

### Adjust Point Size
Edit `shaders/point_cloud.gdshader`:
```gdshader
uniform float point_size : hint_range(1.0, 20.0) = 12.0;  // Increase for bigger points
```

### Change Color Scheme
Edit `scripts/point_cloud_visualizer.gd`:
```gdscript
@export var min_color: Color = Color(0.0, 1.0, 0.0)  # Green for close
@export var max_color: Color = Color(1.0, 1.0, 0.0)  # Yellow for far
```

---

## Advantages Over PiCam 3 Approach

1. **Superior Tracking**: Quest 3's inside-out tracking is more accurate than BNO055 alone
2. **6DOF Movement**: Full positional + rotational tracking
3. **Real-time Visualization**: See the point cloud immediately in VR
4. **Interactive**: Walk around and manipulate the point cloud in real-time
5. **No Camera Processing**: No need for Aruco markers or camera calibration
6. **Higher Refresh Rate**: Quest 3 runs at 90Hz or 120Hz
7. **Built-in Display**: No need for external monitor

---

## Next Steps

1. **Calibrate Sensors**: Run calibration scripts for BNO055 and TFLuna
2. **Save Point Clouds**: Add export functionality to save point clouds as PLY/OBJ files
3. **Multi-Sensor Support**: Add support for multiple TFLuna sensors
4. **Hand Tracking**: Use Quest 3's hand tracking instead of controllers
5. **Spatial Anchors**: Save point clouds with persistent world anchors

---

## File Reference

- **main_vr.tscn**: Main VR scene with XR setup
- **lidar_udp_receiver.gd**: Receives and parses UDP packets
- **point_cloud_visualizer.gd**: Creates and updates point cloud mesh
- **vr_controller.gd**: Handles Quest 3 controller input
- **point_cloud.gdshader**: Custom shader for point rendering
- **point_cloud_material.tres**: Material using the custom shader

---

## Support and Resources

- **Godot XR Documentation**: https://docs.godotengine.org/en/stable/tutorials/xr/
- **Quest 3 Development**: https://developer.oculus.com/documentation/
- **Project Issues**: Check DIARY.md for development notes

---

**Happy VR Point Cloud Mapping! 🚀**
