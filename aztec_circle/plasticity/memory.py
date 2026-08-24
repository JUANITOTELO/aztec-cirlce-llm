"""
Persistent experience memory (long-term potentiation for the circle).

SQLite-backed record of completed runs, recurring flaw categories, and
per-persona token efficiency. `insights_for_goal` distills this history into a
compact "institutional memory" block that is injected into Peer drafting
prompts, so the drafter starts from everything the circle has already learned.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple
import structlog

log = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    task_id     TEXT PRIMARY KEY,
    ts          REAL NOT NULL,
    goal        TEXT NOT NULL,
    status      TEXT NOT NULL,
    loops_used  INTEGER NOT NULL DEFAULT 0,
    final_score REAL NOT NULL DEFAULT 0.0,
    cost_usd    REAL NOT NULL DEFAULT 0.0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    tier        TEXT NOT NULL DEFAULT 'standard'
);
CREATE TABLE IF NOT EXISTS flaw_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL NOT NULL,
    task_id     TEXT NOT NULL,
    category    TEXT NOT NULL,
    category_hash TEXT NOT NULL,
    severity    TEXT NOT NULL DEFAULT 'HIGH',
    detail      TEXT NOT NULL DEFAULT '',
    mitigation  TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_flaw_hash ON flaw_events(category_hash);
CREATE INDEX IF NOT EXISTS idx_runs_ts ON runs(ts);
"""


def _category_key(flaw_text: str) -> Tuple[str, str]:
    """
    Reduce a free-form flaw string to a stable (category, hash) pair so
    recurrence detection works across paraphrasing.
    """
    text = (flaw_text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = [w for w in text.split() if len(w) > 2][:12]
    normalized = " ".join(words)
    return normalized[:160], hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


class ExperienceMemory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ── Lifecycle ────────────────────────────────────────────────────────
    def _connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── Writes ───────────────────────────────────────────────────────────
    def record_run(
        self,
        task_id: str,
        goal: str,
        status: str,
        loops_used: int,
        final_score: float,
        cost_usd: float,
        total_tokens: int,
        tier: str = "standard",
    ) -> None:
        try:
            conn = self._connection()
            conn.execute(
                "INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    time.time(),
                    goal or "",
                    status,
                    int(loops_used),
                    float(final_score or 0.0),
                    float(cost_usd or 0.0),
                    int(total_tokens or 0),
                    tier or "standard",
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            log.warning("memory.record_run_failed", error=str(exc))

    def record_flaws(
        self,
        task_id: str,
        flaws: List[str],
        mitigations: Optional[List[str]] = None,
        severity: str = "HIGH",
    ) -> List[Tuple[str, str]]:
        """Persist flaw events; returns their (category, hash) pairs."""
        try:
            conn = self._connection()
            now = time.time()
            cats: List[Tuple[str, str]] = []
            mitigations = mitigations or []
            for i, flaw in enumerate(flaws or []):
                if not flaw or not flaw.strip():
                    continue
                category, chash = _category_key(flaw)
                mitigation = mitigations[i] if i < len(mitigations) else ""
                conn.execute(
                    "INSERT INTO flaw_events (ts, task_id, category, category_hash, severity, detail, mitigation)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (now, task_id, category, chash, severity, flaw.strip(), mitigation),
                )
                cats.append((category, chash))
            conn.commit()
            return cats
        except sqlite3.Error as exc:
            log.warning("memory.record_flaws_failed", error=str(exc))
            return []

    def known_category_hashes(self) -> set:
        """Set of all category hashes currently persisted."""
        try:
            conn = self._connection()
            rows = conn.execute("SELECT DISTINCT category_hash FROM flaw_events").fetchall()
            return {r["category_hash"] for r in rows}
        except sqlite3.Error:
            return set()

    # ── Reads / distillation ─────────────────────────────────────────────
    def first_pass_approval_rate(self, window: int = 20) -> Optional[float]:
        try:
            conn = self._connection()
            rows = conn.execute(
                "SELECT status, loops_used FROM runs ORDER BY ts DESC LIMIT ?",
                (window,),
            ).fetchall()
            if not rows:
                return None
            clean = [r for r in rows if r["status"] in ("APPROVED", "ESCALATED_BEST_EFFORT")]
            if not clean:
                return 0.0
            first_pass = sum(1 for r in clean if r["status"] == "APPROVED" and r["loops_used"] <= 0)
            return round(first_pass / len(clean), 3)
        except sqlite3.Error:
            return None

    def top_recurring_flaws(self, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            conn = self._connection()
            rows = conn.execute(
                """
                SELECT category_hash, MAX(category) AS category,
                       COUNT(*) AS occurrences,
                       MAX(detail) AS detail,
                       (SELECT mitigation FROM flaw_events f2
                        WHERE f2.category_hash = f1.category_hash AND f2.mitigation != ''
                        ORDER BY ts DESC LIMIT 1) AS mitigation,
                       MAX(ts) AS last_ts
                FROM flaw_events f1
                GROUP BY category_hash
                HAVING occurrences > 0
                ORDER BY occurrences DESC, last_ts DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            log.warning("memory.top_flaws_failed", error=str(exc))
            return []

    def insights_for_goal(self, max_insights: int = 5) -> Optional[str]:
        """
        Distill institutional memory into a prompt-injectable block.
        Returns None when there is nothing useful to say yet.
        """
        recurring = self.top_recurring_flaws(limit=max_insights)
        rate = self.first_pass_approval_rate()
        if not recurring:
            return None

        lines: List[str] = ["INSTITUTIONAL MEMORY (learned from previous runs):"]
        if rate is not None and rate >= 0.6:
            lines.append(
                f"- This installation resolves {int(rate * 100)}% of tasks on the first loop; "
                "prioritize getting the architecture right before writing code."
            )
        for item in recurring:
            occ = int(item.get("occurrences") or 0)
            if occ < 2:
                continue  # one-off flaws are noise, not lessons
            detail = str(item.get("detail") or item.get("category") or "")[:180]
            line = f"- RECURRING FLAW ({occ}x): {detail}"
            mitigation = str(item.get("mitigation") or "")
            if mitigation:
                line += f" → PROVEN FIX: {mitigation[:180]}"
            lines.append(line)
        if len(lines) <= 1:
            return None
        return "\n".join(lines)

    def stats(self) -> Dict[str, object]:
        try:
            conn = self._connection()
            runs = conn.execute("SELECT COUNT(*) AS c FROM runs").fetchone()["c"]
            flaws = conn.execute("SELECT COUNT(*) AS c FROM flaw_events").fetchone()["c"]
            distinct = conn.execute(
                "SELECT COUNT(DISTINCT category_hash) AS c FROM flaw_events"
            ).fetchone()["c"]
            avg_score = conn.execute(
                "SELECT AVG(final_score) AS a FROM runs"
            ).fetchone()["a"] or 0.0
            return {
                "total_runs": runs,
                "flaw_events": flaws,
                "distinct_flaw_categories": distinct,
                "avg_final_score": round(float(avg_score), 3),
            }
        except sqlite3.Error:
            return {"total_runs": 0, "flaw_events": 0, "distinct_flaw_categories": 0, "avg_final_score": 0.0}

    def reset(self) -> None:
        try:
            conn = self._connection()
            conn.execute("DELETE FROM runs")
            conn.execute("DELETE FROM flaw_events")
            conn.commit()
        except sqlite3.Error as exc:
            log.warning("memory.reset_failed", error=str(exc))

    def export_state(self) -> str:
        return json.dumps(self.stats(), default=str)
