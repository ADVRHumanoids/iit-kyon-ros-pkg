from xbot2_py_mujoco.utils.terrain_generator import *

stairs = dict(
    step_height_range=(0.10, 0.20),
    step_width=0.3,
    platform_width=3.0,
    border_width=1.0,
    tread_thickness=0.06,
    tread_overlap=0.00,
    proportion=0.0,
)

ROUGH_TERRAINS_CFG = TerrainGeneratorCfg(
    seed=0,  # Deterministic terrain generation.
    size=(12.0, 12.0),  # Width and depth of each terrain tile in meters.
    border_width=20.0,  # Width of the outer collision border in meters.
    border_height=1.0,  # Height of the outer collision border in meters.
    num_rows=4,  # Number of terrain rows.
    num_cols=8,  # Number of terrain columns.
    horizontal_scale=0.1,  # Heightfield sample spacing in meters.
    vertical_scale=0.005,  # Heightfield quantization step in meters.
    slope_threshold=0.75,  # Retained for compatibility; ignored by MuJoCo heightfields.
    use_cache=False,  # Whether to cache generated terrain patches.
    cache_dir="/tmp/xbot2_mujoco/terrains",  # Directory used for terrain caches.
    curriculum=True,  # Arrange terrain types by columns and difficulty by rows.
    difficulty_range=(0.0, 1.0),  # Difficulty interval used for terrain sampling.
    spawn_height=1.0,  # Height added above each terrain origin for robot spawning.
    sub_terrains={
        "open_stairs": MeshOpenPyramidStairsTerrainCfg(**stairs),
        "open_stairs_inv": MeshOpenInvertedPyramidStairsTerrainCfg(**stairs),
        "pyramid_stairs": MeshPyramidStairsTerrainCfg(
            proportion=0.2,  # Share of randomly selected terrain types.
            step_height_range=(0.15, 0.30),  # Minimum and maximum step height.
            step_width=2,  # Width of each stair step in meters.
            platform_width=3.0,  # Flat center platform width in meters.
            border_width=1.0,  # Inset from the tile edge in meters.
        ),
        "pyramid_stairs_inv": MeshInvertedPyramidStairsTerrainCfg(
            proportion=0.2,  # Share of randomly selected terrain types.
            step_height_range=(0.15, 0.30),  # Minimum and maximum step height.
            step_width=2,  # Width of each stair step in meters.
            platform_width=3.0,  # Flat center platform width in meters.
            border_width=1.0,  # Inset from the tile edge in meters.
        ),

        "boxes": MeshRandomGridTerrainCfg(
            proportion=0.2,  # Share of randomly selected terrain types.
            grid_width=0.45,  # Width of each random box cell in meters.
            grid_height_range=(0.05, 0.1),  # Minimum and maximum box height.
            platform_width=2.0,  # Flat center platform width in meters.
        ),
        "random_rough": HfRandomUniformTerrainCfg(
            proportion=0.2,  # Share of randomly selected terrain types.
            noise_range=(0.02, 0.2),  # Minimum and maximum noise height.
            noise_step=0.02,  # Quantization step for sampled noise values.
            border_width=0.25,  # Flat inset border width in meters.
        ),
        "hf_pyramid_slope": HfPyramidSlopedTerrainCfg(
            proportion=0.1,  # Share of randomly selected terrain types.
            slope_range=(0, 0.7),  # Minimum and maximum pyramid slope.
            platform_width=2.0,  # Flat center platform width in meters.
            border_width=0.25,  # Flat inset border width in meters.
        ),
        "hf_pyramid_slope_inv": HfInvertedPyramidSlopedTerrainCfg(
            proportion=0.1,  # Share of randomly selected terrain types.
            slope_range=(0, 0.7),  # Minimum and maximum inverted pyramid slope.
            platform_width=2.0,  # Flat center platform width in meters.
            border_width=0.25,  # Flat inset border width in meters.
        ),
    },
)


def main(argv: list[str] | None = None) -> int:
    """Generate the default rough terrain from the command line."""
    parser = argparse.ArgumentParser(
        description="Save ROUGH_TERRAINS_CFG as a MuJoCo world."
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=Path(__file__).parent.parent / "isaaclab_rough_terrain",
        help="Directory for the MJCF and its heightfield assets.",
    )
    parser.add_argument(
        "--filename",
        default="rough_terrain.xml",
        help="MJCF filename inside OUTPUT_DIR (default: %(default)s).",
    )
    args = parser.parse_args(argv)

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = TerrainGenerator(ROUGH_TERRAINS_CFG).save(
        output_dir / args.filename
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
