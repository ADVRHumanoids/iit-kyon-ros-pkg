# MuJoCo Terrain Generator

A Python tool for generating complex terrains for robot locomotion testing in MuJoCo, similar to IsaacLab's rough terrain concept.

## Features

- **Grid-based terrain generation**: Create grids of different terrain types for systematic testing
- **Multiple terrain types**:
  - **Flat**: Simple flat planes with configurable friction
  - **Noisy Heightfield**: Procedurally generated heightfields with controllable amplitude and frequency
  - **Pyramid Boxes**: Step pyramid structures made of boxes
  - **Stairs**: Configurable stair terrain with adjustable step height and depth
  - **Random Boxes**: Randomly placed box obstacles with configurable size distributions

## Requirements

```bash
pip install numpy pillow
```

## Quick Start

### Using the Command-Line Interface

Generate a default 3x3 terrain grid:

```bash
cd /home/alaurenzi/code/ros2_ws/src/iit-kyon-ros-pkg/kyon_mujoco/src
python3 terrain_generator.py --output my_terrain.xml
```

With custom parameters:

```bash
python3 terrain_generator.py \
    --rows 5 \
    --cols 5 \
    --size 4.0 \
    --spacing 0.5 \
    --output large_terrain.xml \
    --output-dir ./terrain_assets
```

### Using the Python API

```python
from terrain_generator import TerrainGenerator, TerrainType

# Create a 3x3 terrain grid
generator = TerrainGenerator(
    grid_rows=3,
    grid_cols=3,
    terrain_size=5.0,
    terrain_spacing=0.5,
    base_height=-1.0
)

# Define terrain layout
terrain_layout = [
    [TerrainType.FLAT, TerrainType.NOISY_HEIGHTFIELD, TerrainType.PYRAMID_BOXES],
    [TerrainType.STAIRS, TerrainType.RANDOM_BOXES, TerrainType.FLAT],
    [TerrainType.PYRAMID_BOXES, TerrainType.NOISY_HEIGHTFIELD, TerrainType.STAIRS]
]

# Generate and save
generator.generate_grid(terrain_layout, output_dir='./terrain_assets')
generator.save('terrain_grid.xml')
```

### Running Examples

Several example configurations are provided:

```bash
cd /home/alaurenzi/code/ros2_ws/src/iit-kyon-ros-pkg/kyon_mujoco/src
python3 example_terrain_usage.py
```

This will generate:
- `simple_terrain_grid.xml` - Basic 3x3 grid with all terrain types
- `large_terrain_grid.xml` - Larger 5x5 grid with varied terrains
- `progressive_terrain_grid.xml` - Progressive difficulty layout
- `custom_terrain_grid.xml` - Custom parameters for each terrain
- `heightfield_variations.xml` - Different heightfield configurations

## Terrain Types

### 1. Flat Terrain

Simple flat plane with configurable friction.

```python
generator.add_flat_terrain(row=0, col=0, friction=0.6)
```

### 2. Noisy Heightfield

Procedurally generated heightfield using sinusoidal functions and random noise.

```python
generator.add_noisy_heightfield(
    row=0, col=1,
    amplitude=0.1,      # Maximum height variation (m)
    frequency=5.0,      # Frequency of noise pattern
    resolution=256,     # Resolution of heightfield (pixels)
    friction=0.6,
    output_dir='./terrain_assets'
)
```

The heightfield is saved as a PNG image in the specified output directory and referenced in the MJCF file.

### 3. Pyramid Boxes

Step pyramid structure made of stacked boxes.

```python
generator.add_pyramid_boxes(
    row=0, col=2,
    num_levels=5,      # Number of pyramid levels
    max_height=0.5,    # Maximum height of pyramid (m)
    friction=0.6
)
```

### 4. Stairs

Staircase terrain with configurable steps.

```python
generator.add_stairs(
    row=1, col=0,
    num_steps=8,       # Number of steps
    step_height=0.1,   # Height of each step (m)
    step_depth=0.4,    # Depth of each step (m)
    friction=0.6
)
```

### 5. Random Boxes

Randomly placed box obstacles.

```python
generator.add_random_boxes(
    row=1, col=1,
    num_boxes=20,      # Number of random boxes
    min_size=0.1,      # Minimum box size (m)
    max_size=0.3,      # Maximum box size (m)
    max_height=0.3,    # Maximum box height (m)
    friction=0.6,
    seed=42            # Random seed for reproducibility
)
```

## API Reference

### TerrainGenerator Class

```python
TerrainGenerator(
    grid_rows: int = 3,              # Number of rows in terrain grid
    grid_cols: int = 3,              # Number of columns in terrain grid
    terrain_size: float = 5.0,       # Size of each terrain patch (m)
    terrain_spacing: float = 0.5,    # Spacing between patches (m)
    base_height: float = -1.0        # Base height for terrain placement (m)
)
```

### Methods

