"""Convert a STAC Item (PDSSP profile) into one EPN-TAP 2.0 row.

The converter knows nothing about specific fields: it reads
- where each STAC field lives (pdssp:jsonPath, vocab/stac/),
- which EPN-TAP column it maps to and how (mappings/stac-epn-tap/fields.sssom.tsv),
- the transforms by name (transforms.py).
Changing the mapping is a change to data files, not to this code.

Usage::

    uv run python -m pdssp_ontology.convert item.json --service-title "PDSSP HiRISE"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field

from rdflib import URIRef

from . import transforms, vocab

USABLE = {"skos:exactMatch", "skos:closeMatch", "skos:broadMatch"}
_ASSET = re.compile(r"assets\[role=(\w+)\]")


def resolve(item: dict, path: str):
    """Read a pdssp:jsonPath ('a.b | c.d', 'assets[role=data].href')."""
    for alternative in (p.strip() for p in path.split("|")):
        node = item
        for segment in alternative.split("."):
            match = _ASSET.fullmatch(segment)
            if match:
                role = match.group(1)
                assets = node.get("assets", {}) if isinstance(node, dict) else {}
                node = next((a for k, a in assets.items() if role in a.get("roles", []) or k == role), None)
            elif isinstance(node, dict):
                node = node.get(segment)
            else:
                node = None
            if node is None:
                break
        if node is not None:
            return node
    return None


@dataclass
class Result:
    row: dict
    lost_fields: list[str] = field(default_factory=list)      # STAC fields with no EPN column
    empty_mandatory: list[str] = field(default_factory=list)  # EPN mandatory columns left null
    errors: list[str] = field(default_factory=list)


def convert(item: dict, constants: dict | None = None) -> Result:
    ms = vocab.mapping_set("fields")
    fields_graph, columns_graph = vocab.stac_fields(), vocab.epn_columns()
    row: dict = dict(constants or {})
    result = Result(row)
    for mapping in ms.rows:
        subject = URIRef(ms.expand(mapping["subject_id"]))
        path = fields_graph.value(subject, vocab.PDSSP.jsonPath)
        value = resolve(item, str(path)) if path else None
        if mapping["object_id"] == vocab.NO_TERM_FOUND:
            if value is not None:
                result.lost_fields.append(mapping["subject_label"])
            continue
        if mapping["predicate_id"] not in USABLE:
            continue
        column = mapping["object_label"] or mapping["object_id"].split(":", 1)[1]
        options = ms.other(mapping)
        if value is None:
            if "default" in options:
                row.setdefault(column, options["default"])
            continue
        try:
            row[column] = transforms.apply(options.get("transform", "identity"), value)
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            result.errors.append(f"{column}: {exc}")
    for column in columns_graph.subjects(vocab.PDSSP.epnMandatory, None):
        if columns_graph.value(column, vocab.PDSSP.epnMandatory).toPython() is True:
            name = vocab.label(columns_graph, column)
            if row.get(name) is None:
                row.setdefault(name, None)
                result.empty_mandatory.append(name)
    result.empty_mandatory.sort()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("item", type=argparse.FileType("r"))
    parser.add_argument("--service-title", default="PDSSP")
    args = parser.parse_args()
    result = convert(json.load(args.item), {"service_title": args.service_title})
    json.dump({"row": result.row, "lost_fields": result.lost_fields,
               "empty_mandatory": result.empty_mandatory, "errors": result.errors},
              sys.stdout, indent=2, default=str)
    print()
    sys.exit(1 if result.errors else 0)


if __name__ == "__main__":
    main()
