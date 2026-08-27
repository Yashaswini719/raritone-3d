from pathlib import Path
import json
import sys

import trimesh
from PIL import Image


SUPPORTED_FORMATS = {".glb", ".gltf", ".obj", ".ply"}

# Reasonable prototype limits
MAX_FILE_SIZE_MB = 100
MAX_POLYGON_COUNT = 500_000


def get_file_size_mb(file_path: Path) -> float:
    return round(file_path.stat().st_size / (1024 * 1024), 2)


def count_scene_geometry(scene):
    """
    Count vertices and faces/polygons across all meshes.
    """
    vertices = 0
    faces = 0
    mesh_count = 0

    for geometry in scene.geometry.values():

        if isinstance(geometry, trimesh.Trimesh):
            mesh_count += 1
            vertices += len(geometry.vertices)
            faces += len(geometry.faces)

    return mesh_count, vertices, faces


def check_materials_and_textures(scene):
    """
    Check whether the asset contains materials and textures.
    """
    has_materials = False
    has_textures = False
    texture_resolution = []

    for geometry in scene.geometry.values():

        if not isinstance(geometry, trimesh.Trimesh):
            continue

        visual = geometry.visual

        # Material check
        if visual is not None and visual.material is not None:
            has_materials = True

        # Texture check
        if hasattr(visual, "material") and visual.material is not None:

            material = visual.material

            # Trimesh may store image texture here
            if hasattr(material, "image") and material.image is not None:
                has_textures = True

                image = material.image

                if isinstance(image, Image.Image):
                    texture_resolution.append(
                        {
                            "width": image.width,
                            "height": image.height
                        }
                    )

    return has_materials, has_textures, texture_resolution


def validate_asset(asset_path):
    asset_path = Path(asset_path)

    report = {
        "file": str(asset_path),
        "valid": False,
        "format": None,
        "file_exists": False,
        "mesh": False,
        "mesh_empty": True,
        "texture": False,
        "materials": False,
        "polygon_count": 0,
        "vertex_count": 0,
        "mesh_count": 0,
        "file_size_mb": 0,
        "texture_resolution": [],
        "errors": [],
        "warnings": []
    }

    # 1. File exists
    if not asset_path.exists():
        report["errors"].append("File does not exist.")
        return report

    report["file_exists"] = True

    # 2. Check format
    extension = asset_path.suffix.lower()
    report["format"] = extension.replace(".", "")

    if extension not in SUPPORTED_FORMATS:
        report["errors"].append(
            f"Unsupported format: {extension}"
        )
        return report

    # 3. File size
    report["file_size_mb"] = get_file_size_mb(asset_path)

    if report["file_size_mb"] > MAX_FILE_SIZE_MB:
        report["warnings"].append(
            f"Large asset: {report['file_size_mb']} MB"
        )

    # 4. Load 3D asset
    try:
        scene = trimesh.load(
            asset_path,
            force="scene",
            process=False
        )

    except Exception as error:
        report["errors"].append(
            f"Failed to load 3D asset: {error}"
        )
        return report

    # 5. Count mesh geometry
    mesh_count, vertices, faces = count_scene_geometry(scene)

    report["mesh_count"] = mesh_count
    report["vertex_count"] = vertices
    report["polygon_count"] = faces

    if mesh_count == 0:
        report["errors"].append("No mesh found.")

    else:
        report["mesh"] = True

    # 6. Check empty mesh
    if vertices > 0 and faces > 0:
        report["mesh_empty"] = False
    else:
        report["errors"].append("Mesh is empty.")

    # 7. Polygon count
    if faces > MAX_POLYGON_COUNT:
        report["warnings"].append(
            f"High polygon count: {faces}"
        )

    if faces == 0:
        report["errors"].append("Polygon count is zero.")

    # 8. Check materials and textures
    materials, textures, texture_resolution = (
        check_materials_and_textures(scene)
    )

    report["materials"] = materials
    report["texture"] = textures
    report["texture_resolution"] = texture_resolution

    if not materials:
        report["warnings"].append("No material detected.")

    if not textures:
        report["warnings"].append("No texture detected.")

    # Final validation
    critical_checks = [
        report["file_exists"],
        report["mesh"],
        not report["mesh_empty"],
        report["polygon_count"] > 0
    ]

    report["valid"] = all(critical_checks)

    return report


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "python validation/asset_validator.py "
            "path/to/asset.glb"
        )
        return

    asset_path = sys.argv[1]

    report = validate_asset(asset_path)

    print("\n========== RARITONE 3D ASSET VALIDATION ==========\n")

    print(json.dumps(report, indent=4))

    print("\n==================================================\n")


if __name__ == "__main__":
    main()