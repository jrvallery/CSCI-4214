import os
import logging

import pg8000
import pg8000.dbapi

logger = logging.getLogger(__name__)

_conn: pg8000.dbapi.Connection | None = None
_connector = None  # google.cloud.sql.connector.Connector, kept for cleanup


def init_connection() -> None:
    """Open the DB connection. Branches on env vars:
    - CLOUD_SQL_INSTANCE set → Cloud SQL Connector + IAM auth
    - DB_HOST set → direct TCP (local Docker dev / tests)
    """
    global _conn, _connector

    cloud_sql_instance = os.environ.get("CLOUD_SQL_INSTANCE")
    db_name = os.environ.get("DB_NAME", "skiware")

    if cloud_sql_instance:
        from google.cloud.sql.connector import Connector

        db_user = os.environ["DB_USER"]
        password = os.environ.get("DB_PASSWORD")

        _connector = Connector()
        kwargs: dict = {"db": db_name, "user": db_user}
        if password:
            kwargs["password"] = password
        else:
            kwargs["enable_iam_auth"] = True

        logger.info(f"Connecting via Cloud SQL Connector to {cloud_sql_instance} as {db_user}")
        _conn = _connector.connect(cloud_sql_instance, "pg8000", **kwargs)

    else:
        db_host = os.environ.get("DB_HOST", "localhost")
        db_user = os.environ.get("DB_USER", "skiware")
        db_password = os.environ.get("DB_PASSWORD", "skiware")
        db_port = int(os.environ.get("DB_PORT", "5432"))

        logger.info(f"Connecting via TCP to {db_host}:{db_port}/{db_name} as {db_user}")
        _conn = pg8000.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port,
        )


def get_db() -> pg8000.dbapi.Connection:
    """Return the active connection. Raises if init_connection() was not called."""
    if _conn is None:
        raise RuntimeError("DB connection not initialized — call init_connection() first")
    return _conn


def close_connection() -> None:
    """Close the DB connection and Cloud SQL Connector if open."""
    global _conn, _connector
    if _conn is not None:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = None
    if _connector is not None:
        try:
            _connector.close()
        except Exception:
            pass
        _connector = None
