"""Main ingestion script for APEC job offers."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import time, random

from .client import ApecClient
from .storage import Database
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
    
    for i, config in enumerate(SEARCH_CONFIGS.keys()):
        print(f"Running ingestion for config: {config}")
        extracted = run_ingestion(config)
        results[config] = {
            "value": extracted["value"],
            "retrieved_at": extracted["retrieved_at"],
        }
        if i < len(SEARCH_CONFIGS) - 1:
            # sleep a random time between 0.5 and 2 seconds to avoid rate limiting
            sleep_time = random.uniform(0.5, 2.0)
            time.sleep(sleep_time)
    
    # Save all results to database
    db = Database()
    db.save_metrics(results)
    
    print(f"\n✓ Saved all metrics to database")
    print(f"✓ Total configs processed: {len(results)}")
