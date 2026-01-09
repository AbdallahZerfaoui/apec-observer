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

MIN_SLEEP = 0.5  # seconds
MAX_SLEEP = 2.0  # seconds

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
    "cadres_only_idf": {
        "lieux":["711"],  # Ile-de-France only
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
    "cades_only_idf_lst_24h": {
        "lieux":["711"],  # Ile-de-France only
        "statutPoste": ["143688", "143689"],  # only cadres
        "typesConvention": ["143684", "143685", "143686", "143687", "143706"],  # 706=partenaires
        "typeClient": "CADRE",
        "anciennetePublication": "101850", # last 24 hours
    },
    "cadres_only_france_lst_7d": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688", "143689"],  # only cadres
        "typesConvention": ["143684", "143685", "143686", "143687", "143706"],  # 706=partenaires
        "typeClient": "CADRE",
        "anciennetePublication": "101851", # last 7 days
    },
    "cades_only_idf_lst_7d": {
        "lieux":["711"],  # Ile-de-France only
        "statutPoste": ["143688", "143689"],  # only cadres
        "typesConvention": ["143684", "143685", "143686", "143687", "143706"],  # 706=partenaires
        "typeClient": "CADRE",
        "anciennetePublication": "101851", # last 7 days
    },
    # Specific convention types
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
    "cadres_france_debutants": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "niveauxExperience": ["101881"],  # 101881=debutants
        "typeClient": "CADRE",
    },
    "cadres_france_3_5y": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "niveauxExperience": ["20043"],  # 20043=3-5 years experience
        "typeClient": "CADRE",
    },
    "cadres_france_6_9y": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "niveauxExperience": ["20044"],  # 20044=6-9 years experience
        "typeClient": "CADRE",
    },
    "cadres_france_10y_plus": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "niveauxExperience": ["20045"],  # 20045=10+ years experience
        "typeClient": "CADRE",
    },
    "cadres_france_20_30k": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "salaireMinimum": "20",  # 20k EUR
        "salaireMaximum": "30",  # 30k EUR
        "typeClient": "CADRE",
    },
    "cadres_france_31_40k": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "salaireMinimum": "31",  # 31k EUR
        "salaireMaximum": "40",  # 40k EUR
        "typeClient": "CADRE",
    },
    "cadres_france_41_50k": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "salaireMinimum": "41",  # 41k EUR
        "salaireMaximum": "50",  # 50k EUR
        "typeClient": "CADRE",
    },
    "cadres_france_51_60k": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "salaireMinimum": "51",  # 51k EUR
        "salaireMaximum": "60",  # 60k EUR
        "typeClient": "CADRE",
    },
    "cadres_france_61_70k": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "salaireMinimum": "61",  # 61k EUR
        "salaireMaximum": "70",  # 70k EUR
        "typeClient": "CADRE",
    },
    "cadres_france_71k_plus": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "salaireMinimum": "71",  # 71k EUR
        "salaireMaximum": "200",  # no upper limit
        "typeClient": "CADRE",
    },
    # Sector specific configs
    "cadres_france_conseil_gestion_entreprise": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "secteursActivite": ["101762"],  # 101762=conseil et gestion d'entreprise
        "typeClient": "CADRE",
    },
    "cadres_france_intermediaires_recrutement": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "secteursActivite": ["101773"],  # 101773=intermediaires en recrutement
        "typeClient": "CADRE",
    },
    "cadres_france_ingenierie": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "secteursActivite": ["101772", "101753"],  # 101772=ingenierie, R&D, 101753=IT
        "typeClient": "CADRE",
    },
    "cadres_france_industrie": {
        "lieux":["799"],  # France only
        "statutPoste": ["143688"],  # only cadres
        "secteursActivite": ["101756", "101774", "101759", "101766", "101779", "101765"],
        "typeClient": "CADRE",
    },
}
