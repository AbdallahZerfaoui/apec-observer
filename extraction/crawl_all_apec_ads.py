#!/usr/bin/env python3
"""
Full APEC Job Ads Crawler with SQLAlchemy Persistence

Downloads all available APEC job advertisements (~85k) via pagination,
stores them in SQLite with deduplication, and tracks crawl runs.

Features:
- SQLAlchemy ORM with SQLite persistence
- Automatic resume capability (upserts on conflict)
- Exponential backoff with jitter for rate limiting
- Request delay for politeness
- Comprehensive error handling
- Progress tracking and run statistics
- Optional HTTP proxy support

Usage:
    python crawl_all_apec_ads.py

Environment Variables (loaded from .env file):
    HTTP_PROXY / HTTPS_PROXY: Optional proxy URL
    PROXY_USERNAME: Proxy authentication username
    PROXY_PASSWORD: Proxy authentication password
    PROXY_HOST: Proxy host (default: p.webshare.io:80)
"""

import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

import requests
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Configuration
BASE_URL = "https://www.apec.fr/cms/webservices"
ENDPOINT_PATH = "/rechercheOffre"

# Pagination Configuration
PAGE_SIZE = 100  # Results per page (max supported by APEC)
MAX_PAGES = None  # Optional safety cap (None = unlimited)

# Rate Limiting & Politeness
REQUEST_DELAY_SECONDS = 0.8  # Delay between requests
MAX_RETRIES = 5  # Max retry attempts for transient errors

# Database Configuration
DB_PATH = "data/apec_observer.sqlite"

# Request Configuration
REQUEST_TIMEOUT = 100  # seconds
SECTEUR_ALL = ["101753"]  # None = all sectors, or specific ID like "101753" for IT
LIEU_ALL = "711"  # 799 = France (all locations), IDF = 711
CADRES = ["143688", "143689"]

# Request template based on APEC API
REQUEST_TEMPLATE = {
    "lieux": [LIEU_ALL],
    "fonctions": [],
    "statutPoste": CADRES if CADRES else [],
    "typesContrat": [],
    "typesConvention": [],
    "niveauxExperience": [],
    "idsEtablissement": [],
    "secteursActivite": [SECTEUR_ALL] if SECTEUR_ALL else [],
    "typesTeletravail": [],
    "idNomZonesDeplacement": [],
    "positionNumbersExcluded": [],
    "typeClient": "CADRE",
    "sorts": [{"type": "DATE", "direction": "DESCENDING"}],
    "pagination": {"range": PAGE_SIZE, "startIndex": 0},
    "activeFiltre": True,
    "pointGeolocDeReference": {"distance": 0},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/json",
    "Origin": "https://www.apec.fr",
    "Referer": "https://www.apec.fr/candidat/recherche-emploi.html/emploi",
}


# ============================================================================
# DATABASE MODELS
# ============================================================================

class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


