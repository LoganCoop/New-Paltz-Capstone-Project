# LiDAR Point Cloud - Mesh-Based System Setup

## What Changed

The scanner has been upgraded from a GameObject-based system to a **mesh-based point cloud system** with **spatial deduplication**. This provides:

- **10x more points**: Increased from 5,000 to 50,000 points
- **Better performance**: Single mesh vs thousands of GameObjects
- **No duplicates**: Voxel-based deduplication prevents overlapping points
- **Faster rendering**: Uses Unity's optimized mesh pipeline

## Setup Instructions

### 1. Create a Material

1. In Unity, go to `Assets/Shaders/`
2. Right-click on `PointCloud.shader` → Create → Material
3. Name it `PointCloudMaterial`
4. Adjust settings:
   - Point Size: 5-10 (depends on your viewing distance)
   - Brightness: 1.0

### 2. Configure the LidarUdpReceiver

In the Inspector for your LidarUdpReceiver GameObject:

#### Mesh-Based Rendering
- ✅ **Use Mesh Renderer**: Enabled (for new system)
- **Point Cloud Material**: Drag the `PointCloudMaterial` here
- **Max Points**: 50000 (increase for more detail)

#### Spatial Deduplication
- ✅ **Use Spatial Deduplication**: Enabled
- **Voxel Size**: 0.03 (3cm grid - adjust based on your needs)
  - Smaller = more detail, more points
  - Larger = fewer duplicates, smoother appearance

### 3. Optional: Keep Old System as Fallback

If you encounter issues, you can disable the new system:
- ❌ **Use Mesh Renderer**: Disabled
- The script will fall back to GameObject instantiation
- Don't forget to assign **Point Prefab** for the old system

## How It Works

### Spatial Deduplication

The scanner divides 3D space into a grid of voxels (default: 3cm cubes). When a point is scanned:

1. Calculate which voxel it belongs to
2. Check if that voxel already has a point
3. If yes → skip (prevents duplicates)
4. If no → add the point

This prevents the "blob" effect when scanning the same area repeatedly.

### Mesh-Based Rendering

Instead of creating a GameObject for each point:
- All points are stored in a single `Mesh` with point topology
- Colors are stored as vertex colors
- Updated once per frame in `LateUpdate()`
- Uses Unity's optimized rendering pipeline

## Debugging

The on-screen overlay now shows:
- **Point count**: Current/Max points
- **Unique voxels**: Number of occupied voxels
- **Mode**: Which rendering system is active

## Performance Tips

1. **Increase max points gradually** - Test performance on your hardware
2. **Adjust voxel size** based on scanning distance:
   - Close-range (< 2m): 0.01-0.02m voxels
   - Medium-range (2-5m): 0.03-0.05m voxels
   - Long-range (> 5m): 0.05-0.1m voxels
3. **Use point size** in shader to compensate for smaller voxels

## Next Improvements

With this foundation in place, you can now add:
- Multi-sample averaging (reduce noise)
- Outlier detection (remove erroneous points)
- Scanning beam visualization
- Point confidence scores
- Data persistence (save scans)
