"""Configuration constants for APEC API."""

BASE_URL = "https://www.apec.fr/cms/webservices"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:146.0) Gecko/20100101 Firefox/146.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/json",
    "Origin": "https://www.apec.fr",
    "Referer": "https://www.apec.fr/candidat/recherche-emploi.html/emploi",
}

REQUEST_TIMEOUT = 30

# Search filter configurations
SEARCH_CONFIGS = {
    "all_jobs_france": {
        "lieux": ["799"],  # France only
    },
    "cadres_only": {
        "statutPoste": ["143688", "143689"],  # only cadres (public and private)
        "typesConvention": ["143684", "143685", "143686", "143687", "143706"],  # 706=partenaires
        "typeClient": "CADRE",
    },
    "cadres_only_france": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688", "143689"],  # only cadres
        "typesConvention": ["143684", "143685", "143686", "143687", "143706"],  # 706=partenaires
        "typeClient": "CADRE",
    },
    "cadres_only_france_lst_24h": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688", "143689"],  # only cadres
        "typesConvention": ["143684", "143685", "143686", "143687", "143706"],  # 706=partenaires
        "typeClient": "CADRE",
        "anciennetePublication": "101850", # last 24 hours
    },
    "cadres_france_entreprises": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "typesConvention": ["143684"],  # 684=entreprises
        "typeClient": "CADRE",
    },
    "cadres_france_cabinets_recrutement": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "typesConvention": ["143685"],  # 685=cabinets de recrutement
        "typeClient": "CADRE",
    },
    "cadres_france_agence_emploi": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "typesConvention": ["143686"],  # 686=agences d'emploi
        "typeClient": "CADRE",
    },
    "cadres_france_ssii": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "typesConvention": ["143687"],  # 687=SSII
        "typeClient": "CADRE",
    },
    "cadres_france_partenaires": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "typesConvention": ["143706"],  # 706=partenaires
        "typeClient": "CADRE",
    },
}
