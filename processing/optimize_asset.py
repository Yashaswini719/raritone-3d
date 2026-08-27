from pathlib import Path
import json
import sys

import trimesh


TARGET_MAX_FACES = 20_000


def get_file_size_mb(file_path: Path) -> float:
    return round(file_path.stat().st_size / (1024 * 1024), 2)


def get_scene_stats(scene):
    mesh_count = 0
    vertex_count = 0
    face_count = 0

    for geometry in scene.geometry.values():
        if isinstance(geometry, trimesh.Trimesh):
            mesh_count += 1
            vertex_count += len(geometry.vertices)
            face_count += len(geometry.faces)

    return {
        "mesh_count": mesh_count,
        "vertex_count": vertex_count,
        "polygon_count": face_count
    }


def normalize_mesh(mesh):
    """
    Center the mesh and normalize its scale.
    """
    if mesh.is_empty:
        return mesh

    # Move object center to origin
    mesh.apply_translation(-mesh.bounding_box.centroid)

    # Normalize the largest dimension
    extents = mesh.bounding_box.extents
    max_dimension = max(extents)

    if max_dimension > 0:
        scale_factor = 1.0 / max_dimension
        mesh.apply_scale(scale_factor)

    return mesh


def optimize_mesh(mesh, target_faces=TARGET_MAX_FACES):
    """
    Clean and simplify one mesh.
    """

    # Remove unnecessary geometry
    mesh.remove_duplicate_faces()
    mesh.remove_degenerate_faces()
    mesh.remove_unreferenced_vertices()

    # Merge nearby duplicate vertices
    mesh.merge_vertices()

    original_faces = len(mesh.faces)

    # Reduce polygon count only when necessary
    if original_faces > target_faces:
        try:
            mesh = mesh.simplify_quadric_decimation(
                face_count=target_faces
            )
        except Exception as error:
            print(
                f"Warning: Polygon reduction failed: {error}"
            )

    # Normalize position and scale
    mesh = normalize_mesh(mesh)

    return mesh


def optimize_asset(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input asset not found: {input_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    before_size = get_file_size_mb(input_path)

    print("\nLoading asset...")
    scene = trimesh.load(
        input_path,
        force="scene",
        process=False
    )

    before_stats = get_scene_stats(scene)

    print("Original statistics:")
    print(json.dumps(before_stats, indent=4))
    print(f"File size: {before_size} MB")

    optimized_scene = trimesh.Scene()

    print("\nOptimizing meshes...")

    for name, geometry in scene.geometry.items():

        if isinstance(geometry, trimesh.Trimesh):

            print(f"Processing mesh: {name}")

            optimized_mesh = optimize_mesh(geometry.copy())

            optimized_scene.add_geometry(
                optimized_mesh,
                node_name=name
            )

        else:
            print(f"Skipping unsupported geometry: {name}")

    print("\nExporting optimized asset...")

    optimized_scene.export(output_path)

    after_size = get_file_size_mb(output_path)
    after_stats = get_scene_stats(optimized_scene)

    reduction = 0

    if before_stats["polygon_count"] > 0:
        reduction = round(
            (
                1
                - (
                    after_stats["polygon_count"]
                    / before_stats["polygon_count"]
                )
            )
            * 100,
            2
        )

    report = {
        "input": str(input_path),
        "output": str(output_path),
        "before": {
            **before_stats,
            "file_size_mb": before_size
        },
        "after": {
            **after_stats,
            "file_size_mb": after_size
        },
        "polygon_reduction_percent": reduction
    }

    print("\n========== RARITONE ASSET OPTIMIZATION ==========\n")

    print(json.dumps(report, indent=4))

    print("\nOptimization completed successfully.")
    print(f"Optimized asset: {output_path}")

    return report


def main():

    if len(sys.argv) < 3:
        print("\nUsage:")
        print(
            "python processing/optimize_asset.py "
            "input_asset.glb output_asset.glb"
        )
        return

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        optimize_asset(
            input_path,
            output_path
        )

    except Exception as error:
        print(f"\nOptimization failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()