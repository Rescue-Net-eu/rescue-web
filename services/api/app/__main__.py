"""Retention / privacy CLI (manual sections 16.2, 16.4, 17.4).

Run with ``python -m app <command>``. Builds its own async engine/session
from ``DATABASE_URL`` and prints a JSON summary. This is the "retention
cleanup job" container from the manual — suitable for cron or a k8s CronJob.

Commands:
  run                 run every retention sweep
  archive             archive closed missions only
  purge-locations     delete expired raw location samples
  anonymize           strip free text from old participation
  purge-audit         delete audit logs past the window
  erase-user --id ID  erase a single user's personal data
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from . import retention
from .config import get_settings
from .privacy import UserNotFound, erase_user


async def _run(command: str, user_id: str | None) -> dict:
    settings = get_settings()
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is not configured")

    engine = create_async_engine(settings.database_url)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            if command == "run":
                return await retention.run_all(session)
            if command == "archive":
                count = await retention.archive_closed_missions(session)
                await session.commit()
                return {"archived": count}
            if command == "purge-locations":
                count = await retention.purge_expired_locations(session)
                await session.commit()
                return {"locations_purged": count}
            if command == "anonymize":
                count = await retention.anonymize_old_participation(session)
                await session.commit()
                return {"participation_anonymized": count}
            if command == "purge-audit":
                count = await retention.purge_old_audit_logs(session)
                await session.commit()
                return {"audit_logs_purged": count}
            if command == "erase-user":
                if not user_id:
                    raise SystemExit("erase-user requires --id")
                return await erase_user(session, uuid.UUID(user_id))
            raise SystemExit(f"unknown command: {command}")
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app", description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "run",
            "archive",
            "purge-locations",
            "anonymize",
            "purge-audit",
            "erase-user",
        ],
    )
    parser.add_argument("--id", dest="user_id", help="user id for erase-user")
    args = parser.parse_args(argv)

    try:
        result = asyncio.run(_run(args.command, args.user_id))
    except UserNotFound as exc:
        print(json.dumps({"error": "user_not_found", "id": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
