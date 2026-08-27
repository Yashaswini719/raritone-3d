from pathlib import Path
import shutil
import json
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "input"
GENERATED_DIR = BASE_DIR / "generated"
METADATA_DIR = BASE_DIR / "metadata"

ASSET_ID = "RAR-3D-001"
PRODUCT_ID = "PRODUCT-001"

SOURCE_IMAGE = INPUT_DIR / "tshirt-001.png"


def register_generated_asset(glb_file):
    """
    Registers a generated 3D candidate asset in the Raritone pipeline.

    The actual image-to-3D generation provider can be replaced later.
    """

    glb_path = Path(glb_file)

    if not SOURCE_IMAGE.exists():
        raise FileNotFoundError(
            f"Source image not found: {SOURCE_IMAGE}"
        )

    if not glb_path.exists():
        raise FileNotFoundError(
            f"Generated GLB not found: {glb_path}"
        )

    GENERATED_DIR.mkdir(exist_ok=True)
    METADATA_DIR.mkdir(exist_ok=True)

    destination = GENERATED_DIR / f"{ASSET_ID}.glb"

    shutil.copy2(glb_path, destination)

    metadata = {
        "asset_id": ASSET_ID,
        "product_id": PRODUCT_ID,
        "source_image": str(SOURCE_IMAGE.relative_to(BASE_DIR)),
        "model": "TO_BE_DOCUMENTED",
        "model_version": "TO_BE_DOCUMENTED",
        "generated_at": datetime.now().isoformat(),
        "license": "TO_BE_DOCUMENTED",
        "status": "pending_review",
        "reviewed_by": None,
        "processing_steps": [
            "image_to_3d_generation",
            "candidate_registered"
        ]
    }

    metadata_file = METADATA_DIR / f"{ASSET_ID}.json"

    with open(metadata_file, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    print("Candidate asset registered successfully.")
    print(f"Asset: {destination}")
    print(f"Metadata: {metadata_file}")
    print("Status: pending_review")
    print("Candidate remains private until human approval.")


if __name__ == "__main__":
    print("Raritone 3D Asset Generation Pipeline")
    print("Source image:", SOURCE_IMAGE)