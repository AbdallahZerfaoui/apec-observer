"""Entry point for apec-observer ingestion."""

from ingestion.main import run_ingestion


def main():
    """Run APEC job offers ingestion."""
    run_ingestion()


if __name__ == "__main__":
    main()