class Ad(Base):
    """Job advertisement storage with deduplication."""
    
    __tablename__ = "ads"
    
    # Primary key: APEC numeric ID
    id = Column(Integer, primary_key=True, autoincrement=False)
    
    # Core offer fields
    numero_offre = Column(Text, nullable=True)
    intitule = Column(Text, nullable=True)  # Job title
    intitule_surbrillance = Column(Text, nullable=True)  # Highlighted title
    
    # Company information
    nom_commercial = Column(Text, nullable=True)  # Company name
    url_logo = Column(Text, nullable=True)  # Company logo URL
    client_reel = Column(Integer, nullable=True)  # Boolean: real client
    offre_confidentielle = Column(Integer, nullable=True)  # Boolean: confidential offer
    
    # Location information
    lieu_texte = Column(Text, nullable=True)  # Location text
    latitude = Column(Text, nullable=True)  # GPS latitude
    longitude = Column(Text, nullable=True)  # GPS longitude
    localisable = Column(Integer, nullable=True)  # Boolean: can be geolocated
    
    # Job details
    texte_offre = Column(Text, nullable=True)  # Full job description
    salaire_texte = Column(Text, nullable=True)  # Salary information
    type_contrat = Column(Integer, nullable=True)  # Contract type ID
    contract_duration = Column(Integer, nullable=True)  # Contract duration
    
    # Categorization
    secteur_activite = Column(Integer, nullable=True)  # Activity sector ID
    secteur_activite_parent = Column(Integer, nullable=True)  # Parent sector ID
    origine_code = Column(Integer, nullable=True)  # Origin code
    
    # Dates
    date_publication = Column(Text, nullable=True)  # Publication date
    date_validation = Column(Text, nullable=True)  # Validation date
    
    # Remote work & quality indicators
    id_nom_teletravail = Column(Integer, nullable=True)  # Remote work ID
    indicateur_oqa = Column(Integer, nullable=True)  # Boolean: OQA indicator
    indicateur_faible_candidature = Column(Integer, nullable=True)  # Boolean: low candidacy indicator
    
    # Scoring & metadata
    score = Column(Text, nullable=True)  # Relevance score (stored as text for precision)
    
    # Full raw payload for future analysis
    payload_json = Column(Text, nullable=False)
    
    # Tracking timestamps
    first_seen_at = Column(Text, nullable=False)
    last_seen_at = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<Ad(id={self.id}, intitule={self.intitule!r})>"


class Run(Base):
    """Crawl run tracking for observability."""
    
    __tablename__ = "runs"
    
    run_id = Column(String, primary_key=True)
    started_at = Column(Text, nullable=False)
    ended_at = Column(Text, nullable=True)
    ads_fetched = Column(Integer, default=0)
    pages_fetched = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Run(run_id={self.run_id}, ads_fetched={self.ads_fetched})>"


# ============================================================================
# DATABASE UTILITIES
# ============================================================================

def init_database(db_path: str) -> sessionmaker:
    """Initialize database connection and create tables.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        SQLAlchemy sessionmaker factory
    """
    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Create engine with connection pooling disabled for SQLite
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    return sessionmaker(bind=engine)


