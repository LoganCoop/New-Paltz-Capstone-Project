# Complete Unity Setup Guide for LiDAR Scanner

## Prerequisites
- Unity 2020.3 LTS or newer (2021/2022 LTS recommended)
- Your LiDAR hardware connected and sending UDP packets
- Python scripts running (from your `hal/` and `tools/` folders)

---

## Part 1: Create/Open Unity Project

### Step 1.1: Create New Project (if starting fresh)
1. Open **Unity Hub**
2. Click **"New Project"**
3. Select template: **3D** (not 3D URP/HDRP unless you want advanced rendering)
4. Project name: `LiDAR_Visualizer`
5. Location: `C:\Users\lpcoo\OneDrive\Desktop\Capstone Project - LiDAR\Unity\`
6. Click **"Create Project"**

### Step 1.2: Or Open Existing Project
1. Open **Unity Hub**
2. Click **"Open"** or **"Add"**
3. Navigate to your Unity project folder
4. Click **"Select Folder"**

---

## Part 2: Project Structure Setup

### Step 2.1: Create Folder Structure
In Unity's **Project** window, create these folders:

```
Assets/
├── Materials/          (for point cloud materials)
├── Prefabs/           (for point prefabs)
├── Scenes/            (for your scanner scene)
├── Scripts/           (your LidarUdpReceiver.cs is here)
└── Shaders/           (for PointCloud.shader)
```

**How to create folders:**
1. In **Project** window, right-click in `Assets`
2. Select **Create → Folder**
3. Name it accordingly

### Step 2.2: Move Existing Files
1. **Copy** `LidarUdpReceiver.cs` to `Assets/Scripts/` folder in Unity
2. **Copy** `PointCloud.shader` to `Assets/Shaders/` folder in Unity
3. Unity will auto-detect and import them

---

## Part 3: Create the PointCloud Shader Material

### Step 3.1: Verify Shader Import
1. In **Project** window, navigate to `Assets/Shaders/`
2. You should see **PointCloud.shader**
3. If you see an error icon, double-click to check for issues

### Step 3.2: Create Material from Shader
1. Right-click on **PointCloud.shader**
2. Select **Create → Material**
3. Name it: `PointCloudMaterial`
4. Material should appear in the same folder

### Step 3.3: Configure Material
1. Click on **PointCloudMaterial** to select it
2. In **Inspector** window, you'll see:
   - **Shader**: Should show "Custom/PointCloud"
   - **Point Size**: Set to `8` (adjust later based on viewing distance)
   - **Brightness**: Set to `1.0`

---

## Part 4: Create Point Prefab (for Legacy Mode)

### Step 4.1: Create Sphere GameObject
1. In **Hierarchy** window, right-click
2. Select **3D Object → Sphere**
3. Name it: `LidarPoint`

### Step 4.2: Configure the Sphere
1. Select `LidarPoint` in Hierarchy
2. In **Inspector**, set **Transform**:
   - Position: `(0, 0, 0)`
   - Rotation: `(0, 0, 0)`
   - Scale: `(1, 1, 1)` ← Will be controlled by script

### Step 4.3: Optimize the Sphere
1. Remove **Sphere Collider** component (we don't need physics):
   - In Inspector, find **Sphere Collider**
   - Click the ⚙️ gear icon → **Remove Component**

### Step 4.4: Create Prefab
1. Drag `LidarPoint` from **Hierarchy** to `Assets/Prefabs/` folder
2. Prefab should turn blue in Hierarchy
3. **Delete** `LidarPoint` from Hierarchy (we only need the prefab)

---

## Part 5: Create Distance Gradient

### Step 5.1: Create Gradient Asset
Unity's Gradient can't be saved as an asset directly, so we'll configure it on the component.

**NOTE**: We'll set this up in Part 6 when configuring the script.

---

## Part 6: Setup Scene

### Step 6.1: Create Scanner GameObject
1. In **Hierarchy**, right-click
2. Select **Create Empty**
3. Name it: `LidarScanner`
4. Set Position: `(0, 0, 0)`

### Step 6.2: Add the Script
1. Select `LidarScanner` GameObject
2. In **Inspector**, click **Add Component**
3. Type: `LidarUdpReceiver`
4. Press Enter (script should attach)

### Step 6.3: Configure Basic Settings

In the **Inspector** for `LidarScanner`:

#### Network Settings:
- **Port**: `5005` (must match your Python UDP sender)

#### Position Source:
- ✅ **Use Pos Field**: Checked (use position from UDP)
- ✅ **Debug Overlay**: Checked (shows stats on screen)
- ❌ **Ignore Orientation**: Unchecked
- ✅ **Flip X**: Checked
- ✅ **Flip Y**: Checked

#### Point Rendering:
- **Point Prefab**: Drag `LidarPoint` prefab from `Assets/Prefabs/`
- **Scale Meters**: `0.01` (converts cm to meters)
- **Point Scale**: `0.02` (visual size of points)
- **Max Points**: `50000`

#### Distance Gradient (Click to expand):
1. Click on the **gradient bar** (colored rectangle)
2. Set up gradient stops for distance coloring:
   - **Left (0%)**: Blue `(0, 0, 255)` - Close objects
   - **Middle (50%)**: Green `(0, 255, 0)` - Medium distance
   - **Right (100%)**: Red `(255, 0, 0)` - Far objects

**How to add gradient stops:**
- Click below the gradient bar to add stops
- Click above to add alpha stops
- Drag stops to reposition
- Click stop and set color in the color picker

#### Distance & Color Settings:
- **Min Distance Meters**: `0.1`
- **Max Distance Meters**: `5.0`
- **Min Intensity**: `0.5`
- **Max Intensity**: `1.5`
- **Min Strength**: `100` (filters weak signals)

#### Filtering:
- **Distance Median Window**: `5`
- **Orientation Smoothing**: `0.5`
- **Max Timestamp Delta Seconds**: `0.05`
- **Max Distance Jump Meters**: `0.15`

#### Spatial Deduplication:
- ✅ **Use Spatial Deduplication**: Checked
- **Voxel Size**: `0.03` (3cm grid)

#### Mesh-Based Rendering:
- ✅ **Use Mesh Renderer**: Checked (NEW SYSTEM)
- **Point Cloud Material**: Drag `PointCloudMaterial` from `Assets/Materials/`

---

## Part 7: Setup Camera

### Step 7.1: Configure Main Camera
1. Select **Main Camera** in Hierarchy
2. Set Position: `(0, 2, -3)` (behind and above the scanner)
3. Set Rotation: `(20, 0, 0)` (looking slightly down)
4. **Background**: 
   - Change **Clear Flags** to **Solid Color**
   - Set color to dark gray/black `(30, 30, 30)`

### Step 7.2: Add Camera Controls (Optional)
For easy navigation during testing:

1. Select **Main Camera**
2. Add Component → Search: `Fly Camera` or create a simple script:

**Create `Assets/Scripts/SimpleCamera.cs`:**
```csharp
using UnityEngine;

