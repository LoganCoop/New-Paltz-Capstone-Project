#!/usr/bin/env python3
"""
Simple UDP test sender for LiDAR VR Point Cloud
Sends mock sensor data to test rendering without hardware
"""
import socket
import json
import time
import math

# UDP config
QUEST_IP = "192.168.0.232"  # Quest 3 IP
UDP_PORT = 5005

def get_test_data(frame_num):
    """Generate test point cloud data"""
    timestamp = time.time()
    
    # Generate a spiral of points at varying distances
    num_points = 100
    points = []
    
    for i in range(num_points):
        angle = (i / num_points) * 4 * math.pi
        radius = 0.5 + 1.5 * (i / num_points)  # 0.5m to 2m distance
        z = 1.5 * math.sin(angle * 0.5)
        
        # Convert to TF-Luna format (distance in cm from sensor)
        distance_cm = int(radius * 100)
        
        points.append({
            "distance": distance_cm,
            "strength": 200 + (i % 55),
            "angle_x": angle,
            "angle_y": z,
        })
    
    # Mock BNO055 quaternion (eye tracking orientation)
    w = math.cos(frame_num * 0.01)
    x = math.sin(frame_num * 0.005)
    y = 0.0
    z_quat = math.sin(frame_num * 0.01)
    
    # Normalize quaternion
    qlen = math.sqrt(w*w + x*x + y*y + z_quat*z_quat)
    if qlen > 0:
        w /= qlen
        x /= qlen
        y /= qlen
        z_quat /= qlen
    
    packet = {
        "tfluna": {
            "timestamp": timestamp,
            "distance_cm": 150,
            "strength": 250,
            "temperature_c": 25.0
        },
        "bno055": {
            "timestamp": timestamp,
            "qw": w,
            "qx": x,
            "qy": y,
            "qz": z_quat
        },
        "points": points
    }
    
    return packet

def main():
    print(f"UDP Test Sender - Sending to {QUEST_IP}:{UDP_PORT}")
    print("Press Ctrl+C to stop\n")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    frame = 0
    
    try:
        while True:
            data = get_test_data(frame)
            packet_json = json.dumps(data)
            
            try:
                sock.sendto(packet_json.encode(), (QUEST_IP, UDP_PORT))
                print(f"Frame {frame}: sent {len(data.get('points', []))} points, "
                      f"distance={data['tfluna']['distance_cm']}cm")
            except Exception as e:
                print(f"Send error: {e}")
            
            frame += 1
            time.sleep(0.033)  # ~30 FPS
            
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
