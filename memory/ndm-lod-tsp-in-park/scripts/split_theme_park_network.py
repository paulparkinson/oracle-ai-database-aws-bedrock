#!/usr/bin/env python3
"""Split a mixed theme-park GeoJSON FeatureCollection into nodes and links.

The input is expected to contain a ``properties.feature_type`` value of
``node`` or ``link``.  Geometry type is also checked so that an accidental
mixed or malformed feature is reported instead of silently being loaded into
the wrong Oracle table.

The ID mapping includes both top-level feature IDs and IDs referenced by
``from_node``, ``to_node``, and ``parent_link_id``.  This is important because
some parent links in the input are logical parent IDs and do not appear as
separate GeoJSON features.

This script only reads and writes files.  It does not connect to a database.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_DIR / "data" / "theme_park_network.geojson"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "data" / "generated"
DEFAULT_NODE_OUTPUT = "theme_park_network_nodes.geojson"
DEFAULT_LINK_OUTPUT = "theme_park_network_links.geojson"
DEFAULT_MAPPING_OUTPUT = "id_mapping.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a mixed node/link GeoJSON file into two GeoJSON files."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Input GeoJSON file (default: data/theme_park_network.geojson)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for output files (default: data/generated)",
    )
    parser.add_argument(
        "--node-output",
        type=str,
        default=DEFAULT_NODE_OUTPUT,
        help=f"Node output filename (default: {DEFAULT_NODE_OUTPUT})",
    )
    parser.add_argument(
        "--link-output",
        type=str,
        default=DEFAULT_LINK_OUTPUT,
        help=f"Link output filename (default: {DEFAULT_LINK_OUTPUT})",
    )
    parser.add_argument(
        "--mapping-output",
        type=str,
        default=DEFAULT_MAPPING_OUTPUT,
        help=f"ID mapping filename (default: {DEFAULT_MAPPING_OUTPUT})",
    )
    return parser.parse_args()


def load_feature_collection(input_path: Path) -> dict[str, Any]:
    try:
        with input_path.open("r", encoding="utf-8") as source:
            document = json.load(source)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read GeoJSON file {input_path}: {exc}") from exc

    if document.get("type") != "FeatureCollection":
        raise RuntimeError(
            f"Expected a GeoJSON FeatureCollection, found {document.get('type')!r}"
        )
    if not isinstance(document.get("features"), list):
        raise RuntimeError("GeoJSON FeatureCollection has no valid features array")

    return document


def split_features(
    features: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    nodes: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    warnings: list[str] = []

    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise RuntimeError(f"Feature at index {index} is not a JSON object")

        properties = feature.get("properties") or {}
        feature_type = str(properties.get("feature_type", "")).lower()
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type")
        feature_id = feature.get("id", f"index-{index}")

        if feature_type == "node":
            if geometry_type != "Point":
                warnings.append(
                    f"{feature_id}: feature_type=node but geometry={geometry_type!r}"
                )
            nodes.append(feature)
        elif feature_type == "link":
            if geometry_type not in {"LineString", "MultiLineString"}:
                warnings.append(
                    f"{feature_id}: feature_type=link but geometry={geometry_type!r}"
                )
            links.append(feature)
        else:
            raise RuntimeError(
                f"Feature {feature_id!r} at index {index} has unsupported "
                f"properties.feature_type={feature_type!r}; expected 'node' or 'link'"
            )

    return nodes, links, warnings


def validate_link_references(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    id_mapping: dict[str, int],
) -> list[str]:
    node_ids = {
        str(feature.get("id"))
        for feature in nodes
        if feature.get("id") is not None
    }
    missing: list[str] = []

    for feature in links:
        properties = feature.get("properties") or {}
        feature_id = feature.get("id", "<missing-id>")
        for key in ("from_node", "to_node"):
            referenced_id = properties.get(key)
            if referenced_id is not None and str(referenced_id) not in node_ids:
                missing.append(
                    f"{feature_id}: {key}={referenced_id!r} does not match a node id"
                )

        parent_link_id = properties.get("parent_link_id")
        if parent_link_id is not None and str(parent_link_id) not in id_mapping:
            missing.append(
                f"{feature_id}: parent_link_id={parent_link_id!r} "
                "does not have an ID mapping"
            )

    return missing


def build_id_mapping(features: list[dict[str, Any]]) -> dict[str, int]:
    """Assign one unique long integer to feature and reference IDs."""
    mapping: dict[str, int] = {}

    referenced_ids: list[str] = []
    top_level_ids: set[str] = set()

    for feature in features:
        if feature.get("id") is None:
            raise RuntimeError("A feature has no top-level id")

        original_id = str(feature["id"])
        if original_id in top_level_ids:
            raise RuntimeError(f"Duplicate top-level feature id: {original_id!r}")
        top_level_ids.add(original_id)
        referenced_ids.append(original_id)

        properties = feature.get("properties") or {}
        if str(properties.get("feature_type", "")).lower() == "link":
            for key in ("from_node", "to_node", "parent_link_id"):
                referenced_id = properties.get(key)
                if referenced_id is not None and str(referenced_id) != "":
                    referenced_ids.append(str(referenced_id))

    for long_id, original_id in enumerate(dict.fromkeys(referenced_ids), start=1):
        mapping[original_id] = long_id

    return mapping


def add_numeric_id_properties(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
    id_mapping: dict[str, int],
) -> None:
    """Add NDM-friendly numeric IDs while preserving original string fields."""
    for feature in nodes:
        properties = feature.setdefault("properties", {})
        original_id = str(feature["id"])
        properties["node_id"] = id_mapping[original_id]

    for feature in links:
        properties = feature.setdefault("properties", {})
        original_id = str(feature["id"])
        properties["link_id"] = id_mapping[original_id]

        for source_key, numeric_key in (
            ("from_node", "start_node_id"),
            ("to_node", "end_node_id"),
            ("parent_link_id", "parent_link_id_number"),
        ):
            referenced_id = properties.get(source_key)
            properties[numeric_key] = (
                id_mapping.get(str(referenced_id))
                if referenced_id is not None
                else None
            )


def write_id_mapping(path: Path, id_mapping: dict[str, int]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["long_id", "original_id"])
        writer.writeheader()
        for original_id, long_id in id_mapping.items():
            writer.writerow({"long_id": long_id, "original_id": original_id})


def write_feature_collection(
    output_path: Path,
    source_document: dict[str, Any],
    features: list[dict[str, Any]],
    output_name: str,
) -> None:
    document = {
        key: value for key, value in source_document.items() if key != "features"
    }
    document.update(
        {
            "type": "FeatureCollection",
            "name": output_name,
            "features": features,
        }
    )

    with output_path.open("w", encoding="utf-8") as output:
        json.dump(document, output, ensure_ascii=False, indent=2)
        output.write("\n")


def main() -> int:
    args = parse_args()

    if not args.input.is_file():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        source_document = load_feature_collection(args.input)
        nodes, links, warnings = split_features(source_document["features"])
        id_mapping = build_id_mapping(source_document["features"])
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    reference_warnings = validate_link_references(nodes, links, id_mapping)
    warnings.extend(reference_warnings)
    add_numeric_id_properties(nodes, links, id_mapping)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    node_output = args.output_dir / args.node_output
    link_output = args.output_dir / args.link_output
    mapping_output = args.output_dir / args.mapping_output

    write_feature_collection(
        node_output,
        source_document,
        nodes,
        "theme_park_network_nodes",
    )
    write_feature_collection(
        link_output,
        source_document,
        links,
        "theme_park_network_links",
    )
    write_id_mapping(mapping_output, id_mapping)

    print(f"Input: {args.input}")
    print(f"Input features: {len(source_document['features'])}")
    print(f"Node features: {len(nodes)}")
    print(f"Link features: {len(links)}")
    print(f"ID mappings: {len(id_mapping)}")
    print(f"Node output: {node_output}")
    print(f"Link output: {link_output}")
    print(f"Mapping output: {mapping_output}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("Validation: no geometry or node-reference warnings")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
