"""Main ingestion script for APEC job offers."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .client import ApecClient
from .storage import write_json
from .config import SEARCH_CONFIGS


def build_search_payload(config_name: str) -> dict[str, Any]:
    """Build minimal search payload for job offers.

    Returns:
        Dictionary with search parameters
    """
    payload = {
        "lieux": [],
        "fonctions": [],
        "statutPoste": [], 
        "typesContrat": [],
        "typesConvention": [],
        "niveauxExperience": [],
        "idsEtablissement": [],
        "secteursActivite": [],
        "typesTeletravail": [],
        "idNomZonesDeplacement": [],
        "positionNumbersExcluded": [],
        "typeClient": "CADRE",
        "sorts": [{"type": "DATE", "direction": "DESCENDING"}],
        "pagination": {"range": 1, "startIndex": 0},
        "activeFiltre": True,
        "pointGeolocDeReference": {"distance": 0},
    }

    payload.update(SEARCH_CONFIGS[config_name])
    return payload


def extract_total_offers(response: dict[str, Any]) -> dict[str, Any]:
    """Extract total number of job offers from API response.

    Args:
        response: JSON response from APEC API

    Returns:
        Dictionary with extracted value and metadata
    """
    total = response.get("totalCount", 0)
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "value_name": "total_job_offers",
        "value": total,
        "retrieved_at": timestamp,
    }


def run_ingestion(config_name: str) -> dict[str, Any]:
    """Execute the ingestion pipeline for a single config.

    Args:
        config_name: Name of the search configuration to use

    Returns:
        Dictionary with extracted data

    Steps:
        1. Call APEC search endpoint
        2. Extract total number of offers
    """
    client = ApecClient()
    payload = build_search_payload(config_name)

    response = client.post("/rechercheOffre", data=payload)
    extracted = extract_total_offers(response)
    
    print(f"✓ [{config_name}] Extracted {extracted['value']} job offers")
    
    return extracted


if __name__ == "__main__":
    results = {}
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for config in SEARCH_CONFIGS.keys():
        print(f"Running ingestion for config: {config}")
        extracted = run_ingestion(config)
        results[config] = {
            "value": extracted["value"],
            "retrieved_at": extracted["retrieved_at"],
        }
    
    # Write all results to single JSON file
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"data/raw/apec_all_metrics_{timestamp_str}.json")
    
    output_data = {
        "retrieved_at": timestamp,
        "metrics": results,
    }
    
    write_json(output_data, output_path)
    print(f"\n✓ Saved all metrics to {output_path}")
