import psycopg2
import logging
from vecta_os.core.config import config

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.url = config.DATABASE_URL

    def run_query(self, query: str, params: tuple = (), fetch: bool = False):
        conn = None
        try:
            conn = psycopg2.connect(self.url, sslmode="require")
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall() if fetch else None
            conn.commit()
            return result
        except Exception as e:
            logger.error(f"DB Error: {e}")
            if conn: conn.rollback()
            return [] if fetch else None
        finally:
            if conn: conn.close()

db = DatabaseService()
