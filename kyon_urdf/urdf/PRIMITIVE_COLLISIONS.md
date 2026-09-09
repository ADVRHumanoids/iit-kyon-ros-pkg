# Primitive collision model

This branch keeps the visual and inertial descriptions from `ros2` and adds the
`primitive_collisions` xacro argument. It defaults to `false`, selecting the
approximately 100-triangle meshes imported from `crzz-dev`'s
`collision_simplified` directory. Setting it to `true` replaces limb meshes
with fitted boxes. Wheels remain analytic cylinders in both modes so their
smooth collision representation is rotationally symmetric. Wheel joints also
remain continuous; fake +/-1e9 radian limits are intentionally absent.

The pelvis is the sole mesh exception. Its collision mesh is already reduced
to 100 triangles and converts to a 100-plane iDCOL smooth convex polytope in
roughly 0.5 seconds on the development machine. A single enclosing box was
tested, but introduced false pelvis--shoulder collisions in the nominal
wheeled-manipulator posture.

The primitive dimensions started from axis-aligned mesh fits and were reduced
where the enclosing fit was visibly too conservative. The reduced hip-pitch
box is shifted toward the link's exterior surface instead of retaining the
center of the full-width mesh fit. The ankle-yaw box is shifted upward and
shortened to clear the wheel, and its transverse dimensions match those of the
knee-pitch box. Hip-roll collision is omitted in primitive mode because the
pelvis and hip-pitch shapes already cover that region. The approximation is
deliberately simple and inexpensive; it should be validated in the
configurations used by a controller before enabling broad self-collision
checking.
