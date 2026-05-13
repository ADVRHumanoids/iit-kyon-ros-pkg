#!/usr/bin/env python3
"""
Example usage of the terrain generator
Demonstrates different configurations and terrain types
"""

from terrain_generator import TerrainGenerator, TerrainType


def example_simple_grid():
    """Generate a simple 3x3 grid with all terrain types"""
    print("Generating simple 3x3 terrain grid...")
    
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
    generator.save('simple_terrain_grid.xml')
    print("Done! File saved as: simple_terrain_grid.xml")


def example_large_grid():
    """Generate a larger 5x5 grid with varied terrains"""
    print("Generating large 5x5 terrain grid...")
    
    generator = TerrainGenerator(
        grid_rows=5,
        grid_cols=5,
        terrain_size=4.0,
        terrain_spacing=0.3,
        base_height=-1.0
    )
    
    # Create a diverse layout
    terrain_layout = [
        [TerrainType.FLAT, TerrainType.NOISY_HEIGHTFIELD, TerrainType.PYRAMID_BOXES, 
         TerrainType.STAIRS, TerrainType.RANDOM_BOXES],
        [TerrainType.NOISY_HEIGHTFIELD, TerrainType.RANDOM_BOXES, TerrainType.FLAT, 
         TerrainType.PYRAMID_BOXES, TerrainType.STAIRS],
        [TerrainType.STAIRS, TerrainType.FLAT, TerrainType.NOISY_HEIGHTFIELD, 
         TerrainType.RANDOM_BOXES, TerrainType.PYRAMID_BOXES],
        [TerrainType.PYRAMID_BOXES, TerrainType.STAIRS, TerrainType.RANDOM_BOXES, 
         TerrainType.NOISY_HEIGHTFIELD, TerrainType.FLAT],
        [TerrainType.RANDOM_BOXES, TerrainType.PYRAMID_BOXES, TerrainType.STAIRS, 
         TerrainType.FLAT, TerrainType.NOISY_HEIGHTFIELD]
    ]
    
    generator.generate_grid(terrain_layout, output_dir='./terrain_assets')
    generator.save('large_terrain_grid.xml')
    print("Done! File saved as: large_terrain_grid.xml")


def example_progressive_difficulty():
    """Generate terrains with progressive difficulty"""
    print("Generating progressive difficulty terrain grid...")
    
    generator = TerrainGenerator(
        grid_rows=3,
        grid_cols=5,
        terrain_size=5.0,
        terrain_spacing=0.5,
        base_height=-1.0
    )
    
    # Easy -> Medium -> Hard progression
    terrain_layout = [
        # Easy row
        [TerrainType.FLAT, TerrainType.FLAT, TerrainType.FLAT, 
         TerrainType.FLAT, TerrainType.FLAT],
        # Medium row
        [TerrainType.STAIRS, TerrainType.NOISY_HEIGHTFIELD, TerrainType.RANDOM_BOXES,
         TerrainType.NOISY_HEIGHTFIELD, TerrainType.STAIRS],
        # Hard row
        [TerrainType.PYRAMID_BOXES, TerrainType.RANDOM_BOXES, TerrainType.NOISY_HEIGHTFIELD,
         TerrainType.PYRAMID_BOXES, TerrainType.RANDOM_BOXES]
    ]
    
    generator.generate_grid(terrain_layout, output_dir='./terrain_assets')
    generator.save('progressive_terrain_grid.xml')
    print("Done! File saved as: progressive_terrain_grid.xml")


def example_custom_parameters():
    """Generate terrain with custom parameters for each type"""
    print("Generating terrain with custom parameters...")
    
    generator = TerrainGenerator(
        grid_rows=2,
        grid_cols=3,
        terrain_size=6.0,
        terrain_spacing=1.0,
        base_height=-1.0
    )
    
    # Add terrains individually with custom parameters
    
    # Row 0, Col 0: Flat with high friction
    generator.add_flat_terrain(0, 0, friction=1.2)
    
    # Row 0, Col 1: Noisy heightfield with large amplitude
    generator.add_noisy_heightfield(0, 1, amplitude=0.3, frequency=8.0, 
                                   output_dir='./terrain_assets')
    
    # Row 0, Col 2: Tall pyramid
    generator.add_pyramid_boxes(0, 2, num_levels=7, max_height=0.8)
    
    # Row 1, Col 0: Many small stairs
    generator.add_stairs(1, 0, num_steps=12, step_height=0.05, step_depth=0.3)
    
    # Row 1, Col 1: Dense random boxes
    generator.add_random_boxes(1, 1, num_boxes=50, min_size=0.05, 
                              max_size=0.15, max_height=0.2, seed=42)
    
    # Row 1, Col 2: Large random obstacles
    generator.add_random_boxes(1, 2, num_boxes=10, min_size=0.3, 
                              max_size=0.5, max_height=0.5, seed=123)
    
    generator.save('custom_terrain_grid.xml')
    print("Done! File saved as: custom_terrain_grid.xml")


def example_heightfield_variations():
    """Generate different heightfield variations"""
    print("Generating heightfield variations...")
    
    generator = TerrainGenerator(
        grid_rows=2,
        grid_cols=3,
        terrain_size=5.0,
        terrain_spacing=0.5,
        base_height=-1.0
    )
    
    # Different heightfield configurations
    generator.add_noisy_heightfield(0, 0, amplitude=0.05, frequency=3.0, 
                                   output_dir='./terrain_assets')
    generator.add_noisy_heightfield(0, 1, amplitude=0.15, frequency=5.0,
                                   output_dir='./terrain_assets')
    generator.add_noisy_heightfield(0, 2, amplitude=0.25, frequency=8.0,
                                   output_dir='./terrain_assets')
    
    generator.add_noisy_heightfield(1, 0, amplitude=0.1, frequency=2.0,
                                   output_dir='./terrain_assets')
    generator.add_noisy_heightfield(1, 1, amplitude=0.2, frequency=10.0,
                                   output_dir='./terrain_assets')
    generator.add_noisy_heightfield(1, 2, amplitude=0.15, frequency=6.0,
                                   output_dir='./terrain_assets')
    
    generator.save('heightfield_variations.xml')
    print("Done! File saved as: heightfield_variations.xml")


if __name__ == '__main__':
    print("=== Terrain Generator Examples ===\n")
    
    # Run all examples
    example_simple_grid()
    print()
    
    example_large_grid()
    print()
    
    example_progressive_difficulty()
    print()
    
    example_custom_parameters()
    print()
    
    example_heightfield_variations()
    print()
    
    print("=== All examples completed! ===")
    print("\nYou can now load these MJCF files in MuJoCo.")
    print("Heightfield images are saved in the './terrain_assets' directory.")
