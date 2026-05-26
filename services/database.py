import os
import psycopg2
import logging

DATABASE_URL = os.environ.get("DATABASE_URL")
logger = logging.getLogger(__name__)

def run_query(query, params=(), fetch=False):
    """Executes a database query safely."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall() if fetch else None
        conn.commit()
        return result
    except Exception as e:
        logger.error(f"Database error: {e}")
        if conn: conn.rollback()
        return [] if fetch else None
    finally:
        if conn: conn.close()
