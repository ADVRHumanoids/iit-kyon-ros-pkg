#!/usr/bin/env python3
"""Writes config/hesai_qt128_occluder.stl, the lidar-only occluder of config/lidar_qt128.xml.

The occluder is kyon's pelvis visual mesh in imu_link, without its faces within --bay m of the
QT128 (the lidar bay) and without the faces the sensor cannot see. The sensor pose is the
hesai_qt128 site of lidar_qt128.xml. Run it in the xbot2_mujoco environment after changing the
pelvis mesh or the sensor pose, then reinstall kyon_mujoco:

  python3 make_qt128_occluder.py [--bay 0.15] [--output <kyon_mujoco>/config/hesai_qt128_occluder.stl]
"""
import argparse
import os
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from ament_index_python.packages import get_package_share_directory
from xbot2_py_mujoco.mjcf_tools import MjcfGenerator

XACRO_ARGS = ["floating_joint:=true", "upper_body:=false", "legs:=true", "varta:=true"]
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")


def pelvis_mesh_in_imu_link():
    """Vertices (in imu_link) and faces of the pelvis visual mesh."""
    urdf = subprocess.run(
        ["xacro", os.path.join(get_package_share_directory("kyon_urdf"), "urdf", "kyon_robot.urdf.xacro"),
         *XACRO_ARGS], capture_output=True, text=True, check=True).stdout
    with tempfile.TemporaryDirectory() as tmp:
        model = mujoco.MjModel.from_xml_string(
            MjcfGenerator(name="kyon", urdf_str=urdf, output_dir=tmp).generate_mjcf_string())
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    pelvis = model.body("pelvis").id
    visual = [g for g in range(model.ngeom) if model.geom_bodyid[g] == pelvis
              and model.geom_group[g] == 1 and model.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH]
    if len(visual) != 1:
        raise RuntimeError(f"expected one pelvis visual mesh, found {len(visual)}")
    g = visual[0]
    mesh = model.geom_dataid[g]
    verts = model.mesh_vert[model.mesh_vertadr[mesh]:model.mesh_vertadr[mesh] + model.mesh_vertnum[mesh]]
    faces = model.mesh_face[model.mesh_faceadr[mesh]:model.mesh_faceadr[mesh] + model.mesh_facenum[mesh]]
    world = verts @ data.geom_xmat[g].reshape(3, 3).T + data.geom_xpos[g]
    imu = data.body("imu_link")
    return (world - imu.xpos) @ imu.xmat.reshape(3, 3), faces


def sensor_position(lidar_xml):
    site = ET.parse(lidar_xml).getroot().find("reference/site[@name='hesai_qt128']")
    return np.array([float(v) for v in site.get("pos").split()])


def visible_faces(verts, faces, sensor):
    """Faces whose centroid, or a point near one of its corners, the sensor sees."""
    spec = mujoco.MjSpec()
    spec.add_mesh(name="m", uservert=verts.ravel().tolist(), userface=faces.ravel().tolist(),
                  inertia=mujoco.mjtMeshInertia.mjMESH_INERTIA_SHELL)
    spec.worldbody.add_geom(type=mujoco.mjtGeom.mjGEOM_MESH, meshname="m")
    model = spec.compile()
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    tri = verts[faces]
    centroid = tri.mean(1)
    visible = np.zeros(len(faces), bool)
    for points in [centroid] + [0.8 * tri[:, k] + 0.2 * centroid for k in range(3)]:
        direction = points - sensor
        dist = np.linalg.norm(direction, axis=1)
        direction /= dist[:, None]
        geom = np.zeros(len(points), np.int32)
        hit = np.zeros(len(points))
        mujoco.mj_multiRay(model, data, sensor, direction.ravel(), None, 1, -1, geom, hit, None,
                           len(points), 10.0)
        visible |= (geom == 0) & (hit > dist - 2e-3)
    return visible


def write_stl(path, verts, faces):
    with open(path, "wb") as f:
        f.write(b"kyon pelvis visual mesh minus the QT128 bay, imu_link frame".ljust(80, b" "))
        f.write(struct.pack("<I", len(faces)))
        for tri in verts[faces]:
            normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            normal /= np.linalg.norm(normal) or 1.0
            f.write(struct.pack("<12fH", *normal, *tri.ravel(), 0))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bay", type=float, default=0.15, help="radius of the removed lidar bay (m)")
    parser.add_argument("--lidar-xml", default=os.path.join(CONFIG_DIR, "lidar_qt128.xml"))
    parser.add_argument("--output", default=os.path.join(CONFIG_DIR, "hesai_qt128_occluder.stl"))
    args = parser.parse_args()

    verts, faces = pelvis_mesh_in_imu_link()
    sensor = sensor_position(args.lidar_xml)
    total = len(faces)
    faces = faces[(np.linalg.norm(verts[faces] - sensor, axis=2) > args.bay).all(1)]
    faces = faces[visible_faces(verts, faces, sensor)]
    used = np.unique(faces)
    remap = np.full(len(verts), -1)
    remap[used] = np.arange(len(used))
    write_stl(args.output, verts[used], remap[faces])
    print(f"{args.output}: {len(faces)} of {total} faces")


if __name__ == "__main__":
    main()
