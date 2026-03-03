# Quest 3 VR LiDAR - Quick Start Checklist

## ✅ Before You Start
- [ ] Quest 3 fully charged
- [ ] Quest 3 Developer Mode enabled (via Meta Quest app)
- [ ] PC and Quest 3 on same WiFi network
- [ ] Godot 4.3+ installed
- [ ] Android export templates installed in Godot
- [ ] ADB (Android Debug Bridge) installed
- [ ] LiDAR sensors (TFLuna + BNO055) connected
- [ ] Python environment set up

---

## 🔧 Hardware Setup (5 minutes)
1. [ ] Connect TFLuna to PC/Raspberry Pi via UART/I2C
2. [ ] Connect BNO055 to same device via I2C
3. [ ] Verify sensor connections:
   ```powershell
   python tools/tfluna_read.py
   python tools/bno055_quat_read.py
   ```
4. [ ] Connect Quest 3 to PC via USB-C cable (for first deployment)
5. [ ] Put on Quest 3 and allow USB debugging

---

## 💻 Software Setup (10 minutes)

### Network Configuration
1. [ ] Get PC IP address: `ipconfig` in PowerShell
2. [ ] Note down IP (e.g., 192.168.1.100)
3. [ ] Open Windows Firewall and allow UDP port 5005:
   ```powershell
   netsh advfirewall firewall add rule name="LiDAR UDP" dir=in action=allow protocol=UDP localport=5005
   ```

### Godot Project
1. [ ] Open Godot 4.3
2. [ ] Import project: `li-dar\project.godot`
3. [ ] Wait for project to load and import assets
4. [ ] Open `scenes/main_vr.tscn`

### Export Configuration
1. [ ] Go to **Project → Export**
2. [ ] Add **Android** preset
3. [ ] Configure for Quest 3:
   - [ ] XR Mode: OpenXR
   - [ ] Permissions: INTERNET, ACCESS_NETWORK_STATE
   - [ ] Hand Tracking: V2.0
4. [ ] Verify ADB connection: `adb devices`

---

## 🚀 First Run (5 minutes)

### Start Sensor Streaming
1. [ ] Open PowerShell in project root
2. [ ] Run UDP streaming:
   ```powershell
   python tools/send_sensor_data_udp.py
   ```
   OR
   ```powershell
   python run_all_components.py
   ```
3. [ ] Verify terminal shows "Sending UDP packets..."

### Deploy to Quest 3
1. [ ] In Godot, click **Project → Export → Quest 3**
2. [ ] Click **Export Project** → Save as `lidar_quest3.apk`
3. [ ] OR click **Remote Debug** to auto-deploy
4. [ ] Wait for build to complete (1-3 minutes first time)
5. [ ] App should auto-launch on Quest 3

---

## 🎮 Testing (2 minutes)

### In Quest 3
1. [ ] Put on Quest 3 headset
2. [ ] Look around - you should see empty 3D space
3. [ ] Check console output (if using Remote Debug):
   - [ ] "✓ UDP Receiver started on port 5005"
   - [ ] "✓ Point Cloud Visualizer connected"

### Generate Point Cloud
1. [ ] Point TFLuna sensor at objects around you
2. [ ] Slowly rotate or move the sensor
3. [ ] Watch as colored points appear in VR space
4. [ ] Points should be:
   - Blue = close objects
   - Red = far objects
   - Updating in real-time

### Controller Test
1. [ ] **Left thumbstick**: Move forward/back/strafe
2. [ ] **Left grip + thumbstick X**: Rotate view
3. [ ] **Left grip + trigger**: Scale point cloud up
4. [ ] **Left trigger click**: Recenter player
5. [ ] **Left X/A button**: Toggle spatial deduplication
6. [ ] **Left Y/B button**: Clear point cloud
7. [ ] **Left Menu button**: Toggle HUD visibility

---

## 🐛 Quick Troubleshooting

### No Point Cloud Appearing
- [ ] Check Python script is running and sending UDP
- [ ] Verify firewall allows UDP 5005
- [ ] Ensure PC IP is correct
- [ ] Check both devices on same WiFi network
- [ ] Look at Godot console for UDP errors

### App Crashes or Won't Launch
- [ ] Check Godot console for export errors
- [ ] Verify Android export templates installed
- [ ] Ensure Quest 3 firmware is up to date
- [ ] Try clean build: delete `build` folder and re-export

### Low Frame Rate
- [ ] Reduce Max Points (50000 → 30000)
- [ ] Increase Voxel Size (0.03 → 0.05)
- [ ] Disable shadows on DirectionalLight3D
- [ ] Enable Foveated Rendering (already enabled)

### Controller Not Working
- [ ] Check Quest 3 controllers are paired
- [ ] Replace controller batteries if needed
- [ ] Verify controller tracking in Quest dashboard

---

## 📊 Expected Results

After completing this checklist, you should have:
- ✓ Real-time 3D point cloud in VR
- ✓ Color-coded distance visualization
- ✓ Smooth 90Hz VR experience
- ✓ Full 6DOF movement around point cloud
- ✓ Working controller input
- ✓ Up to 50,000 points rendered

---

## 🎯 Next Steps

Once basic functionality works:
1. [ ] Calibrate BNO055 for better orientation
2. [ ] Tune point cloud colors and size
3. [ ] Experiment with voxel size for quality vs performance
4. [ ] Add multiple TFLuna sensors for faster scanning
5. [ ] Implement point cloud export to PLY/OBJ format

---

## 📝 Notes

**UDP Reception Test:**
```gdscript
# In Godot console, you should see:
UDP Receiver started on port 5005
✓ Point Cloud Visualizer connected to UDP Receiver
Packet received: TFLuna distance: 1.23m, Strength: 450
```

**Performance Target:**
- 90 FPS on Quest 3 with 30k-50k points
- < 20ms frame time
- Stereo rendering at 1832x1920 per eye

---

**Time to Complete**: ~20-25 minutes for full setup
**Difficulty**: Intermediate
**Last Updated**: March 2026
