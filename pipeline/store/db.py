"""LanceDB store wrapper for Vestio."""
from __future__ import annotations

import warnings
import lancedb
from store.schema import POSTS_SCHEMA, ITEMS_SCHEMA


class VestioStore:
    def __init__(self, db_path: str):
        self.db = lancedb.connect(db_path)
        self._ensure_tables()

    def _list_table_names(self) -> list[str]:
        """Get table names, handling both old and new LanceDB APIs."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = self.db.table_names()
        # table_names() may return a list or a ListTablesResponse
        if isinstance(result, list):
            return result
        if hasattr(result, "tables"):
            return list(result.tables)
        return list(result)

    def _ensure_tables(self):
        existing = self._list_table_names()
        if "posts" not in existing:
            self.db.create_table("posts", schema=POSTS_SCHEMA)
        if "items" not in existing:
            self.db.create_table("items", schema=ITEMS_SCHEMA)

    def table_names(self) -> list[str]:
        return self._list_table_names()

    def add_posts(self, posts: list[dict]):
        table = self.db.open_table("posts")
        table.add(posts)

    def get_posts(self, where: str | None = None, limit: int = 100) -> list[dict]:
        table = self.db.open_table("posts")
        query = table.search().limit(limit)
        if where:
            query = query.where(where)
        return query.to_list()

    def add_items(self, items: list[dict]):
        table = self.db.open_table("items")
        table.add(items)

    def search_items(
        self,
        query_vector: list[float],
        limit: int = 10,
        where: str | None = None,
    ) -> list[dict]:
        table = self.db.open_table("items")
        query = table.search(query_vector).limit(limit)
        if where:
            query = query.where(where)
        return query.to_list()
