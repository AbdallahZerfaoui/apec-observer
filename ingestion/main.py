"""Main ingestion script for APEC job offers."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .client import ApecClient
from .storage import write_json


def build_search_payload() -> dict[str, Any]:
    """Build minimal search payload for job offers.

    Returns:
        Dictionary with search parameters
    """
    return {
        "lieux": [],
        "fonctions": [],
        "statutPoste": ["143688", "143689"], #only cadres (public and private)
        "typesContrat": [],
        "typesConvention": ["143684", "143685", "143686", "143687", "143706"], #706=partenaires
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


def run_ingestion() -> None:
    """Execute the ingestion pipeline.

    1. Call APEC search endpoint
    2. Extract total number of offers
    3. Write result to disk
    """
    client = ApecClient()
    payload = build_search_payload()

    response = client.post("/rechercheOffre", data=payload)
    extracted = extract_total_offers(response)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"data/raw/apec_main_value_{timestamp}.json")

    write_json(extracted, output_path)
    print(f"✓ Extracted {extracted['value']} job offers")
    print(f"✓ Saved to {output_path}")


if __name__ == "__main__":
    run_ingestion()
