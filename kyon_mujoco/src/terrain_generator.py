#!/usr/bin/env python3
"""
Terrain Generator for MuJoCo
Generates complex terrains for robot locomotion testing, similar to IsaacLab's rough terrain.
Creates a grid of terrains with different types: flat, noisy heightfield, and pyramid-style boxes.
"""

import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
from enum import Enum
import argparse
import os
from typing import List, Tuple, Optional
from PIL import Image


class TerrainType(Enum):
    """Types of terrain that can be generated"""
    FLAT = "flat"
    NOISY_HEIGHTFIELD = "noisy_heightfield"
    PYRAMID_BOXES = "pyramid_boxes"
    STAIRS = "stairs"
    RANDOM_BOXES = "random_boxes"


class TerrainGenerator:
    """Generates complex terrains for MuJoCo simulation"""
    
    def __init__(self, 
                 grid_rows: int = 3,
                 grid_cols: int = 3,
                 terrain_size: float = 5.0,
                 terrain_spacing: float = 0.0,
                 base_height: float = -1.0):
        """
        Initialize the terrain generator
        
        Args:
            grid_rows: Number of rows in the terrain grid
            grid_cols: Number of columns in the terrain grid
            terrain_size: Size of each terrain patch (meters)
            terrain_spacing: Reserved for future use (currently terrains are continuous)
            base_height: Base height for terrain placement (meters)
        """
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.terrain_size = terrain_size
        self.terrain_spacing = terrain_spacing
        self.base_height = base_height
        
        # Create root MJCF structure
        self.root = ET.Element('mujoco')
        self.root.set('model', 'terrain_grid')
        
        # Add compiler settings
        compiler = ET.SubElement(self.root, 'compiler')
        compiler.set('angle', 'radian')
        
        # Add asset section
        self.asset = ET.SubElement(self.root, 'asset')
        self._add_default_assets()
        
        # Add worldbody section
        self.worldbody = ET.SubElement(self.root, 'worldbody')
        
        # Track terrain index for naming
        self.terrain_index = 0
        self.heightfield_index = 0
        
    def _add_default_assets(self):
        """Add default textures and materials"""
        # Skybox
        skybox = ET.SubElement(self.asset, 'texture')
        skybox.set('type', 'skybox')
        skybox.set('builtin', 'gradient')
        skybox.set('rgb1', '.3 .5 .7')
        skybox.set('rgb2', '0 0 0')
        skybox.set('width', '512')
        skybox.set('height', '512')
        
        # Grid texture
        grid_tex = ET.SubElement(self.asset, 'texture')
        grid_tex.set('name', 'grid')
        grid_tex.set('type', '2d')
        grid_tex.set('builtin', 'checker')
        grid_tex.set('width', '512')
        grid_tex.set('height', '512')
        grid_tex.set('rgb1', '.1 .2 .3')
        grid_tex.set('rgb2', '.2 .3 .4')
        
        # Grid material
        grid_mat = ET.SubElement(self.asset, 'material')
        grid_mat.set('name', 'grid')
        grid_mat.set('texture', 'grid')
        grid_mat.set('texrepeat', '1 1')
        grid_mat.set('texuniform', 'true')
        grid_mat.set('reflectance', '.2')
        
        # Box material
        box_tex = ET.SubElement(self.asset, 'texture')
        box_tex.set('name', 'box_texture')
        box_tex.set('type', '2d')
        box_tex.set('builtin', 'checker')
        box_tex.set('width', '512')
        box_tex.set('height', '512')
        box_tex.set('rgb1', '.8 .8 0')
        box_tex.set('rgb2', '.6 .6 0')
        
        box_mat = ET.SubElement(self.asset, 'material')
        box_mat.set('name', 'box_material')
        box_mat.set('texture', 'box_texture')
        
    def _get_terrain_position(self, row: int, col: int) -> Tuple[float, float]:
        """
        Calculate the position of a terrain patch in the grid
        
        Args:
            row: Row index
            col: Column index
            
        Returns:
            (x, y) position in world coordinates
        """
        # Position terrains continuously (no gaps) - spacing is used for optional margins
        x = col * self.terrain_size - \
            (self.grid_cols - 1) * self.terrain_size / 2
        y = row * self.terrain_size - \
            (self.grid_rows - 1) * self.terrain_size / 2
        return x, y
    
    def add_flat_terrain(self, row: int, col: int, friction: float = 0.6):
        """Add a flat plane terrain"""
        x, y = self._get_terrain_position(row, col)
        
        geom = ET.SubElement(self.worldbody, 'geom')
        geom.set('name', f'flat_terrain_{self.terrain_index}')
        geom.set('type', 'plane')
        geom.set('size', f'{self.terrain_size/2} {self.terrain_size/2} 0.05')
        geom.set('pos', f'{x} {y} {self.base_height}')
        geom.set('material', 'grid')
        geom.set('friction', str(friction))
        geom.set('condim', '3')
        
        self.terrain_index += 1
        
    def add_noisy_heightfield(self, 
                              row: int, 
                              col: int,
                              amplitude: float = 0.1,
                              frequency: float = 5.0,
                              resolution: int = 256,
                              friction: float = 0.6,
                              output_dir: str = '.'):
        """
        Add a noisy heightfield terrain
        
        Args:
            row: Row index
            col: Column index
            amplitude: Maximum height variation (meters)
            frequency: Frequency of noise pattern
            resolution: Resolution of heightfield (pixels)
            friction: Friction coefficient
            output_dir: Directory to save heightfield images
        """
        x, y = self._get_terrain_position(row, col)
        
        # Generate noise heightfield
        x_grid = np.linspace(0, frequency * 2 * np.pi, resolution)
        y_grid = np.linspace(0, frequency * 2 * np.pi, resolution)
        X, Y = np.meshgrid(x_grid, y_grid)
        
        # Combine multiple frequencies for more interesting terrain
        Z = np.sin(X) * np.cos(Y) + \
            0.5 * np.sin(2 * X + 1) * np.cos(2 * Y + 2) + \
            0.25 * np.sin(4 * X + 0.5) * np.cos(4 * Y + 1.5)
        
        # Add random noise
        Z += np.random.randn(*Z.shape) * 0.2
        
        # Normalize to [0, 1] range
        Z = (Z - Z.min()) / (Z.max() - Z.min())
        
        # Save as PNG (MuJoCo uses grayscale images for heightfields)
        img_array = (Z * 255).astype(np.uint8)
        img = Image.fromarray(img_array, mode='L')
        
        os.makedirs(output_dir, exist_ok=True)
        img_filename = f'heightfield_{self.heightfield_index}.png'
        img_path = os.path.join(output_dir, img_filename)
        img.save(img_path)
        
        # Add to assets (use absolute path for MuJoCo)
        hfield = ET.SubElement(self.asset, 'hfield')
        hfield.set('name', f'hfield_{self.heightfield_index}')
        hfield.set('file', os.path.abspath(img_path))
        hfield.set('size', f'{self.terrain_size/2} {self.terrain_size/2} {amplitude} 0.01')
        
        # Add to worldbody
        geom = ET.SubElement(self.worldbody, 'geom')
        geom.set('name', f'heightfield_terrain_{self.terrain_index}')
        geom.set('type', 'hfield')
        geom.set('hfield', f'hfield_{self.heightfield_index}')
        geom.set('pos', f'{x} {y} {self.base_height}')
        geom.set('friction', str(friction))
        geom.set('condim', '3')
        
        self.heightfield_index += 1
        self.terrain_index += 1
        
    def add_pyramid_boxes(self,
                         row: int,
                         col: int,
                         num_levels: int = 5,
                         max_height: float = 0.5,
                         friction: float = 0.6):
        """
        Add pyramid-style terrain made of boxes
        
        Args:
            row: Row index
            col: Column index
            num_levels: Number of pyramid levels
            max_height: Maximum height of pyramid (meters)
            friction: Friction coefficient
        """
        x_base, y_base = self._get_terrain_position(row, col)
        
        # Add base plane
        base_geom = ET.SubElement(self.worldbody, 'geom')
        base_geom.set('name', f'pyramid_base_{self.terrain_index}')
        base_geom.set('type', 'plane')
        base_geom.set('size', f'{self.terrain_size/2} {self.terrain_size/2} 0.01')
        base_geom.set('pos', f'{x_base} {y_base} {self.base_height}')
        base_geom.set('material', 'grid')
        base_geom.set('friction', str(friction))
        base_geom.set('condim', '3')
        
        # Calculate box dimensions
        base_box_size = self.terrain_size / (2 * num_levels + 1)
        height_per_level = max_height / num_levels
        
        box_count = 0
        for level in range(num_levels):
            # Number of boxes per side at this level
            boxes_per_side = num_levels - level
            box_size = base_box_size
            box_height = height_per_level * (level + 1)
            
            # Calculate positions for this level
            start_offset = -(boxes_per_side - 1) * base_box_size
            
            for i in range(boxes_per_side):
                for j in range(boxes_per_side):
                    x = x_base + start_offset + i * 2 * box_size
                    y = y_base + start_offset + j * 2 * box_size
                    z = self.base_height + box_height / 2
                    
                    geom = ET.SubElement(self.worldbody, 'geom')
                    geom.set('name', f'pyramid_{self.terrain_index}_box_{box_count}')
                    geom.set('type', 'box')
                    geom.set('size', f'{box_size} {box_size} {box_height/2}')
                    geom.set('pos', f'{x} {y} {z}')
                    geom.set('material', 'box_material')
                    geom.set('friction', str(friction))
                    geom.set('condim', '3')
                    
                    box_count += 1
        
        self.terrain_index += 1
        
    def add_stairs(self,
                  row: int,
                  col: int,
                  num_steps: int = 8,
                  step_height: float = 0.1,
                  step_depth: float = 0.4,
                  friction: float = 0.6):
        """
        Add stair terrain
        
        Args:
            row: Row index
            col: Column index
            num_steps: Number of steps
            step_height: Height of each step (meters)
            step_depth: Depth of each step (meters)
            friction: Friction coefficient
        """
        x_base, y_base = self._get_terrain_position(row, col)
        
        # Add base plane
        base_geom = ET.SubElement(self.worldbody, 'geom')
        base_geom.set('name', f'stairs_base_{self.terrain_index}')
        base_geom.set('type', 'plane')
        base_geom.set('size', f'{self.terrain_size/2} {self.terrain_size/2} 0.01')
        base_geom.set('pos', f'{x_base} {y_base} {self.base_height}')
        base_geom.set('material', 'grid')
        base_geom.set('friction', str(friction))
        base_geom.set('condim', '3')
        
        step_width = self.terrain_size * 0.8
        start_x = x_base - (num_steps * step_depth) / 2 + step_depth / 2
        
        for i in range(num_steps):
            x = start_x + i * step_depth
            height = (i + 1) * step_height
            z = self.base_height + height / 2
            
            geom = ET.SubElement(self.worldbody, 'geom')
            geom.set('name', f'stairs_{self.terrain_index}_step_{i}')
            geom.set('type', 'box')
            geom.set('size', f'{step_depth/2} {step_width/2} {height/2}')
            geom.set('pos', f'{x} {y_base} {z}')
            geom.set('material', 'box_material')
            geom.set('friction', str(friction))
            geom.set('condim', '3')
        
        self.terrain_index += 1
        
    def add_random_boxes(self,
                        row: int,
                        col: int,
                        num_boxes: int = 20,
                        min_size: float = 0.1,
                        max_size: float = 0.3,
                        max_height: float = 0.3,
                        friction: float = 0.6,
                        seed: Optional[int] = None):
        """
        Add random box obstacles
        
        Args:
            row: Row index
            col: Column index
            num_boxes: Number of random boxes
            min_size: Minimum box size (meters)
            max_size: Maximum box size (meters)
            max_height: Maximum box height (meters)
            friction: Friction coefficient
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)
            
        x_base, y_base = self._get_terrain_position(row, col)
        
        # Add base plane
        base_geom = ET.SubElement(self.worldbody, 'geom')
        base_geom.set('name', f'random_base_{self.terrain_index}')
        base_geom.set('type', 'plane')
        base_geom.set('size', f'{self.terrain_size/2} {self.terrain_size/2} 0.01')
        base_geom.set('pos', f'{x_base} {y_base} {self.base_height}')
        base_geom.set('material', 'grid')
        base_geom.set('friction', str(friction))
        base_geom.set('condim', '3')
        
        # Generate random boxes
        for i in range(num_boxes):
            # Random position within terrain bounds (with margin)
            margin = max_size
            x = x_base + np.random.uniform(-self.terrain_size/2 + margin, 
                                           self.terrain_size/2 - margin)
            y = y_base + np.random.uniform(-self.terrain_size/2 + margin,
                                           self.terrain_size/2 - margin)
            
            # Random size and height
            size_x = np.random.uniform(min_size, max_size)
            size_y = np.random.uniform(min_size, max_size)
            height = np.random.uniform(min_size, max_height)
            z = self.base_height + height / 2
            
            geom = ET.SubElement(self.worldbody, 'geom')
            geom.set('name', f'random_{self.terrain_index}_box_{i}')
            geom.set('type', 'box')
            geom.set('size', f'{size_x/2} {size_y/2} {height/2}')
            geom.set('pos', f'{x} {y} {z}')
            geom.set('material', 'box_material')
            geom.set('friction', str(friction))
            geom.set('condim', '3')
        
        self.terrain_index += 1
    
    def generate_grid(self, terrain_types: List[List[TerrainType]], **kwargs):
        """
        Generate a grid of terrains
        
        Args:
            terrain_types: 2D list of TerrainType specifying the type for each grid cell
            **kwargs: Additional parameters passed to terrain generation functions
                     Common: friction, output_dir
                     Heightfield: amplitude, frequency, resolution
                     Pyramid: num_levels, max_height
                     Stairs: num_steps, step_height, step_depth
                     Random: num_boxes, min_size, max_size, max_height
        """
        if len(terrain_types) != self.grid_rows:
            raise ValueError(f"terrain_types must have {self.grid_rows} rows")
        if any(len(row) != self.grid_cols for row in terrain_types):
            raise ValueError(f"All rows in terrain_types must have {self.grid_cols} columns")
        
        # Extract common parameters
        friction = kwargs.get('friction', 0.6)
        output_dir = kwargs.get('output_dir', '.')
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                terrain_type = terrain_types[row][col]
                
                if terrain_type == TerrainType.FLAT:
                    self.add_flat_terrain(row, col, friction=friction)
                elif terrain_type == TerrainType.NOISY_HEIGHTFIELD:
                    self.add_noisy_heightfield(
                        row, col,
                        amplitude=kwargs.get('amplitude', 0.1),
                        frequency=kwargs.get('frequency', 5.0),
                        resolution=kwargs.get('resolution', 256),
                        friction=friction,
                        output_dir=output_dir
                    )
                elif terrain_type == TerrainType.PYRAMID_BOXES:
                    self.add_pyramid_boxes(
                        row, col,
                        num_levels=kwargs.get('num_levels', 5),
                        max_height=kwargs.get('max_height', 0.5),
                        friction=friction
                    )
                elif terrain_type == TerrainType.STAIRS:
                    self.add_stairs(
                        row, col,
                        num_steps=kwargs.get('num_steps', 8),
                        step_height=kwargs.get('step_height', 0.1),
                        step_depth=kwargs.get('step_depth', 0.4),
                        friction=friction
                    )
                elif terrain_type == TerrainType.RANDOM_BOXES:
                    self.add_random_boxes(
                        row, col,
                        num_boxes=kwargs.get('num_boxes', 20),
                        min_size=kwargs.get('min_size', 0.1),
                        max_size=kwargs.get('max_size', 0.3),
                        max_height=kwargs.get('max_height', 0.3),
                        friction=friction,
                        seed=row * self.grid_cols + col
                    )
    
    def save(self, filename: str, pretty: bool = True):
        """
        Save the terrain MJCF file
        
        Args:
            filename: Output filename
            pretty: Whether to pretty-print the XML
        """
        if pretty:
            xml_str = minidom.parseString(ET.tostring(self.root)).toprettyxml(indent="  ")
            # Remove extra blank lines
            xml_str = '\n'.join([line for line in xml_str.split('\n') if line.strip()])
        else:
            xml_str = ET.tostring(self.root, encoding='unicode')
        
        with open(filename, 'w') as f:
            f.write(xml_str)
        
        print(f"Terrain MJCF saved to: {filename}")


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Generate MuJoCo terrain grids')
    parser.add_argument('--rows', type=int, default=3, help='Number of rows in terrain grid')
    parser.add_argument('--cols', type=int, default=3, help='Number of columns in terrain grid')
    parser.add_argument('--size', type=float, default=5.0, help='Size of each terrain patch (m)')
    parser.add_argument('--spacing', type=float, default=0.5, help='Spacing between patches (m)')
    parser.add_argument('--output', type=str, default='terrain_grid.xml', help='Output filename')
    parser.add_argument('--output-dir', type=str, default='./terrain_assets', 
                       help='Directory for heightfield images')
    
    args = parser.parse_args()
    
    # Create generator
    generator = TerrainGenerator(
        grid_rows=args.rows,
        grid_cols=args.cols,
        terrain_size=args.size,
        terrain_spacing=args.spacing
    )
    
    # Define a sample terrain layout based on grid dimensions
    # Cycle through all available terrain types
    terrain_types = [
        TerrainType.FLAT,
        TerrainType.NOISY_HEIGHTFIELD,
        TerrainType.PYRAMID_BOXES,
        TerrainType.STAIRS,
        TerrainType.RANDOM_BOXES
    ]
    
    terrain_layout = []
    type_idx = 0
    for row in range(args.rows):
        row_layout = []
        for col in range(args.cols):
            row_layout.append(terrain_types[type_idx % len(terrain_types)])
            type_idx += 1
        terrain_layout.append(row_layout)
    
    # Generate terrains
    generator.generate_grid(terrain_layout, output_dir=args.output_dir)
    
    # Save MJCF file
    generator.save(args.output)


if __name__ == '__main__':
    main()
