# 🎯 Unity LiDAR Scanner - Quick Start Checklist

Follow these steps in order. Check off each step as you complete it.

## ☑️ Phase 1: Project Setup (5 minutes)

- [ ] Open Unity Hub
- [ ] Create new 3D project OR open existing project
- [ ] Create folder structure:
  - [ ] Assets/Scripts/
  - [ ] Assets/Shaders/
  - [ ] Assets/Materials/
  - [ ] Assets/Prefabs/
  - [ ] Assets/Scenes/

## ☑️ Phase 2: Import Files (3 minutes)

- [ ] Copy `LidarUdpReceiver.cs` → `Assets/Scripts/`
- [ ] Copy `SimpleCamera.cs` → `Assets/Scripts/`
- [ ] Copy `PointCloud.shader` → `Assets/Shaders/`
- [ ] Wait for Unity to compile (check bottom-right progress bar)
- [ ] Verify no errors in Console window (Ctrl+Shift+C)

## ☑️ Phase 3: Create Materials (2 minutes)

- [ ] Navigate to `Assets/Shaders/` in Project window
- [ ] Right-click `PointCloud.shader` → Create → Material
- [ ] Rename material to: `PointCloudMaterial`
- [ ] Select material, set in Inspector:
  - [ ] Point Size: `8`
  - [ ] Brightness: `1.0`
- [ ] Move material to `Assets/Materials/` folder

## ☑️ Phase 4: Create Point Prefab (3 minutes)
*(Skip if using mesh-based mode)*

- [ ] Hierarchy → Right-click → 3D Object → Sphere
- [ ] Rename to: `LidarPoint`
- [ ] In Inspector, remove Sphere Collider component
- [ ] Drag from Hierarchy → `Assets/Prefabs/` folder
- [ ] Delete from Hierarchy (prefab is saved)

## ☑️ Phase 5: Setup Scene (10 minutes)

### Create Scanner GameObject:
- [ ] Hierarchy → Right-click → Create Empty
- [ ] Rename to: `LidarScanner`
- [ ] Position: `(0, 0, 0)`
- [ ] Add Component → `LidarUdpReceiver`

### Configure LidarUdpReceiver:
- [ ] **Port**: `5005`
- [ ] **Point Prefab**: Drag from Prefabs folder *(optional)*
- [ ] **Scale Meters**: `0.01`
- [ ] **Point Scale**: `0.02`
- [ ] **Max Points**: `50000`

#### Distance Gradient:
- [ ] Click gradient bar
- [ ] Add color stops:
  - [ ] Left (0%) = Blue
  - [ ] Middle (50%) = Green  
  - [ ] Right (100%) = Red

#### Settings:
- [ ] **Min Distance Meters**: `0.1`
- [ ] **Max Distance Meters**: `5.0`
- [ ] **Min Strength**: `100`
- [ ] **Distance Median Window**: `5`
- [ ] **Orientation Smoothing**: `0.5`

#### Checkboxes:
- [ ] ✅ Use Pos Field
- [ ] ✅ Debug Overlay
- [ ] ✅ Flip X
- [ ] ✅ Flip Y
- [ ] ✅ Use Spatial Deduplication
- [ ] **Voxel Size**: `0.03`
- [ ] ✅ Use Mesh Renderer
- [ ] **Point Cloud Material**: Drag from Materials folder

### Setup Camera:
- [ ] Select `Main Camera` in Hierarchy
- [ ] Position: `(0, 2, -3)`
- [ ] Rotation: `(20, 0, 0)`
- [ ] Background color: Dark gray `(30, 30, 30)`
- [ ] Add Component → `SimpleCamera` *(optional)*

### Lighting:
- [ ] Verify `Directional Light` exists
- [ ] Rotation: `(50, -30, 0)`

### Save Scene:
- [ ] File → Save As → `Assets/Scenes/LidarScanner.unity`

## ☑️ Phase 6: Test Python Connection (5 minutes)

### Start Python Scripts:
- [ ] Open PowerShell/Terminal
- [ ] Navigate to project folder:
  ```powershell
  cd "C:\Users\lpcoo\OneDrive\Desktop\Capstone Project - LiDAR"
  ```
- [ ] Run sensor scripts:
  ```powershell
  python run_all_components.py
  ```
  OR
  ```powershell
  python tools/send_sensor_data_udp.py
  ```
- [ ] Verify output shows "Sending UDP packets..."

## ☑️ Phase 7: First Test Run! (2 minutes)

- [ ] Press **Play ▶️** in Unity
- [ ] Check top-left overlay shows:
  - [ ] UDP packets count increasing
  - [ ] "Last packet: X.XXs ago" updating
  - [ ] Point count increasing
- [ ] Verify points appearing in Game view
- [ ] Test camera controls (Right-click + WASD)
- [ ] Press Space to calibrate orientation

## ✅ Success Criteria

You should see:
- ✅ Points appearing in 3D space
- ✅ Colors changing by distance (blue → green → red)
- ✅ UDP packet counter increasing
- ✅ No errors in Console
- ✅ Smooth point cloud building up

## ⚠️ Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| No packets received | Check Python script is running, port = 5005 |
| No points visible | Check camera position, Material assigned |
| Errors in Console | Read error message, check file paths |
| Performance slow | Decrease maxPoints to 10000, increase voxelSize to 0.05 |
| Points jumping | Increase orientationSmoothing to 0.8 |

## 📚 Full Documentation

For detailed explanations, see:
- `UNITY_SETUP_GUIDE.md` - Complete step-by-step guide
- `MESH_SYSTEM_SETUP.md` - Mesh rendering system details

## 🎮 Controls Reference

### In Unity Editor:
- **Space** - Calibrate sensor orientation
- **Right-Mouse + WASD** - Fly camera
- **E/Q** - Up/Down
- **Shift** - Move faster
- **F** - Focus on selected object

### In Python:
- **Ctrl+C** - Stop sensor scripts

---

**Estimated Total Time: 30 minutes**

**Current Step:** _________

**Notes:**
_______________________________________________________
_______________________________________________________
_______________________________________________________