public class SimpleCamera : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float lookSpeed = 2f;
    
    void Update()
    {
        // WASD movement
        float x = Input.GetAxis("Horizontal") * moveSpeed * Time.deltaTime;
        float z = Input.GetAxis("Vertical") * moveSpeed * Time.deltaTime;
        float y = 0;
        
        if (Input.GetKey(KeyCode.E)) y = moveSpeed * Time.deltaTime;
        if (Input.GetKey(KeyCode.Q)) y = -moveSpeed * Time.deltaTime;
        
        transform.Translate(x, y, z);
        
        // Mouse look (hold right-click)
        if (Input.GetMouseButton(1))
        {
            float mouseX = Input.GetAxis("Mouse X") * lookSpeed;
            float mouseY = -Input.GetAxis("Mouse Y") * lookSpeed;
            
            transform.Rotate(mouseY, mouseX, 0);
        }
    }
}
```

3. Attach this script to Main Camera

---

## Part 8: Scene Lighting

### Step 8.1: Basic Lighting
1. Check if **Directional Light** exists in Hierarchy
2. If not: Right-click Hierarchy → **Light → Directional Light**
3. Set Rotation: `(50, -30, 0)`
4. Intensity: `1.0`

---

## Part 9: Save Scene

### Step 9.1: Save Your Scene
1. **File → Save As...**
2. Save to: `Assets/Scenes/`
3. Name: `LidarScanner.unity`
4. Click **Save**

---

## Part 10: Test the Setup

### Step 10.1: Pre-Flight Check
Before running Unity, verify:

✅ Python UDP sender is running (check `tools/send_sensor_data_udp.py`)
✅ Hardware is connected (TFLuna, BNO055)
✅ Port 5005 matches in both Unity and Python
✅ Firewall allows UDP on port 5005

### Step 10.2: Start Python Scripts
Open PowerShell/Command Prompt:

```powershell
cd "C:\Users\lpcoo\OneDrive\Desktop\Capstone Project - LiDAR"

# Option 1: Run all components
python run_all_components.py

