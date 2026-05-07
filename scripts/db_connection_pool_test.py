#!/usr/bin/env python3
"""Quick DB connection-pooling load test for SQLAlchemy engines.

Usage:
  ./venv/bin/python scripts/db_connection_pool_test.py --workers 50 --tasks 200

Defaults: reads DATABASE_URL from environment or uses sqlite:///./backend/sentinel.db
"""
import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, text


def run_task(engine, query):
    try:
        with engine.connect() as conn:
            r = conn.execute(text(query)).fetchone()
        return True, r
    except Exception as e:
        return False, str(e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--database-url", default=os.getenv("DATABASE_URL", "sqlite:///./backend/sentinel.db"))
    p.add_argument("--workers", type=int, default=20)
    p.add_argument("--tasks", type=int, default=100)
    p.add_argument("--pool-size", type=int, default=5)
    p.add_argument("--max-overflow", type=int, default=10)
    p.add_argument("--query", default="SELECT 1")
    args = p.parse_args()

    print(f"Using DATABASE_URL={args.database_url}")
    engine = create_engine(
        args.database_url,
        pool_size=args.pool_size,
        max_overflow=args.max_overflow,
        pool_timeout=30,
    )

    start = time.time()
    successes = 0
    failures = 0
    durations = []

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(run_task, engine, args.query) for _ in range(args.tasks)]
        for fut in as_completed(futures):
            ok, info = fut.result()
            if ok:
                successes += 1
            else:
                failures += 1
                print(f"Task error: {info}")

    total = time.time() - start
    print("\n-- Summary --")
    print(f"tasks: {args.tasks}")
    print(f"workers: {args.workers}")
    print(f"pool_size: {args.pool_size}, max_overflow: {args.max_overflow}")
    print(f"successes: {successes}")
    print(f"failures: {failures}")
    print(f"total_time_s: {total:.2f}")


if __name__ == '__main__':
    main()
