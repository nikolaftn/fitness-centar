import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIRECTORY = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIRECTORY / "fitness.db"


def require_database(database_path=DATABASE_PATH):
    """Reports a clear error if the database has not been created manually yet."""
    database_path = Path(database_path)
    if not database_path.is_file():
        raise FileNotFoundError(
            "Database is not initialized. First run: "
            "python reset_test_database.py"
        )


def get_connection(database_path=DATABASE_PATH):
    """Opens the existing local SQLite database."""
    database_path = Path(database_path)
    require_database(database_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
