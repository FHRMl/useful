import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "course-kg-dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'coursekg_dev.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    NEO4J_URI = os.getenv("NEO4J_URI", "")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    STRICT_NEO4J = os.getenv("STRICT_NEO4J", "0") == "1"
    SAMPLE_GRAPH_PATH = BASE_DIR / "backend" / "data" / "sample_graph.json"