# Option 2: Run UDP sender directly
python tools/send_sensor_data_udp.py
```

### Step 10.3: Run Unity Scene
1. Click **Play ▶️** button at top of Unity Editor
2. Check **Game** view for visualization
3. Check **Console** window (Ctrl+Shift+C) for errors

### Step 10.4: What You Should See

**On-Screen Overlay (top-left):**
```
UDP packets: 145
Last packet: 0.02s ago
Last sender: 127.0.0.1:5005
Point count: 2847 / 50000
Unique voxels: 2431
Mode: Mesh-based (optimized)
```

**In Scene:**
- Colored points appearing as you scan
- Points should form 3D shapes of objects
- Colors change with distance (blue=close, red=far)

---

## Part 11: Troubleshooting

### Problem: No points appearing

**Check 1: UDP Connection**
- Open Console window (Ctrl+Shift+C)
- Look for "UDP packets" count increasing in debug overlay
- If stuck at 0, check:
  - Python script is running
  - Port matches (5005)
  - Firewall settings

**Check 2: Point Prefab/Material**
- In mesh mode: Material must be assigned
- In legacy mode: Point Prefab must be assigned
- Check Console for errors

**Check 3: Camera Position**
- Points might be behind camera
- Use Scene view (double-click LidarScanner in Hierarchy)
- Move camera or adjust spawn position

### Problem: Points but no colors

**Solution:**
- Check Distance Gradient is configured
- Verify Min/Max Distance Meters settings
- Ensure Gradient has color stops

### Problem: Too many/few points

**Adjust Settings:**
- **Too dense**: Increase `voxelSize` (try 0.05-0.1)
- **Too sparse**: Decrease `voxelSize` (try 0.01-0.02)
- **Too few total**: Increase `maxPoints`
- **Performance issues**: Decrease `maxPoints`

### Problem: Points flickering/jumping

**Solutions:**
- Increase `orientationSmoothing` (try 0.7-0.9)
- Increase `distanceMedianWindow` (try 7-10)
- Decrease `maxDistanceJumpMeters` (try 0.05-0.1)

### Problem: Mesh not rendering (points invisible)

**Check:**
1. Select `LidarScanner` in Hierarchy
2. Look for **Mesh Renderer** component
3. Ensure Material is assigned
4. Try disabling "Use Mesh Renderer" temporarily (uses fallback)

---

## Part 12: Tips & Tricks

### Keyboard Shortcuts:
- **Space**: Calibrate orientation (sets current orientation as reference)
- **F**: Focus on selected object (in Scene view)
- **Right-click + WASD**: Fly around scene
- **Scroll wheel**: Zoom in/out
- **Alt + Left-click drag**: Orbit around point

### Performance Optimization:
1. **Reduce Max Points**: Start with 10,000, increase gradually
2. **Increase Voxel Size**: Fewer unique points = better performance
3. **Disable Debug Overlay**: Once working, uncheck for slight boost
4. **Build Mode**: File → Build Settings → Build (runs faster than editor)

### Visual Enhancements:
1. **Bloom Effect**: Camera → Add Component → Post Process Volume
2. **Point Size**: Adjust in PointCloudMaterial (5-15 range)
3. **Gradient**: Experiment with different color schemes
4. **Background**: Solid black looks more professional

### Data Capture:
- Use Unity's built-in **Recorder** package (Window → Package Manager)
- Record video: Window → General → Recorder → Add Movie Recorder
- Screenshots: Game view → right-click → Save Screenshot

---

## Part 13: Next Steps

### Once Basic Setup Works:

1. **Add Scanning Beam Visual**
   - LineRenderer from origin to scan point
   - Particle system at impact point

2. **Point Persistence**
   - Save point cloud to file
   - Load previous scans
   - Merge multiple scans

3. **Surface Reconstruction**
   - Normal estimation
   - Mesh generation from points
   - Collision detection

4. **UI Improvements**
   - Canvas with stats
   - Buttons to clear/save scans
   - Real-time coverage map

### Advanced Features:
- SLAM integration
- Multi-scanner support
- Real-time mapping
- AR overlay

---

## Quick Reference: File Locations

```
Project Root: C:\Users\lpcoo\OneDrive\Desktop\Capstone Project - LiDAR\

Python Scripts:
├── run_all_components.py          (start all systems)
├── tools/send_sensor_data_udp.py  (UDP sender)
└── hal/example_runner.py          (hardware interface)

Unity Project:
└── Unity/  (or wherever you created it)
    └── Assets/
        ├── Scenes/LidarScanner.unity
        ├── Scripts/LidarUdpReceiver.cs
        ├── Shaders/PointCloud.shader
        ├── Materials/PointCloudMaterial.mat
        └── Prefabs/LidarPoint.prefab
```

---

## Support & Resources

- **Unity Manual**: https://docs.unity3d.com/Manual/
- **C# Reference**: https://docs.microsoft.com/en-us/dotnet/csharp/
- **Point Cloud Rendering**: Search "Unity point cloud" on YouTube

---

## Checklist Before First Run

Use this checklist to verify setup:

- [ ] Unity project created/opened
- [ ] Folder structure created (Scripts, Shaders, Materials, etc.)
- [ ] LidarUdpReceiver.cs in Assets/Scripts/
- [ ] PointCloud.shader in Assets/Shaders/
- [ ] PointCloudMaterial created and configured
- [ ] LidarPoint prefab created (if using legacy mode)
- [ ] LidarScanner GameObject created in scene
- [ ] LidarUdpReceiver script attached to LidarScanner
- [ ] All settings configured in Inspector
- [ ] Point Cloud Material assigned
- [ ] Distance Gradient configured
- [ ] Camera positioned properly
- [ ] Scene saved
- [ ] Python scripts ready to run
- [ ] Hardware connected

---

**You're ready to scan! Press Play and start capturing the world in 3D!** 🎯
