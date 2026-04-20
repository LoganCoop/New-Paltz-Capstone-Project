"""Convert ArUco anchor JSONL into timestamped camera poses and movement deltas.

Usage examples:

# Process latest anchors file in test_outputs
python3 tools/anchors_to_movement.py --anchors latest

# Process a specified anchors file and write movements
python3 tools/anchors_to_movement.py --anchors test_outputs/anchors_20260413_123000.jsonl --out test_outputs/movements.jsonl --marker-map markers.json

Marker map JSON format (optional):
{
  "1": { "pos": [0,0,0], "quat": [1,0,0,0] },
  "2": { "pos": [1,0,0], "quat": [1,0,0,0] }
}

If no marker map is provided, the script will use the first observed marker as the world origin.
"""
from pathlib import Path
import argparse
import json
import time
import math
import numpy as np
import cv2


def rvec_tvec_to_transform(rvec, tvec):
    R, _ = cv2.Rodrigues(np.array(rvec, dtype=float))
    t = np.array(tvec, dtype=float).reshape(3)
    T = np.eye(4, dtype=float)
    T[0:3, 0:3] = R
    T[0:3, 3] = t
    return T


def transform_to_pos_quat(T):
    t = T[0:3, 3].tolist()
    R = T[0:3, 0:3]
    # convert rotation matrix to quaternion (w,x,y,z)
    qw = math.sqrt(max(0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2.0
    qx = math.copysign(math.sqrt(max(0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2.0, R[2, 1] - R[1, 2])
    qy = math.copysign(math.sqrt(max(0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2.0, R[0, 2] - R[2, 0])
    qz = math.copysign(math.sqrt(max(0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2.0, R[1, 0] - R[0, 1])
    q = [qw, qx, qy, qz]
    return t, q


def quat_normalize(q):
    q = np.array(q, dtype=float)
    n = np.linalg.norm(q)
    if n == 0:
        return [1.0, 0.0, 0.0, 0.0]
    return (q / n).tolist()


def average_transforms(transforms):
    # transforms: list of 4x4 numpy arrays
    if len(transforms) == 0:
        return None
    # average positions
    positions = np.array([T[0:3, 3] for T in transforms])
    avg_pos = positions.mean(axis=0)
    # average quaternions by normalized sum
    quats = []
    for T in transforms:
        _, q = transform_to_pos_quat(T)
        quats.append(q)
    qsum = np.sum(np.array(quats), axis=0)
    qavg = quat_normalize(qsum)
    # reconstruct transform
    qw, qx, qy, qz = qavg
    # build rotation matrix from quaternion
    R = np.array([
        [1 - 2 * (qy**2 + qz**2), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
        [2 * (qx * qy + qz * qw), 1 - 2 * (qx**2 + qz**2), 2 * (qy * qz - qx * qw)],
        [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx**2 + qy**2)],
    ])
    T = np.eye(4, dtype=float)
    T[0:3, 0:3] = R
    T[0:3, 3] = avg_pos
    return T


def load_marker_map(path):
    with open(path, 'r') as fh:
        data = json.load(fh)
    marker_map = {}
    for k, v in data.items():
        kid = int(k)
        if isinstance(v, dict) and 'pos' in v and 'quat' in v:
            pos = v['pos']
            qw, qx, qy, qz = v['quat']
            # build transform
            qw, qx, qy, qz = float(qw), float(qx), float(qy), float(qz)
            R = np.array([
                [1 - 2 * (qy**2 + qz**2), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
                [2 * (qx * qy + qz * qw), 1 - 2 * (qx**2 + qz**2), 2 * (qy * qz - qx * qw)],
                [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx**2 + qy**2)],
            ])
            T = np.eye(4, dtype=float)
            T[0:3, 0:3] = R
            T[0:3, 3] = np.array(v['pos'], dtype=float)
            marker_map[kid] = T
        elif isinstance(v, list) and len(v) == 16:
            M = np.array(v, dtype=float).reshape((4, 4))
            marker_map[kid] = M
        else:
            raise RuntimeError('Unsupported marker map format for id: %s' % k)
    return marker_map


def find_latest_anchors_file(dirpath):
    p = Path(dirpath)
    files = sorted(p.glob('anchors_*.jsonl'))
    if not files:
        return None
    return files[-1]


def process_anchors(anchors_path, marker_map=None, out_path=None):
    anchors_path = Path(anchors_path)
    if out_path is None:
        ts = time.strftime('%Y%m%d_%H%M%S')
        out_path = anchors_path.parent / f'movements_{ts}.jsonl'
    else:
        out_path = Path(out_path)

    last_camera_T = None
    with open(anchors_path, 'r') as inf, open(out_path, 'w') as outf:
        for line in inf:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            ts = rec.get('timestamp', time.time())
            markers = rec.get('markers', [])
            transforms_world_cam = []
            used_ids = []
            for m in markers:
                if 'tvec' not in m or 'rvec' not in m:
                    continue
                mid = int(m['id'])
                if marker_map is None and len(transforms_world_cam) == 0:
                    # will set origin later
                    pass
                if marker_map is None and mid not in marker_map if marker_map else False:
                    # marker not in map
                    pass
                # T_cam_marker from rvec/tvec
                T_cam_marker = rvec_tvec_to_transform(m['rvec'], m['tvec'])
                # invert -> T_marker_cam
                T_marker_cam = np.linalg.inv(T_cam_marker)
                if marker_map and mid in marker_map:
                    T_world_marker = marker_map[mid]
                    T_world_cam = T_world_marker @ T_marker_cam
                    transforms_world_cam.append(T_world_cam)
                    used_ids.append(mid)
                else:
                    # cannot resolve without marker_map; skip
                    continue

            if len(transforms_world_cam) == 0:
                # nothing to do for this record
                continue

            # average across multiple visible markers
            T_world_cam = average_transforms(transforms_world_cam)
            pos, quat = transform_to_pos_quat(T_world_cam)
            out_rec = {
                'timestamp': ts,
                'camera_pos': pos,
                'camera_quat': quat,
                'marker_ids_used': used_ids,
            }
            if last_camera_T is None:
                out_rec['delta_pos'] = [0.0, 0.0, 0.0]
                out_rec['delta_dist'] = 0.0
            else:
                last_pos = last_camera_T[0:3, 3]
                delta = np.array(pos) - last_pos
                out_rec['delta_pos'] = delta.tolist()
                out_rec['delta_dist'] = float(np.linalg.norm(delta))
            outf.write(json.dumps(out_rec) + '\n')
            outf.flush()
            last_camera_T = T_world_cam
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Convert anchors JSONL into movement deltas')
    parser.add_argument('--anchors', default='latest', help='Path to anchors jsonl or "latest" to auto-pick')
    parser.add_argument('--marker-map', default=None, help='JSON file mapping marker id to world transform')
    parser.add_argument('--out', default=None, help='Output movements jsonl path')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    if args.anchors == 'latest':
        anchors_file = find_latest_anchors_file(project_root / 'test_outputs')
        if anchors_file is None:
            raise SystemExit('No anchors files in test_outputs')
    else:
        anchors_file = Path(args.anchors)
        if not anchors_file.exists():
            raise SystemExit('Anchors file not found: %s' % anchors_file)

    marker_map = None
    if args.marker_map:
        marker_map = load_marker_map(args.marker_map)

    out_path = process_anchors(anchors_file, marker_map=marker_map, out_path=args.out)
    print('Wrote movements to', out_path)


if __name__ == '__main__':
    main()
