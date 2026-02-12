import socket
import threading
import time
import json
import serial
import board
import busio
import adafruit_bno055

# TF-Luna config
TF_LUNA_PORT = "/dev/serial0"
TF_LUNA_BAUD = 115200
TF_LUNA_TIMEOUT = 1.0

# BNO055 config
BNO055_ADDRESS = 0x29  # Default I2C address
BNO055_RATE_HZ = 10.0

# UDP config
UDP_IP = "192.168.0.198"  # Change to your Unity machine's IP
UDP_PORT = 5005


def read_tfluna(port_path, baud, timeout, result_dict):
    FRAME_HEADER = 0x59
    FRAME_LENGTH = 9
    with serial.Serial(port_path, baud, timeout=timeout) as port:
        while True:
            first = port.read(1)
            if not first or first[0] != FRAME_HEADER:
                continue
            second = port.read(1)
            if not second or second[0] != FRAME_HEADER:
                continue
            rest = port.read(FRAME_LENGTH - 2)
            if len(rest) != FRAME_LENGTH - 2:
                continue
            frame = bytes([FRAME_HEADER, FRAME_HEADER]) + rest
            checksum = sum(frame[0:8]) & 0xFF
            if checksum != frame[8]:
                continue
            distance_cm = frame[2] + (frame[3] << 8)
            strength = frame[4] + (frame[5] << 8)
            temp_raw = frame[6] + (frame[7] << 8)
            temperature_c = (temp_raw / 8.0) - 256.0
            result_dict['tfluna'] = {
                'timestamp': time.time(),
                'distance_cm': distance_cm,
                'strength': strength,
                'temperature_c': temperature_c
            }


def read_bno055(result_dict, address, rate_hz):
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_bno055.BNO055_I2C(i2c, address=address)
    interval = 1.0 / max(rate_hz, 0.1)
    while True:
        quat = sensor.quaternion
        if quat is not None:
            w, x, y, z = quat
            result_dict['bno055'] = {
                'timestamp': time.time(),
                'qw': w,
                'qx': x,
                'qy': y,
                'qz': z
            }
        time.sleep(interval)


def main():
    data = {}
    # Start sensor threads
    t1 = threading.Thread(target=read_tfluna, args=(TF_LUNA_PORT, TF_LUNA_BAUD, TF_LUNA_TIMEOUT, data), daemon=True)
    t2 = threading.Thread(target=read_bno055, args=(data, BNO055_ADDRESS, BNO055_RATE_HZ), daemon=True)
    t1.start()
    t2.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Sending UDP packets to {UDP_IP}:{UDP_PORT}")
    while True:
        if 'tfluna' in data and 'bno055' in data:
            packet = {
                'tfluna': data['tfluna'],
                'bno055': data['bno055']
            }
            msg = json.dumps(packet).encode('utf-8')
            sock.sendto(msg, (UDP_IP, UDP_PORT))
        time.sleep(0.05)  # 20 Hz


if __name__ == "__main__":
    main()
