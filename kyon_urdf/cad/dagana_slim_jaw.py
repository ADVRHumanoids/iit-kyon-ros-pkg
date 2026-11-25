#!/usr/bin/env python3
"""Printable jaw for the dagana, the physical counterpart of the boxy_slim model with its tooth.

The jaw is a 30 mm wide finger standing on a bridge that sits on top of the dagana's actuator. Two legs, one at
each end of the bridge, come down along the actuator's sides, and each is screwed to the actuator by two M3
screws going across the width, with their heads sunk in counterbores so that they are flush with the legs.
At the finger's tip, on the gripping face, is the tooth: a wedge whose end is flush with the tip and whose slope
goes back to the face.

Frame (mm): x across the width, centred on the finger; y through the thickness, the gripping face is y=0 and the
back y=thickness (the tooth sticks out towards -y); z along the jaw, z=0 is the bridge's underside (the top of the
actuator), the legs go down to z=-leg_length and the tip is at z=tip_height.

The back face is flat over the whole part: print it lying on its back, with the tooth pointing up.

It writes the jaw as STEP and STL, and also as STL without the tooth (<out>_no_tooth.stl): kyon_dagana.urdf.xacro
uses the two STLs as the boxy_slim jaws' visuals, with and without dagana_teeth.

Usage (CadQuery is not needed in the workspace's venvs, uv fetches it):
    uv run --no-project --with cadquery python3 dagana_slim_jaw.py                       # writes dagana_slim_jaw*.step/.stl here
    uv run --no-project --with cadquery python3 dagana_slim_jaw.py --set bridge_thickness=10 --set fit_clearance=0.3
    uv run --no-project --with cadquery python3 dagana_slim_jaw.py --list                # prints the parameters
"""
from __future__ import annotations
import argparse
import dataclasses
from pathlib import Path
import cadquery as cq


@dataclasses.dataclass
class JawParams:
    """All in mm."""
    finger_width: float = 30.0       # across the jaw, x
    thickness: float = 27.0          # of the finger, the bridge and the legs, y
    tip_height: float = 110.0        # the tip above the bridge's underside
    bridge_thickness: float = 8.0
    leg_width: float = 8.0           # each leg, along x
    leg_gap: float = 71.9            # between the legs: the actuator's width
    fit_clearance: float = 0.2       # added to leg_gap, so that the legs slide over the actuator
    leg_length: float = 10.0         # the legs below the bridge's underside
    hole_d: float = 3.4              # M3 clearance
    hole_height: float = 5.0         # the holes' centres above the legs' bottom
    hole_back_offset: float = 5.0    # the first hole's centre from the back face
    hole_pitch: float = 14.0         # between the two holes of a leg, along y
    counterbore_d: float = 6.0       # M3 socket head: 5.5 mm
    counterbore_depth: float = 3.2   # M3 socket head: 3 mm
    tooth_height: float = 10.0       # how far the tooth's end sticks out of the gripping face
    tooth_length: float = 10.0       # where the tooth's slope meets the face, from the tip (45 degrees if equal to tooth_height)

    def check(self):
        if self.hole_back_offset + self.hole_pitch + self.counterbore_d/2 > self.thickness:
            raise ValueError("The second hole's counterbore goes past the gripping face")
        if self.hole_back_offset < self.counterbore_d/2:
            raise ValueError("The first hole's counterbore goes past the back face")
        if not (0 < self.hole_height - self.counterbore_d/2 and self.hole_height + self.counterbore_d/2 < self.leg_length):
            raise ValueError("The counterbores do not fit in the legs' length below the bridge")
        if self.counterbore_depth >= self.leg_width:
            raise ValueError("The counterbores are deeper than the legs")
        if self.finger_width > self.leg_gap:
            raise ValueError("The finger is wider than the gap between the legs")


def box(x0, x1, y0, y1, z0, z1) -> cq.Workplane:
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def make_jaw(p : JawParams, with_tooth : bool = True) -> cq.Workplane:
    p.check()
    t = p.thickness
    gap_half = (p.leg_gap + p.fit_clearance)/2
    outer_half = gap_half + p.leg_width
    jaw = box(-outer_half, outer_half, 0, t, 0, p.bridge_thickness)                          # bridge
    jaw = jaw.union(box(-outer_half, -gap_half, 0, t, -p.leg_length, 0))                    # legs
    jaw = jaw.union(box(gap_half, outer_half, 0, t, -p.leg_length, 0))
    jaw = jaw.union(box(-p.finger_width/2, p.finger_width/2, 0, t, p.bridge_thickness, p.tip_height))  # finger
    if with_tooth:
        # its profile in the y-z plane, extruded across the finger's width
        tooth = (cq.Workplane("YZ").polyline([(0, p.tip_height), (-p.tooth_height, p.tip_height), (0, p.tip_height - p.tooth_length)])
                 .close().extrude(p.finger_width).translate((-p.finger_width/2, 0, 0)))
        jaw = jaw.union(tooth)
    # holes across each leg, with the counterbore on the leg's outer side
    z = -p.leg_length + p.hole_height
    for y in (t - p.hole_back_offset, t - p.hole_back_offset - p.hole_pitch):
        for side in (-1, 1):
            through = cq.Solid.makeCylinder(p.hole_d/2, p.leg_width + 2, cq.Vector(side*(gap_half - 1), y, z), cq.Vector(side, 0, 0))
            counterbore = cq.Solid.makeCylinder(p.counterbore_d/2, p.counterbore_depth + 1,
                                                cq.Vector(side*(outer_half + 1), y, z), cq.Vector(-side, 0, 0))
            jaw = jaw.cut(cq.Workplane().add(through)).cut(cq.Workplane().add(counterbore))
    return jaw


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE", help="Override a parameter, in mm")
    ap.add_argument("--list", action="store_true", help="Print the parameters and exit")
    ap.add_argument("--out", default=str(Path(__file__).with_suffix("")), help="Output path without extension")
    args = ap.parse_args()
    params = JawParams()
    names = {f.name for f in dataclasses.fields(JawParams)}
    for item in args.set:
        name, _, value = item.partition("=")
        if name not in names:
            raise SystemExit(f"Unknown parameter '{name}', the parameters are: {', '.join(sorted(names))}")
        setattr(params, name, float(value))
    if args.list:
        for name, value in dataclasses.asdict(params).items():
            print(f"{name} = {value}")
        return
    jaw = make_jaw(params)
    cq.exporters.export(jaw, args.out + ".step")
    cq.exporters.export(jaw, args.out + ".stl", tolerance=0.01, angularTolerance=0.1)
    cq.exporters.export(make_jaw(params, with_tooth=False), args.out + "_no_tooth.stl", tolerance=0.01, angularTolerance=0.1)
    bb = jaw.val().BoundingBox()
    print(f"Wrote {args.out}.step, {args.out}.stl and {args.out}_no_tooth.stl: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, "
          f"volume {jaw.val().Volume()/1000:.1f} cm3")


if __name__ == "__main__":
    main()
