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
<<<<<<< Updated upstream
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

## (3/23/26)
### What I accomplished
- Fixed point cloud coordinate orientation in Unity (`LidarUdpReceiver.cs`) — point cloud now renders in first-person perspective instead of top-down.
- Resolved left-right mirroring issue: scanner movement to the left now correctly plots points to the left.
- Fine-tuned yaw correction offset iteratively from 90° → -90° → -135° → -180° based on live testing feedback.
- Added right-click mouse drag orbit feature, allowing the camera to rotate around the point cloud interactively.
- Fixed a Unity runtime crash (`InvalidOperationException`) caused by legacy `Input.*` API calls conflicting with the project's new Input System package — patched `HandleRightClickOrbit()` with a `#if ENABLE_INPUT_SYSTEM` / `#else` dual-path implementation using `Mouse.current`.

### Current Working Settings (Unity Inspector)
- Flip X: false, Flip Y: true
- Swap Y And Z: true, Invert Z: true, Mirror Horizontal: true
- Yaw Correction Degrees: -180
- Enable Right Click Orbit: true, Orbit Sensitivity: 3.0

### Next Steps
- Run a full live scan test end-to-end (Pi → UDP → Unity) to validate orientation and controls.
- Consider adding mouse wheel zoom and middle-click pan for fuller view control.

## Presentation Out line (3/10/26)
- Intro - begin by defining LiDAR and its uses
- Build components - list out components used and then describe their various functions
- Construction - describe the construction of the LiDAR scanner (wiring into the Raspberry Pi, CAD modeling, and printing/assembly.
- Initial testing - talk about the raw data derived from each component
- Sending data - talk about using UDP to send packets of data from the initial testing to the Unity/Godot environments
- Point cloud - talk about generating point clouds from the data sent over from the scanner via UDP
- VR capabilities - talk about how now that point clouds have been generated via a 2D interface like unity it can now be integrated with VR to make a more interactive point cloud with greater accuracy.
- Conclusion - describe how point clouds can be useful and my overall experience building the LiDAR scanner system.

## (4/6/26)
### Notes
- After further research, I found that the only reliable way to get proper close-up object scans is through the ArUco process using the Pi Camera 3.
- With more work on the framework, I can get this workflow fully functional.
- Current blocker: my Pi Camera 3 is still not working.

### Next Steps
- Purchase and install a replacement Pi Camera 3.
- Resume and complete the small object scanning workflow once the new camera is in place.
=======
- 
- 
- 

## (4/13/26)
### What I accomplished
- Replaced Pi Camera 3 with Pi Camera Rev 1.3 and verified camera is working.
### Plan / Next Steps (focus shift to ArUco)
- Use ArUco markers for more accurate positioning and pointcloud alignment.
- Capture new calibration images with the Rev 1.3 camera and run camera calibration.
- Update ArUco scripts (`tools/aruco_pose_demo.py`, `tools/aruco_anchor_publisher.py`) to use the new calibration and camera device/backend.
- Generate improved point clouds using marker-based poses and evaluate accuracy.
- Print a set of ArUco markers for field testing and repeat calibration if needed.

### Notes
- Will prefer OpenCV VideoCapture or `picamera2` depending on environment; test both if necessary.
- Next immediate action: capture calibration images and produce a `.npz` intrinsics file.
>>>>>>> Stashed changes

## (4/20/26)
### What I accomplished
- Updated BNO055 I2C usage to default to bus 3 and added `--i2c-bus` to relevant tools.
- Integrated ArUco marker output with the UDP sensor sender: `tools/send_sensor_data_udp.py` now listens for ArUco packets (default port 6006) and includes marker data in outgoing UDP packets to Unity.
- Made ArUco detector UDP destination configurable (`tools/aruco_pose_demo.py` now defaults to sending to localhost:6006).

### Final status (4/20/26, after live testing)
- Rewired BNO055 to I2C bus 1 and updated defaults to use bus 1. All IMU reads validated on bus 1.
- Started headless ArUco detector (Picamera2) feeding the local aggregator on port 6006.
- Implemented a simple `scanner_pose` fusion in `tools/send_sensor_data_udp.py` combining ArUco position (first marker `tvec`) with BNO055 orientation (normalized quaternion). Outgoing UDP packets now include `scanner_pose` with `position` and `orientation` fields.
- Verified outgoing UDP packets to Unity (192.168.0.198:5005) contain `tfluna`, `bno055`, `aruco`, and the new `scanner_pose` field.

### Next steps / Improvements to consider
- Smooth `scanner_pose` over time (exponential moving average or complementary filter).
- Transform ArUco `tvec` from camera frame into the IMU/world frame using measured extrinsics.
- Average or robustly select among multiple detected markers for a more stable position.
- Add timestamp alignment logic and small buffer to better fuse asynchronous sensor updates.
- Add a `--fusion-mode` flag to `tools/send_sensor_data_udp.py` to toggle simple vs. smoothed fusion.

### Next steps / Test plan
- Run the ArUco detector and the sensor UDP sender together: start `tools/send_sensor_data_udp.py` (pointing to Unity IP) and run `tools/aruco_pose_demo.py` to feed marker data to it.
- Verify fused packets arriving in Unity contain `aruco` field with markers and that IMU/TF-Luna fields remain present.
- If OK, perform a live scan and note results in this diary.

### Notes
- Defaults were set to I2C bus 3 to match the new hardware wiring; use `--i2c-bus` to override if needed.

### Additional work completed later on 4/20/26
- Fixed an unexpected Unity startup sphere by preventing runtime marker visualization from spawning the point prefab unless marker rendering is explicitly enabled.
- Moved mesh initialization earlier in the Unity lifecycle so the receiver no longer flashes a primitive mesh at startup.
- Refactored the sensor-to-Unity frame handling so `tools/send_sensor_data_udp.py` now owns the main coordinate conversion and tags outgoing packets as Unity-frame data.
- Simplified `Assets/Scripts/LidarUdpReceiver.cs` so Unity consumes already-converted packet data instead of relying on stacked flip/swap corrections.
- Added Unity-frame trim and inversion controls for fast live testing while keeping the legacy correction path separated.
- Added debug overlay lines in Unity to show `Position source`, `Frame mode`, and `Pose mode` during live tests.
- Fixed a regression where valid `pos_m` endpoint data could be skipped, causing a blank view even though UDP packets were arriving.
- Corrected the scanner semantics so tracked ArUco pose is treated as the scanner origin and the actual plotted point is the measured endpoint in front of the scanner.
- Resolved the "horizontal cylinder around the user" issue by preferring endpoint data (`pos_m`) over scanner origin data when plotting the point cloud.

### Current understanding after live testing on 4/20/26
- ArUco markers are actively used when the camera-side detector is running and sending packets into `tools/send_sensor_data_udp.py` on the configured ArUco UDP port.
- ArUco improves accuracy by providing a tracked scanner origin that reduces IMU-only drift and makes first-person room/object scanning more reliable.
- If ArUco is not available, the system falls back to IMU orientation plus TF-Luna distance, which is enough for orientation-driven plotting but is less accurate for real spatial alignment.

### Next steps after today's fixes
- Run another live scan with ArUco visible in the camera feed and confirm the Unity overlay reports the expected position source and pose mode.
- Measure and tune the physical beam/mount alignment only if remaining error is consistent after ArUco-assisted scanning.
- Once the scan behavior is stable, remove or hide the remaining legacy Unity correction controls to reduce misconfiguration risk.

