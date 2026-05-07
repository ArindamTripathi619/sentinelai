#!/usr/bin/env python3
"""Migrate SentinelAI data from SQLite to PostgreSQL.

This script copies the current application tables in dependency order and
verifies row counts after the transfer.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, Type

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import models  # noqa: E402
from database import build_engine, is_sqlite_url  # noqa: E402


MODEL_ORDER: list[Type[models.Base]] = [
    models.User,
    models.Event,
    models.Alert,
    models.OtpSession,
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL.")
    parser.add_argument(
        "--source-url",
        default=os.getenv("SOURCE_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")),
        help="Source database URL. Defaults to SOURCE_DATABASE_URL or DATABASE_URL.",
    )
    parser.add_argument(
        "--target-url",
        default=os.getenv("TARGET_DATABASE_URL"),
        required=os.getenv("TARGET_DATABASE_URL") is None,
        help="Target PostgreSQL URL. Defaults to TARGET_DATABASE_URL.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate connectivity and counts without copying data.",
    )
    parser.add_argument(
        "--truncate-target",
        action="store_true",
        help="Delete target rows before importing.",
    )
    return parser.parse_args()


def count_rows(session, model) -> int:
    return session.query(model).count()


def serialize_row(instance, model):
    return {
        column.name: getattr(instance, column.name)
        for column in model.__table__.columns
    }


def clear_target(session, model_order: Iterable[Type[models.Base]]) -> None:
    for model in reversed(list(model_order)):
        session.query(model).delete(synchronize_session=False)
    session.commit()


def copy_model_rows(source_session, target_session, model) -> int:
    rows = source_session.query(model).all()
    if not rows:
        return 0

    copied = [model(**serialize_row(row, model)) for row in rows]
    target_session.add_all(copied)
    target_session.commit()
    return len(copied)


def main() -> int:
    args = parse_args()

    if not is_sqlite_url(args.source_url):
        print(f"[warn] Source URL is not SQLite: {args.source_url}")

    source_engine = build_engine(args.source_url)
    target_engine = build_engine(args.target_url)

    models.Base.metadata.create_all(bind=target_engine)

    SourceSession = sessionmaker(autocommit=False, autoflush=False, bind=source_engine)
    TargetSession = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)

    source_session = SourceSession()
    target_session = TargetSession()

    try:
        print(f"[info] Source: {args.source_url}")
        print(f"[info] Target: {args.target_url}")

        source_counts = {model.__tablename__: count_rows(source_session, model) for model in MODEL_ORDER}
        print(f"[info] Source counts: {source_counts}")

        if args.dry_run:
            print("[info] Dry run complete. No data copied.")
            return 0

        if args.truncate_target:
            print("[info] Truncating target tables before import...")
            clear_target(target_session, MODEL_ORDER)

        copied_counts = {}
        for model in MODEL_ORDER:
            table_name = model.__tablename__
            copied_counts[table_name] = copy_model_rows(source_session, target_session, model)
            print(f"[info] Copied {copied_counts[table_name]} rows into {table_name}")

        target_counts = {model.__tablename__: count_rows(target_session, model) for model in MODEL_ORDER}
        print(f"[info] Target counts: {target_counts}")

        mismatches = {
            table: (source_counts[table], target_counts[table])
            for table in source_counts
            if source_counts[table] != target_counts[table]
        }
        if mismatches:
            raise RuntimeError(f"Row-count mismatch after migration: {mismatches}")

        print("[success] Migration completed successfully.")
        return 0
    finally:
        source_session.close()
        target_session.close()


if __name__ == "__main__":
    raise SystemExit(main())