- `add_flat_terrain(row, col, friction=0.6)` - Add a flat plane terrain
- `add_noisy_heightfield(row, col, amplitude=0.1, frequency=5.0, resolution=256, friction=0.6, output_dir='.')` - Add noisy heightfield
- `add_pyramid_boxes(row, col, num_levels=5, max_height=0.5, friction=0.6)` - Add pyramid structure
- `add_stairs(row, col, num_steps=8, step_height=0.1, step_depth=0.4, friction=0.6)` - Add stairs
- `add_random_boxes(row, col, num_boxes=20, min_size=0.1, max_size=0.3, max_height=0.3, friction=0.6, seed=None)` - Add random boxes
- `generate_grid(terrain_types, **kwargs)` - Generate entire grid from layout
- `save(filename, pretty=True)` - Save MJCF file

## Loading in MuJoCo

### Including in Existing World

You can include the generated terrain in your existing MuJoCo world file:

```xml
<mujoco>
    <include file="terrain_grid.xml"/>
    
    <!-- Your robot and other elements -->
    <worldbody>
        <body name="robot">
            <!-- Robot definition -->
        </body>
    </worldbody>
</mujoco>
```

### Standalone Usage

The generated MJCF files are complete and can be loaded directly in MuJoCo:

```bash
python -m mujoco.viewer terrain_grid.xml
```

### With ROS 2

Update your launch file to use the generated terrain:

```python
# In your launch file
world_file = os.path.join(
    get_package_share_directory('kyon_mujoco'),
    'config',
    'terrain_grid.xml'
)
```

## Advanced Usage

### Progressive Difficulty Training

Create terrains with increasing difficulty for curriculum learning:

```python
generator = TerrainGenerator(grid_rows=3, grid_cols=5, terrain_size=5.0)

terrain_layout = [
    # Easy row - mostly flat
    [TerrainType.FLAT, TerrainType.FLAT, TerrainType.FLAT, 
     TerrainType.FLAT, TerrainType.FLAT],
    # Medium row - gentle obstacles
    [TerrainType.STAIRS, TerrainType.NOISY_HEIGHTFIELD, TerrainType.RANDOM_BOXES,
     TerrainType.NOISY_HEIGHTFIELD, TerrainType.STAIRS],
    # Hard row - challenging terrain
    [TerrainType.PYRAMID_BOXES, TerrainType.RANDOM_BOXES, TerrainType.NOISY_HEIGHTFIELD,
     TerrainType.PYRAMID_BOXES, TerrainType.RANDOM_BOXES]
]

generator.generate_grid(terrain_layout, output_dir='./terrain_assets')
generator.save('progressive_terrain.xml')
```

### Custom Terrain Combinations

Mix and match terrain types with custom parameters:

```python
generator = TerrainGenerator(grid_rows=2, grid_cols=2, terrain_size=6.0)

# Fine-tune each terrain individually
generator.add_noisy_heightfield(0, 0, amplitude=0.3, frequency=8.0, 
                               output_dir='./terrain_assets')
generator.add_pyramid_boxes(0, 1, num_levels=7, max_height=0.8)
generator.add_stairs(1, 0, num_steps=12, step_height=0.05, step_depth=0.3)
generator.add_random_boxes(1, 1, num_boxes=50, min_size=0.05, max_size=0.15, seed=42)

generator.save('custom_mix.xml')
```

## File Structure

After running the generator, you'll have:

```
kyon_mujoco/
├── src/
│   ├── terrain_generator.py      # Main generator class
│   ├── example_terrain_usage.py  # Usage examples
│   └── terrain_assets/           # Generated heightfield images
│       ├── heightfield_0.png
│       ├── heightfield_1.png
│       └── ...
├── config/
│   ├── terrain_grid.xml          # Generated MJCF file
│   └── ...
```

## Tips and Best Practices

1. **Heightfield Resolution**: Higher resolution (512+) provides smoother terrain but increases file size
2. **Grid Spacing**: Leave adequate spacing between terrains to prevent collision overlap
3. **Friction Values**: Typical values range from 0.4 (slippery) to 1.2 (high traction)
4. **Random Seeds**: Use consistent seeds for reproducible random terrain generation
5. **Terrain Size**: Match terrain size to your robot's stride length and capabilities
6. **Output Directory**: Keep heightfield images organized in a dedicated directory

## Troubleshooting

### Heightfield images not loading

Ensure the `output_dir` path is relative to where MuJoCo will be run, or use absolute paths:

```python
import os
output_dir = os.path.join(os.path.dirname(__file__), 'terrain_assets')
generator.add_noisy_heightfield(0, 0, output_dir=output_dir)
```

### Collisions between terrain patches

Increase the `terrain_spacing` parameter:

```python
generator = TerrainGenerator(terrain_spacing=1.0)  # Larger spacing
```

### Robot falling through terrain

Check that `base_height` aligns with your robot's spawn position and adjust as needed.

## Future Enhancements

Potential additions:
- Slopes and ramps
- Gap/pit obstacles
- Moving platforms
- Deformable terrain
- Procedural caves/tunnels
- Custom texture mapping

## License

Part of the iit-kyon-ros-pkg project.

## References

- [MuJoCo Documentation](https://mujoco.readthedocs.io/)
- [IsaacLab Rough Terrain](https://isaac-sim.github.io/IsaacLab/)