def upsert_ad(session: Session, offer: Dict[str, Any], now_iso: str) -> bool:
    """Insert or update a single ad with conflict resolution.
    
    Args:
        session: SQLAlchemy session
        offer: Raw offer dictionary from API
        now_iso: Current timestamp in ISO format
        
    Returns:
        True if new ad, False if updated existing
    """
    offer_id = offer.get("id")
    if not offer_id:
        return False
    
    # Try to parse as integer
    try:
        offer_id = int(offer_id)
    except (ValueError, TypeError):
        return False
    
    # Helper to convert boolean to int (SQLite)
    def bool_to_int(val) -> int | None:
        if val is None:
            return None
        return 1 if val else 0
    
    # Helper to convert float to string for precision
    def float_to_str(val) -> str | None:
        if val is None:
            return None
        return str(val)
    
    # Check if ad exists
    existing = session.get(Ad, offer_id)
    
    if existing:
        # Update existing ad
        existing.last_seen_at = now_iso
        existing.payload_json = json.dumps(offer, ensure_ascii=False)
        
        # Update all extracted fields (in case they changed)
        existing.numero_offre = offer.get("numeroOffre")
        existing.intitule = offer.get("intitule")
        existing.intitule_surbrillance = offer.get("intituleSurbrillance")
        existing.nom_commercial = offer.get("nomCommercial")
        existing.url_logo = offer.get("urlLogo")
        existing.client_reel = bool_to_int(offer.get("clientReel"))
        existing.offre_confidentielle = bool_to_int(offer.get("offreConfidentielle"))
        existing.lieu_texte = offer.get("lieuTexte")
        existing.latitude = offer.get("latitude")
        existing.longitude = offer.get("longitude")
        existing.localisable = bool_to_int(offer.get("localisable"))
        existing.texte_offre = offer.get("texteOffre")
        existing.salaire_texte = offer.get("salaireTexte")
        existing.type_contrat = offer.get("typeContrat")
        existing.contract_duration = offer.get("contractDuration")
        existing.secteur_activite = offer.get("secteurActivite")
        existing.secteur_activite_parent = offer.get("secteurActiviteParent")
        existing.origine_code = offer.get("origineCode")
        existing.date_publication = offer.get("datePublication")
        existing.date_validation = offer.get("dateValidation")
        existing.id_nom_teletravail = offer.get("idNomTeletravail")
        existing.indicateur_oqa = bool_to_int(offer.get("indicateurOqa"))
        existing.indicateur_faible_candidature = bool_to_int(offer.get("indicateurFaibleCandidature"))
        existing.score = float_to_str(offer.get("score"))
        
        return False
    else:
        # Insert new ad
        ad = Ad(
            id=offer_id,
            numero_offre=offer.get("numeroOffre"),
            intitule=offer.get("intitule"),
            intitule_surbrillance=offer.get("intituleSurbrillance"),
            nom_commercial=offer.get("nomCommercial"),
            url_logo=offer.get("urlLogo"),
            client_reel=bool_to_int(offer.get("clientReel")),
            offre_confidentielle=bool_to_int(offer.get("offreConfidentielle")),
            lieu_texte=offer.get("lieuTexte"),
            latitude=offer.get("latitude"),
            longitude=offer.get("longitude"),
            localisable=bool_to_int(offer.get("localisable")),
            texte_offre=offer.get("texteOffre"),
            salaire_texte=offer.get("salaireTexte"),
            type_contrat=offer.get("typeContrat"),
            contract_duration=offer.get("contractDuration"),
            secteur_activite=offer.get("secteurActivite"),
            secteur_activite_parent=offer.get("secteurActiviteParent"),
            origine_code=offer.get("origineCode"),
            date_publication=offer.get("datePublication"),
            date_validation=offer.get("dateValidation"),
            id_nom_teletravail=offer.get("idNomTeletravail"),
            indicateur_oqa=bool_to_int(offer.get("indicateurOqa")),
            indicateur_faible_candidature=bool_to_int(offer.get("indicateurFaibleCandidature")),
            score=float_to_str(offer.get("score")),
            payload_json=json.dumps(offer, ensure_ascii=False),
            first_seen_at=now_iso,
            last_seen_at=now_iso,
        )
        session.add(ad)
        return True


# ============================================================================
# HTTP UTILITIES
# ============================================================================

def get_proxy_config() -> Optional[Dict[str, str]]:
    """Get proxy configuration from environment variables.
    
    Supports both simple proxy URLs and username/password authentication.
    If PROXY_USERNAME and PROXY_PASSWORD are set, they will be injected into the URL.
    
    Returns:
        Dict with 'http' and 'https' keys if proxies configured, else None
    """
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    
    # Check for proxy authentication credentials
    proxy_username = os.environ.get("PROXY_USERNAME")
    proxy_password = os.environ.get("PROXY_PASSWORD")
    
    # If we have credentials but no full proxy URL, build one
    if proxy_username and proxy_password and not (http_proxy or https_proxy):
        # Default proxy host - update this if you have a different proxy server
        proxy_host = os.environ.get("PROXY_HOST", "p.webshare.io:80")
        auth_proxy = f"http://{proxy_username}:{proxy_password}@{proxy_host}"
        return {
            "http": auth_proxy,
            "https": auth_proxy,
        }
    
    # If we have a proxy URL but also have credentials, inject them
    if proxy_username and proxy_password and (http_proxy or https_proxy):
        proxy_url = https_proxy or http_proxy
        # Parse and inject credentials if not already present
        if "@" not in proxy_url:
            # Extract protocol and rest
            if "://" in proxy_url:
                protocol, rest = proxy_url.split("://", 1)
                auth_proxy = f"{protocol}://{proxy_username}:{proxy_password}@{rest}"
            else:
                auth_proxy = f"http://{proxy_username}:{proxy_password}@{proxy_url}"
            return {
                "http": auth_proxy,
                "https": auth_proxy,
            }
    
    if http_proxy or https_proxy:
        return {
            "http": http_proxy or https_proxy,
            "https": https_proxy or http_proxy,
        }
    return None


