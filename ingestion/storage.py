"""Storage utilities for writing data to disk."""

import json
from pathlib import Path
from typing import Any


def write_json(data: dict[str, Any], filepath: Path) -> None:
    """Write data as JSON to disk.

    Args:
        data: Dictionary to write
        filepath: Path object for target file

    Creates parent directories if they don't exist.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# def update_json(data: dict[str, Any], filepath: Path) -> None:
#     """Update existing JSON file with new data.

#     Args:
#         data: Dictionary to update
#         filepath: Path object for target file

#     Creates parent directories if they don't exist.
#     """
#     if filepath.exists():
#         with open(filepath, "r", encoding="utf-8") as f:
#             existing_data = json.load(f)
#         existing_data.update(data)
#         data = existing_data

#     filepath.parent.mkdir(parents=True, exist_ok=True)
#     with open(filepath, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)
