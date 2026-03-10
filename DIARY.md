# Project Diary
## (2/5/26)
## What I want to add
- BNO055 IMU
- Pi Camera 3
- Jumper cables

## What I have added
- TF-Luna LiDAR scanner
- Raspberry Pi 5

## Notes
- Plan: assemble scanner system after the BNO055 IMU, Pi Camera 3, and jumper cables arrive.
- Software choice: Raspberry Pi will handle point-generation math, then send point data to Godot for visualization.
- Orientation plan: use BNO055 quaternion output for more accurate orientation tracking.
- Camera plan: use Pi Camera 3 with marker-based localization to reduce drift when mapping.

## (2/6/26)

## What I want to add 
- 3D printed casing
- software for part integration

## What I have added
- BNO055 IMU
- Pi Camera 3
- Jumper cables
- TF-Luna LiDAR scanner
- Raspberry Pi 5

## Notes
- Plan: I have wired in all parts so now my game plan is to test and calibrate all parts to get some preliminary test data. Then I'll begin working on the housing for all my parts to make it into a handheld device. Then I will work further on the software.
- Now that all components have been tested and are working I have made a working dev branch where I will develope the software to make 3D maps and create the housing for the full system.

## (2/9/26)

##
- Plan: I have begon designing and printing the housing for the LiDAR system. While the case is being printed I plan on working on building the bridge of data between the hardware and software. I have chosen to send the readings of the TF-luna and other components to a 3D environment made in Unity.

## (2/12/26)
### What I accomplished
- Finished Pi Camera 3 testing and calibration.
- Successfully estimated ArUco marker poses and streamed them to Unity.
- Updated Unity receiver to handle both sensor and marker pose data.
- Cleaned up unused folders (libcamera) from git tracking.

### Next Steps
- Commit and push latest changes.
- Continue testing marker pose visualization in Unity.
- Finalize integration and document workflow.

## (3/3/26)
### What I accomplished
- Switched focus from Unity-only visualization to a dedicated Godot VR pipeline for Quest 3.
- Set up the `li-dar/` Godot project structure for VR point cloud rendering.
- Added initial VR scripts for UDP receive, point cloud visualization, and controller input.
- Added project setup docs for Quest 3 deployment and testing.

### Next Steps
- Validate full sensor-to-VR data flow (TFLuna + BNO055 -> UDP -> Quest 3 app).
- Tune rendering and point density to keep stable FPS in-headset.
- Continue documenting setup and troubleshooting notes.

## (3/10/26)
### What I added
- Godot Quest 3 VR app assets and config in `li-dar/` (scene, scripts, shaders, materials, Android export files).
- VR-specific scripts: `vr_init.gd`, `vr_hud_3d.gd`, and `debug_hud.gd` for startup and in-headset debugging.
- Quest 3 deployment docs: `li-dar/QUEST3_VR_SETUP_GUIDE.md`, `li-dar/QUEST3_QUICK_START.md`, and `li-dar/deploy_to_quest3.ps1`.
- Updated point cloud shader/material pipeline for better in-headset visualization.

### Notes
- Current visualization direction is Quest 3 VR-first (black background, non-passthrough) so scanning can be viewed in an isolated environment.
- Python tooling and HAL remain the sensor source, with UDP bridging into the VR app.

### Next Steps
- Run end-to-end headset test with live UDP stream and record performance baseline.
- Add save/export option for captured point clouds.
- Refine VR interaction flow (controller toggles, reset, and debug HUD controls).

## Presentation Out line (3/10/26)
- Intro - begin by defining LiDAR and its uses
- Build components - list out components used and then describe their various functions
- Construction - describe the construction of the LiDAR scanner (wiring into the Raspberry Pi, CAD modeling, and printing/assembly.
- Initial testing - talk about the raw data derived from each component
- Sending data - talk about using UDP to send packets of data from the initial testing to the Unity/Godot environments
- Point cloud - talk about generating point clouds from the data sent over from the scanner via UDP
- VR capabilities - talk about how now that point clouds have been generated via a 2D interface like unity it can now be integrated with VR to make a more interactive point cloud with greater accuracy.
- Conclusion - describe how point clouds can be useful and my overall experience building the LiDAR scanner system.
