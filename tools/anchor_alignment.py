"""Compute alignment between camera-observed anchors and known world anchor positions.

Usage:
  python3 tools/anchor_alignment.py --observations test_outputs/anchors_YYYYMMDD_*.jsonl --known known_anchors.json

`known_anchors.json` should be a dict {id: [x,y,z], ...} in world meters.

The script loads observations (marker tvecs in camera frame) and computes a rigid
transform (rotation + translation) from camera frame to world frame using
Procrustes / Umeyama on matched anchors.
"""
import argparse
import json
import numpy as np
from pathlib import Path


def load_observations(paths):
    obs = {}
    for p in paths:
        with open(p) as fh:
            for line in fh:
                rec = json.loads(line)
                ts = rec.get("timestamp")
                for m in rec.get("markers", []):
                    if "tvec" in m:
                        obs.setdefault(m["id"], []).append((ts, np.array(m["tvec"])))
    return obs


def umeyama(src, dst):
    # src, dst: Nx3 arrays. returns R, t
    assert src.shape == dst.shape
    mu_src = src.mean(axis=0)
    mu_dst = dst.mean(axis=0)
    src_c = src - mu_src
    dst_c = dst - mu_dst
    cov = src_c.T @ dst_c / src.shape[0]
    U, S, Vt = np.linalg.svd(cov)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = U @ Vt
    t = mu_dst - R @ mu_src
    return R, t


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", nargs="+", required=True)
    parser.add_argument("--known", required=True, help="JSON file mapping id->[x,y,z]")
    args = parser.parse_args()

    obs = load_observations(args.observations)
    known = json.load(open(args.known))

    # For each marker id, pick the most recent observed tvec
    ids = []
    cam_pts = []
    world_pts = []
    for mid, samples in obs.items():
        if str(mid) not in known and mid not in known:
            continue
        # choose latest sample
        samples.sort(key=lambda x: x[0])
        tvec = samples[-1][1]
        ids.append(mid)
        cam_pts.append(tvec)
        world_pts.append(np.array(known.get(str(mid), known.get(mid))))

    if len(cam_pts) < 3:
        raise SystemExit("Need at least 3 anchors with known world positions to compute alignment")

    src = np.vstack(cam_pts)
    dst = np.vstack(world_pts)

    R, t = umeyama(src, dst)
    out = {"R": R.tolist(), "t": t.tolist(), "ids": ids}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
