"""Storage utilities for SQLite database."""

from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, Integer, DateTime, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


class Base(DeclarativeBase):
    pass


def create_metric_table(config_name: str) -> type[Base]:
    """Dynamically create a table class for a specific config.
    
    Args:
        config_name: Name of the search configuration
        
    Returns:
        SQLAlchemy model class for the metric table
    """
    class_name = f"{config_name.title().replace('_', '')}Metric"
    table_name = f"metric_{config_name}"
    
    return type(
        class_name,
        (Base,),
        {
            "__tablename__": table_name,
            "__mapper_args__": {"eager_defaults": True},
            "id": mapped_column(Integer, primary_key=True, autoincrement=True),
            "value": mapped_column(Integer, nullable=False),
            "retrieved_at": mapped_column(DateTime, nullable=False),
            "__repr__": lambda self: f"{class_name}(id={self.id}, value={self.value})",
        },
    )


class Database:
    """Simple database manager for APEC metrics with separate tables per config."""

    def __init__(self, db_path: Path | str = "data/apec_metrics.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{db_path}")
        self.tables: dict[str, type[Base]] = {}

    def _get_or_create_table(self, config_name: str) -> type[Base]:
        """Get or create table class for a config.
        
        Args:
            config_name: Name of the search configuration
            
        Returns:
            SQLAlchemy model class
        """
        if config_name not in self.tables:
            self.tables[config_name] = create_metric_table(config_name)
            Base.metadata.create_all(self.engine, tables=[self.tables[config_name].__table__])
        return self.tables[config_name]

    def save_metrics(self, metrics: dict[str, dict[str, Any]]) -> None:
        """Save multiple metrics to database, one table per config.

        Args:
            metrics: Dictionary mapping config_name to metric data
                    Example: {"cadres_only": {"value": 123, "retrieved_at": "..."}}
        """
        with Session(self.engine) as session:
            for config_name, data in metrics.items():
                table_class = self._get_or_create_table(config_name)
                metric = table_class(
                    value=data["value"],
                    retrieved_at=datetime.fromisoformat(data["retrieved_at"]),
                )
                session.add(metric)
            session.commit()

    def get_latest_metric(self, config_name: str) -> Any | None:
        """Get the most recent metric for a specific config.

        Args:
            config_name: Name of the search configuration

        Returns:
            Latest metric object or None
        """
        if config_name not in self.tables:
            return None
            
        table_class = self._get_or_create_table(config_name)
        
        with Session(self.engine) as session:
            stmt = select(table_class).order_by(table_class.retrieved_at.desc()).limit(1)
            result = session.execute(stmt).scalar_one_or_none()
            return result

    def get_time_series(self, config_name: str, limit: int = 100) -> list[Any]:
        """Get time series data for a specific config.

        Args:
            config_name: Name of the search configuration
            limit: Maximum number of records to return

        Returns:
            List of metric objects ordered by time (newest first)
        """
        table_class = self._get_or_create_table(config_name)
        
        with Session(self.engine) as session:
            stmt = select(table_class).order_by(table_class.retrieved_at.desc()).limit(limit)
            results = session.execute(stmt).scalars().all()
            return list(results)

