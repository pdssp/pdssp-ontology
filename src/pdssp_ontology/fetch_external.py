"""Refresh the committed snapshots of the external vocabularies the
mappings point at (vocab/external/*.desise.json).

They are PADC (Observatoire de Paris) vocabularies for EPNcore, published
in IVOA "Vocabularies in the VO 2" form, CC-0. Pinned by release date so a
refresh is a reviewed change, never a silent one.

Usage::

    uv run python -m pdssp_ontology.fetch_external
"""

from __future__ import annotations

import json

import httpx

from .vocab import EXTERNAL_DIR

BASE = "https://voparis-ns.obspm.fr/rdf/epn/2.0"
PINNED = {  # name -> (release date, file stem on the PADC server)
    "target-class": ("2024-11-04", "epn_target_class"),
    "product-type": ("2024-03-28", "epn_product_type"),
    "spatial-frame-type": ("2024-05-07", "epn_spatial_frame_type"),
}


def main() -> None:
    for name, (date, stem) in PINNED.items():
        url = f"{BASE}/{name}/{date}/{stem}.desise"
        data = httpx.get(url, follow_redirects=True, timeout=30).raise_for_status().json()
        data["_snapshot"] = {"version": date, "source": url}
        path = EXTERNAL_DIR / f"epn-{name}.desise.json"
        path.write_text(json.dumps(data, indent=1), encoding="utf-8")
        print(f"wrote {path} ({len(data['terms'])} terms)")


if __name__ == "__main__":
    main()
