import sqlite3
from models.translation import TranslationMapElement
from core.config import settings

class TranslationCache:
    def __init__(self, db_path: str = settings.database_path):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    id TEXT,
                    book_id TEXT,
                    model_name TEXT,
                    text TEXT NOT NULL,
                    PRIMARY KEY (id, book_id, model_name)
                )
            """)

    def save_batch(self, book_id: str, model_name: str, elements: list[TranslationMapElement]):
        """Saves a batch of translations linked to a specific book."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO cache (id, book_id, model_name, text) VALUES (?, ?, ?, ?)",
                [(el.id, book_id, model_name, el.text) for el in elements]
            )

    def get_translation(self, book_id: str, model_name: str, ref_id: str) -> str | None:
        """Retrieves text only if it matches both ID and Book."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT text FROM cache WHERE id = ? AND book_id = ? AND model_name = ?", 
                (ref_id, book_id, model_name)
            )
            row = cursor.fetchone()
            return row[0] if row else None