def exponential_backoff_sleep(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0):
    """Sleep with exponential backoff and jitter.
    
    Args:
        attempt: Retry attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
    sleep_time = delay + jitter
    print(f"    ⏳ Backing off for {sleep_time:.2f}s (attempt {attempt + 1})")
    time.sleep(sleep_time)


def fetch_page(
    session: requests.Session,
    start_index: int,
    proxies: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Fetch one page of job offers with retry logic.
    
    Args:
        session: Requests session with headers
        start_index: Starting index for pagination
        proxies: Optional proxy configuration
        
    Returns:
        API response dictionary
        
    Raises:
        requests.HTTPError: If request fails after retries
        SystemExit: If authentication fails (401/403)
    """
    payload = REQUEST_TEMPLATE.copy()
    payload["pagination"] = {"range": PAGE_SIZE, "startIndex": start_index}
    
    url = f"{BASE_URL}{ENDPOINT_PATH}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.post(
                url,
                json=payload,
                timeout=REQUEST_TIMEOUT,
                proxies=proxies,
            )
            
            # Handle authentication errors immediately
            if response.status_code in (401, 403):
                print(f"\n❌ Authentication failed (HTTP {response.status_code})")
                print("Check API access or credentials.")
                sys.exit(1)
            
            # Handle rate limiting with backoff
            if response.status_code == 429:
                print(f"    ⚠️  Rate limited (429)")
                if attempt < MAX_RETRIES - 1:
                    exponential_backoff_sleep(attempt)
                    continue
                else:
                    response.raise_for_status()
            
            # Handle server errors with backoff
            if response.status_code >= 500:
                print(f"    ⚠️  Server error ({response.status_code})")
                if attempt < MAX_RETRIES - 1:
                    exponential_backoff_sleep(attempt)
                    continue
                else:
                    response.raise_for_status()
            
            # Success
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            print(f"    ⚠️  Request timeout")
            if attempt < MAX_RETRIES - 1:
                exponential_backoff_sleep(attempt)
            else:
                raise
                
        except requests.exceptions.ConnectionError as e:
            print(f"    ⚠️  Connection error: {e}")
            if attempt < MAX_RETRIES - 1:
                exponential_backoff_sleep(attempt)
            else:
                raise
    
    raise requests.HTTPError(f"Failed after {MAX_RETRIES} retries")


# ============================================================================
# MAIN CRAWLER
# ============================================================================

