#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detect and repair mojibake Arabic text in SQLite.

Default mode is dry-run.
Use --apply to write changes.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path


MOJIBAKE_RE = re.compile(r"[\u00D8\u00D9\u00C3\u00C2\u00D0\u00D1\uFFFD]")
ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def likely_mojibake(value: str) -> bool:
    return bool(MOJIBAKE_RE.search(value))


def decode_candidate(value: str, source_encoding: str) -> str | None:
    try:
        return value.encode(source_encoding).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None


def pick_best(value: str) -> str | None:
    if not likely_mojibake(value):
        return None

    candidates = []
    for enc in ("cp1252", "latin1"):
        decoded = decode_candidate(value, enc)
        if decoded is not None:
            candidates.append(decoded)

    if not candidates:
        return None

    def score(text: str) -> tuple[int, int]:
        return (len(ARABIC_RE.findall(text)), -len(MOJIBAKE_RE.findall(text)))

    original_score = score(value)
    best = max(candidates, key=score)
    if score(best) > original_score:
        return best
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix mojibake Arabic text in SQLite.")
    parser.add_argument("--db", default="data.db", help="Path to SQLite database.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Without this flag, only reports what would change.",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.text_factory = str
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    changed_rows = 0
    changed_values = 0

    tables = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()

    for (table_name,) in tables:
        col_rows = cur.execute(f"PRAGMA table_info({table_name})").fetchall()
        text_cols = []
        for c in col_rows:
            ctype = (c["type"] or "").upper()
            if any(token in ctype for token in ("TEXT", "CHAR", "CLOB", "VARCHAR")):
                text_cols.append(c["name"])
        if not text_cols:
            continue

        select_cols = ", ".join([f'"{c}"' for c in text_cols])
        rows = cur.execute(f'SELECT rowid, {select_cols} FROM "{table_name}"').fetchall()
        for row in rows:
            updates = {}
            for col in text_cols:
                value = row[col]
                if not isinstance(value, str):
                    continue
                fixed = pick_best(value)
                if fixed is not None and fixed != value:
                    updates[col] = fixed

            if not updates:
                continue

            changed_rows += 1
            changed_values += len(updates)
            print(f'{table_name} rowid={row["rowid"]}: {", ".join(updates.keys())}')

            if args.apply:
                set_clause = ", ".join([f'"{col}" = ?' for col in updates])
                params = list(updates.values()) + [row["rowid"]]
                cur.execute(
                    f'UPDATE "{table_name}" SET {set_clause} WHERE rowid = ?',
                    params,
                )

    if args.apply:
        conn.commit()
    conn.close()

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] changed_rows={changed_rows}, changed_values={changed_values}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
