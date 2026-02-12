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