def crawl_all_ads(
    session_maker: sessionmaker,
    http_session: requests.Session,
    proxies: Optional[Dict[str, str]],
) -> tuple[str, int, int]:
    """Main crawl loop: paginate through all ads and persist to DB.
    
    Args:
        session_maker: SQLAlchemy session factory
        http_session: Requests session with headers
        proxies: Optional proxy configuration
        
    Returns:
        Tuple of (run_id, total_ads_fetched, total_pages_fetched)
    """
    # Create run record
    run_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    
    with session_maker() as db_session:
        run = Run(
            run_id=run_id,
            started_at=now_iso,
            ads_fetched=0,
            pages_fetched=0,
            notes="Full crawl of all APEC job ads",
        )
        db_session.add(run)
        db_session.commit()
    
    print(f"🚀 Starting crawl run: {run_id}")
    print(f"📊 Page size: {PAGE_SIZE}")
    print(f"⏱️  Request delay: {REQUEST_DELAY_SECONDS}s")
    print(f"🔄 Max retries: {MAX_RETRIES}")
    if proxies:
        print(f"🌐 Using proxy: {proxies.get('https', proxies.get('http'))}")
    print()
    
    start_index = 0
    total_ads_saved = 0
    total_pages = 0
    new_ads_count = 0
    updated_ads_count = 0
    
    while True:
        # Check max pages limit
        if MAX_PAGES and total_pages >= MAX_PAGES:
            print(f"\n⚠️  Reached MAX_PAGES limit ({MAX_PAGES})")
            break
        
        print(f"📄 Page {total_pages + 1} (index {start_index})...", end=" ", flush=True)
        
        try:
            response = fetch_page(http_session, start_index, proxies)
        except (requests.HTTPError, requests.RequestException) as e:
            print(f"\n❌ Request failed: {e}")
            break
        
        # Extract offers from response
        offers = response.get("resultats", [])
        total_available = response.get("totalCount", 0)
        
        if not offers:
            print("no results (end of pagination)")
            break
        
        print(f"fetched {len(offers)} offers", end=" ", flush=True)
        
        # Process offers in a transaction
        now_iso = datetime.now(timezone.utc).isoformat()
        page_new = 0
        page_updated = 0
        
        with session_maker() as db_session:
            for offer in offers:
                is_new = upsert_ad(db_session, offer, now_iso)
                if is_new:
                    page_new += 1
                else:
                    page_updated += 1
            
            db_session.commit()
        
        new_ads_count += page_new
        updated_ads_count += page_updated
        total_ads_saved += page_new  # Only count new ads
        total_pages += 1
        
        print(f"→ {page_new} new, {page_updated} updated (total: {total_ads_saved} new)")
        
        # Check if we've reached the end
        next_index = start_index + PAGE_SIZE
        if next_index >= total_available:
            print(f"\n✅ Reached end of results (total available: {total_available})")
            break
        
        start_index = next_index
        
        # Polite delay between requests
        time.sleep(REQUEST_DELAY_SECONDS)
    
    # Update run record
    end_iso = datetime.now(timezone.utc).isoformat()
    with session_maker() as db_session:
        run = db_session.get(Run, run_id)
        if run:
            run.ended_at = end_iso
            run.ads_fetched = new_ads_count + updated_ads_count
            run.pages_fetched = total_pages
            db_session.commit()
    
    return run_id, new_ads_count + updated_ads_count, total_pages


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main execution: crawl all APEC ads and persist to SQLite."""
    load_dotenv()  # Load environment variables from .env file if present
    
    print("=" * 70)
    print("APEC Full Ads Crawler")
    print("=" * 70)
    print()
    
    # Initialize database
    print(f"📁 Database: {DB_PATH}")
    session_maker = init_database(DB_PATH)
    
    # Setup HTTP session
    http_session = requests.Session()
    http_session.headers.update(HEADERS)
    
    # Get proxy configuration
    proxies = get_proxy_config()
    
    # Record start time
    start_time = time.time()
    
    # Run crawler
    try:
        run_id, ads_fetched, pages_fetched = crawl_all_ads(
            session_maker,
            http_session,
            proxies,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Calculate duration
    duration_seconds = time.time() - start_time
    duration_minutes = duration_seconds / 60
    
    # Get final database stats
    with session_maker() as db_session:
        total_unique_ads = db_session.execute(
            select(func.count(Ad.id))
        ).scalar()
    
    # Print summary
    print()
    print("=" * 70)
    print("CRAWL SUMMARY")
    print("=" * 70)
    print(f"Run ID:           {run_id}")
    print(f"Ads fetched:      {ads_fetched:,}")
    print(f"Pages fetched:    {pages_fetched:,}")
    print(f"Unique ads in DB: {total_unique_ads:,}")
    print(f"Duration:         {duration_minutes:.2f} minutes ({duration_seconds:.1f}s)")
    print(f"Database:         {Path(DB_PATH).absolute()}")
    print("=" * 70)
    print()
    print("✅ Crawl completed successfully!")


if __name__ == "__main__":
    main()
