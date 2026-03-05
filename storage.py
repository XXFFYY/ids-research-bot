import os
import sqlite3
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

class Storage:
    def get_paper_id_by_key(self, key: str):
        cur = self.conn.execute("SELECT paper_id FROM paper_keys WHERE canonical_key=? LIMIT 1", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def bind_key(self, key: str, paper_id: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO paper_keys(canonical_key,paper_id) VALUES (?,?)",
            (key, paper_id)
        )
        self.conn.commit()
    def get_translation(self, key: str):
        cur = self.conn.execute("SELECT title_zh, tags_zh FROM translations WHERE key=? LIMIT 1", (key,))
        row = cur.fetchone()
        if not row:
            return None
        title_zh, tags_zh = row[0], row[1]
        tags_list = tags_zh.split("||") if tags_zh else []
        return title_zh, tags_list

    def save_translation(self, key: str, title_zh: str, tags_zh: list[str]):
        from datetime import datetime
        self.conn.execute(
            "INSERT OR REPLACE INTO translations(key,title_zh,tags_zh,created_at) VALUES (?,?,?,?)",
            (key, title_zh, "||".join(tags_zh), datetime.utcnow().isoformat())
        )
        self.conn.commit()
    def __init__(self, db_path: str):
        dir_ = os.path.dirname(db_path)
        if dir_:
            os.makedirs(dir_, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()

    def _init_schema(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            key TEXT PRIMARY KEY,
            title_zh TEXT,
            tags_zh TEXT,
            created_at TEXT
        )
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            source TEXT,
            published TEXT,
            venue TEXT,
            abstract TEXT,
            extra TEXT,
            created_at TEXT
        )
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS digests (
            date TEXT PRIMARY KEY,
            markdown TEXT,
            created_at TEXT
        )
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS pushed (
            date TEXT,
            paper_id TEXT,
            PRIMARY KEY (date, paper_id)
        )
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_keys (
            canonical_key TEXT PRIMARY KEY,
            paper_id TEXT
        )
        """)
        self.conn.commit()

    def upsert_paper(self, p: Dict[str, Any]) -> str:
        pid = p.get("id") or _hash((p.get("url","") + p.get("title","")).strip())
        self.conn.execute("""
        INSERT OR REPLACE INTO papers (id,title,url,source,published,venue,abstract,extra,created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            pid,
            p.get("title",""),
            p.get("url",""),
            p.get("source",""),
            p.get("published",""),
            p.get("venue",""),
            p.get("abstract",""),
            p.get("extra",""),
            datetime.utcnow().isoformat()
        ))
        self.conn.commit()
        return pid

    def already_pushed_today(self, date: str, paper_id: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM pushed WHERE date=? AND paper_id=? LIMIT 1", (date, paper_id))
        return cur.fetchone() is not None

    def mark_pushed(self, date: str, paper_ids: List[str]):
        self.conn.executemany("INSERT OR IGNORE INTO pushed(date,paper_id) VALUES (?,?)",
                              [(date, pid) for pid in paper_ids])
        self.conn.commit()

    def save_digest(self, date: str, markdown: str):
        self.conn.execute("""
        INSERT OR REPLACE INTO digests(date, markdown, created_at)
        VALUES (?,?,?)
        """, (date, markdown, datetime.utcnow().isoformat()))
        self.conn.commit()

    def get_recent_papers(self, days: int = 14) -> List[Dict[str, Any]]:
        cur = self.conn.execute("""
        SELECT id,title,url,source,published,venue,abstract,extra
        FROM papers
        ORDER BY published DESC
        LIMIT 500
        """)
        rows = cur.fetchall()
        res = []
        for r in rows:
            res.append({
                "id": r[0], "title": r[1], "url": r[2], "source": r[3],
                "published": r[4], "venue": r[5], "abstract": r[6], "extra": r[7],
            })
        return res

    def close(self):
        self.conn.close()