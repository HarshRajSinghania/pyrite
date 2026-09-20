"""
SQLiteBackend — SearchBackend implementation backed by SQLite + FTS5 + sqlite-vec.

Inherits shared ORM/SQL logic from BaseBackend.  Only overrides:
- ``_exec`` / ``_exec_one`` / ``_exec_scalar`` (raw sqlite3 connection)
- ``_sync_links`` (diff-based sync)
- Full-text search (FTS5)
- Embedding operations (sqlite-vec)
"""

from __future__ import annotations

import copy
import struct
from typing import Any, ClassVar

from ..models import Link
from .base_backend import BaseBackend
from .capabilities import BackendCapability


class SQLiteBackend(BaseBackend):
    """SearchBackend implementation for SQLite + FTS5 + sqlite-vec."""

    # SQLite implements the full backend protocol: entity CRUD (BaseBackend),
    # FTS5 keyword search, and sqlite-vec embeddings. EMBEDDING is declared at
    # the class level ("can in principle"); whether sqlite-vec is loaded right
    # now is a separate runtime gate (``vec_available``). See capabilities.py.
    capabilities: ClassVar[set[BackendCapability]] = {
        BackendCapability.ENTITY,
        BackendCapability.SEARCH,
        BackendCapability.EMBEDDING,
    }

    def __init__(
        self,
        session,
        raw_conn,
        vec_available: bool = False,
        owner=None,
    ):
        # `owner` is the PyriteDB that built this backend. When given,
        # `self._session` resolves through it to the *current scope's* session
        # rather than caching one object for the backend's whole lifetime —
        # the shared-session bug (#131). An explicit `session` is still
        # accepted for callers that construct a backend with one they own
        # (diff/overlay backends, tests).
        self._owner = owner
        self._explicit_session = session
        self._raw_conn = raw_conn
        self.vec_available = vec_available

    @property
    def _session(self):
        """The session for the current scope (see ``PyriteDB.session``)."""
        if self._owner is not None:
            return self._owner.session
        return self._explicit_session

    @_session.setter
    def _session(self, value):
        self._explicit_session = value

    def for_owner(self, owner) -> SQLiteBackend:
        """A copy of this backend whose session resolves through *owner*.

        Used by ``PyriteDB.request_handle()`` so a per-request handle's ORM
        reads use that request's session while still sharing the engine, pool
        and raw connection (#131).
        """
        clone = copy.copy(self)
        clone._owner = owner
        return clone

    def close(self) -> None:
        """No-op — connection lifecycle owned by PyriteDB."""

    # =====================================================================
    # Raw SQL helpers (sqlite3 positional-param style via _raw_conn)
    # =====================================================================

    def _raw_cursor(self):
        """Serialised private cursor on the shared raw sqlite3 connection.

        ``_raw_conn`` is one connection shared by every caller — the same
        lifetime shape the session had (#131 criterion 7). sqlite3 serialises
        individual statements, but ``Connection.execute()`` returns a cursor
        whose rows are fetched afterwards, and with
        ``check_same_thread=False`` two threads can interleave execute and
        fetch on one implicit cursor. A private cursor under the owner's lock
        removes that without opening a second connection per request.

        Falls back to the bare connection when no owner supplied a lock (a
        backend constructed directly in a test).
        """
        if self._owner is not None:
            return self._owner._raw_cursor()

        from contextlib import nullcontext

        return nullcontext(self._raw_conn)

    def _exec(self, sql: str, params: dict | None = None) -> list[dict[str, Any]]:
        """Execute raw SQL via the raw sqlite3 connection.

        Translates ``:named`` params to ``?``-style for sqlite3.
        """
        sql_out, param_list = self._translate_params(sql, params)
        with self._raw_cursor() as cur:
            rows = cur.execute(sql_out, param_list).fetchall()
        return [dict(r) for r in rows]

    def _exec_one(self, sql: str, params: dict | None = None) -> dict | None:
        sql_out, param_list = self._translate_params(sql, params)
        with self._raw_cursor() as cur:
            row = cur.execute(sql_out, param_list).fetchone()
        if row is None:
            return None
        return dict(row)

    def _exec_scalar(self, sql: str, params: dict | None = None):
        sql_out, param_list = self._translate_params(sql, params)
        with self._raw_cursor() as cur:
            row = cur.execute(sql_out, param_list).fetchone()
        return row[0] if row else None

    @staticmethod
    def _translate_params(sql: str, params: dict | None) -> tuple[str, list]:
        """Convert ``:name`` placeholders to ``?`` with a positional param list.

        This lets the base class use ``:named`` style everywhere while
        SQLite's raw connection receives ``?``-style it expects.
        """
        if not params:
            return sql, []

        import re

        param_list: list[Any] = []

        # Match :word_chars but not ::double-colon (Postgres cast)
        def _replacer(m):
            name = m.group(1)
            param_list.append(params[name])
            return "?"

        sql_out = re.sub(r"(?<!:):([a-zA-Z_]\w*)", _replacer, sql)
        return sql_out, param_list

    # =====================================================================
    # _sync_links (diff-based — SQLite-specific)
    # =====================================================================

    def _sync_links(self, entry_id: str, kb_name: str, links: list[dict[str, Any]]) -> None:
        from ...schema import get_inverse_relation

        # Build desired state as a dict keyed by (target_id, target_kb, relation)
        desired: dict[tuple[str, str, str], dict[str, Any]] = {}
        for link in links:
            relation = link.get("relation", "related_to")
            target_kb = link.get("kb", kb_name)
            target_id = link.get("target", "")
            key = (target_id, target_kb, relation)
            desired[key] = {
                "note": link.get("note", ""),
                "inverse_relation": get_inverse_relation(relation),
            }

        # Load existing links from DB
        existing = self._session.query(Link).filter_by(source_id=entry_id, source_kb=kb_name).all()

        existing_keys: dict[tuple[str, str, str], Link] = {}
        for row in existing:
            key = (row.target_id, row.target_kb, row.relation)
            existing_keys[key] = row

        # Delete links no longer in desired set
        for key, row in existing_keys.items():
            if key not in desired:
                self._session.delete(row)

        # Add new links and update changed ones
        for key, attrs in desired.items():
            if key in existing_keys:
                # Update note/inverse if changed
                row = existing_keys[key]
                if row.note != attrs["note"] or row.inverse_relation != attrs["inverse_relation"]:
                    row.note = attrs["note"]
                    row.inverse_relation = attrs["inverse_relation"]
            else:
                # Insert new link
                target_id, target_kb, relation = key
                self._session.add(
                    Link(
                        source_id=entry_id,
                        source_kb=kb_name,
                        target_id=target_id,
                        target_kb=target_kb,
                        relation=relation,
                        inverse_relation=attrs["inverse_relation"],
                        note=attrs["note"],
                    )
                )

    # =====================================================================
    # Full-text search (FTS5)
    # =====================================================================

    def search(
        self,
        query: str,
        kb_name: str | None = None,
        kb_names: set[str] | list[str] | None = None,
        entry_type: str | None = None,
        tags: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_archived: bool = False,
        lifecycle: str | None = None,
        fips: str | None = None,
        state: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                e.id, e.kb_name, e.entry_type, e.title, e.body, e.summary,
                e.file_path, e.date, e.importance, e.status, e.location,
                e.lifecycle, e.metadata, e.created_at, e.updated_at, e.indexed_at,
                e.created_by, e.modified_by,
                snippet(entry_fts, 4, '<mark>', '</mark>', '...', 32) as snippet,
                bm25(entry_fts) as rank
            FROM entry_fts
            JOIN entry e ON entry_fts.rowid = e.rowid
            WHERE entry_fts MATCH ?
        """
        params: list[Any] = [query]
        if lifecycle:
            sql += " AND e.lifecycle = ?"
            params.append(lifecycle)
        elif not include_archived:
            sql += " AND COALESCE(e.lifecycle, 'active') != 'archived'"
        if kb_name:
            sql += " AND e.kb_name = ?"
            params.append(kb_name)
        if kb_names is not None:
            names = list(kb_names)
            if names:
                sql += f" AND e.kb_name IN ({','.join('?' * len(names))})"
                params.extend(names)
            else:
                sql += " AND 0"
        if entry_type:
            sql += " AND e.entry_type = ?"
            params.append(entry_type)
        if date_from:
            sql += " AND e.date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND e.date <= ?"
            params.append(date_to)
        if tags:
            tag_placeholders = ",".join(["?"] * len(tags))
            sql += f"""
                AND e.id IN (
                    SELECT et.entry_id FROM entry_tag et
                    JOIN tag t ON et.tag_id = t.id
                    WHERE t.name IN ({tag_placeholders})
                    GROUP BY et.entry_id, et.kb_name
                    HAVING COUNT(DISTINCT t.name) = ?
                )
            """
            params.extend(tags)
            params.append(len(tags))
        if fips:
            sql += " AND e.fips = ?"
            params.append(fips)
        if state:
            sql += " AND e.state = ?"
            params.append(state)
        if status:
            sql += " AND e.status = ?"
            params.append(status)
        sql += " ORDER BY rank LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self._raw_cursor() as cur:
            rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def search_by_tag(
        self, tag: str, kb_name: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT e.* FROM entry e
            JOIN entry_tag et ON e.id = et.entry_id AND e.kb_name = et.kb_name
            JOIN tag t ON et.tag_id = t.id
            WHERE t.name = ?
        """
        params: list[Any] = [tag]
        if kb_name:
            sql += " AND e.kb_name = ?"
            params.append(kb_name)
        sql += " ORDER BY e.date DESC, e.title LIMIT ?"
        params.append(limit)
        with self._raw_cursor() as cur:
            rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def search_by_date_range(
        self,
        date_from: str,
        date_to: str,
        kb_name: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM entry WHERE date >= ? AND date <= ?"
        params: list[Any] = [date_from, date_to]
        if kb_name:
            sql += " AND kb_name = ?"
            params.append(kb_name)
        sql += " ORDER BY date ASC LIMIT ?"
        params.append(limit)
        with self._raw_cursor() as cur:
            rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def search_by_tag_prefix(
        self, prefix: str, kb_name: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT DISTINCT e.* FROM entry e
            JOIN entry_tag et ON e.id = et.entry_id AND e.kb_name = et.kb_name
            JOIN tag t ON et.tag_id = t.id
            WHERE (t.name = ? OR t.name LIKE ?)
        """
        params: list[Any] = [prefix, prefix + "/%"]
        if kb_name:
            sql += " AND e.kb_name = ?"
            params.append(kb_name)
        sql += " ORDER BY e.date DESC, e.title LIMIT ?"
        params.append(limit)
        with self._raw_cursor() as cur:
            rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # =====================================================================
    # Semantic search (sqlite-vec embeddings)
    # =====================================================================

    @staticmethod
    def _embedding_to_blob(embedding: list[float]) -> bytes:
        return struct.pack(f"{len(embedding)}f", *embedding)

    def upsert_embedding(self, entry_id: str, kb_name: str, embedding: list[float]) -> bool:
        if not self.vec_available:
            return False
        # One critical section: the rowid lookup, the delete and the insert
        # are a read-modify-write, and a concurrent writer between them would
        # orphan or duplicate the vector row.
        with self._raw_cursor() as cur:
            row = cur.execute(
                "SELECT rowid FROM entry WHERE id = ? AND kb_name = ?",
                (entry_id, kb_name),
            ).fetchone()
            if not row:
                return False
            rowid = row[0]
            blob = self._embedding_to_blob(embedding)
            cur.execute("DELETE FROM vec_entry WHERE rowid = ?", (rowid,))
            cur.execute("INSERT INTO vec_entry(rowid, embedding) VALUES (?, ?)", (rowid, blob))
            self._raw_conn.commit()
        return True

    def search_semantic(
        self,
        embedding: list[float],
        kb_name: str | None = None,
        limit: int = 20,
        max_distance: float = 1.3,
    ) -> list[dict[str, Any]]:
        if not self.vec_available:
            return []
        blob = self._embedding_to_blob(embedding)
        fetch_limit = limit * 3 if kb_name else limit * 2
        with self._raw_cursor() as cur:
            rows = cur.execute(
                """
                SELECT v.rowid, v.distance, e.*
                FROM vec_entry v
                JOIN entry e ON v.rowid = e.rowid
                WHERE v.embedding MATCH ? AND k = ?
                ORDER BY v.distance
                """,
                (blob, fetch_limit),
            ).fetchall()
        results = []
        for row in rows:
            entry = dict(row)
            distance = entry.get("distance", 0)
            if distance > max_distance:
                continue
            if kb_name and entry.get("kb_name") != kb_name:
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    def has_embeddings(self) -> bool:
        if not self.vec_available:
            return False
        with self._raw_cursor() as cur:
            row = cur.execute("SELECT COUNT(*) FROM vec_entry").fetchone()
        return row[0] > 0

    def embedding_stats(self) -> dict[str, Any]:
        if not self.vec_available:
            return {"available": False, "count": 0, "total_entries": 0}
        with self._raw_cursor() as cur:
            vec_count = cur.execute("SELECT COUNT(*) FROM vec_entry").fetchone()[0]
            entry_count = cur.execute("SELECT COUNT(*) FROM entry").fetchone()[0]
        return {
            "available": True,
            "count": vec_count,
            "total_entries": entry_count,
            "coverage": f"{vec_count / entry_count * 100:.1f}%" if entry_count > 0 else "0%",
        }

    def get_embedded_rowids(self) -> set[int]:
        if not self.vec_available:
            return set()
        with self._raw_cursor() as cur:
            rows = cur.execute("SELECT rowid FROM vec_entry").fetchall()
        return {r[0] for r in rows}

    def get_entries_for_embedding(self, kb_name: str | None = None) -> list[dict[str, Any]]:
        with self._raw_cursor() as cur:
            if kb_name:
                rows = cur.execute(
                    "SELECT rowid, id, kb_name, title, summary, body FROM entry WHERE kb_name = ?",
                    (kb_name,),
                ).fetchall()
            else:
                rows = cur.execute(
                    "SELECT rowid, id, kb_name, title, summary, body FROM entry"
                ).fetchall()
        return [dict(r) for r in rows]

    def delete_embedding(self, entry_id: str, kb_name: str) -> None:
        if not self.vec_available:
            return
        with self._raw_cursor() as cur:
            row = cur.execute(
                "SELECT rowid FROM entry WHERE id = ? AND kb_name = ?",
                (entry_id, kb_name),
            ).fetchone()
            if row:
                cur.execute("DELETE FROM vec_entry WHERE rowid = ?", (row[0],))
                self._raw_conn.commit()
