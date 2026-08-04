#!/usr/bin/env python3
"""
archive_crawl.py — roll old tier-2 crawl bulk into monthly tarballs.

Tier 2 (abilities / healing / avoidance / damage_taken) is gitignored and lives
only on this machine. It is re-fetchable from ascensionlogs.gg by report id, but
re-fetching is slow and impolite, so we keep it — just not scattered across one
directory per day forever.

This consolidates tier-2 files older than --older-than days into
`data/archive/crawl_<YYYY-MM>.tar` (one per month, already-gzipped members so the
tar itself is not re-compressed), then deletes the originals.

**Nothing irreplaceable is touched.** Tier-1 files (characters, leaderboards,
phases, reports), `manifest.json`, and `scan_log.json` are never archived or
removed — they are committed to git and stay in place.

Archiving is DEFERRED, not destructive: the tarball keeps every byte, and each
day's committed manifest.json still lists record counts and sha256 for the
archived files. Verify an archive at any time with --verify.

Usage:
    py tools/scrapers/archive_crawl.py --older-than 30        (default 30)
    py tools/scrapers/archive_crawl.py --older-than 30 --dry-run
    py tools/scrapers/archive_crawl.py --verify
"""
import argparse
import hashlib
import json
import sys
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CRAWL_ROOT = REPO_ROOT / "data" / "source" / "crawl"
ARCHIVE_ROOT = REPO_ROOT / "data" / "archive"

TIER2_PREFIXES = ("abilities", "healing", "avoidance", "damage_taken")


def tier2_files(date_dir):
    return [p for p in sorted(date_dir.glob("*.jsonl.gz"))
            if p.name.split(".")[0] in TIER2_PREFIXES]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def do_archive(older_than, dry_run):
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=older_than)
    moved = freed = 0
    by_month = {}

    for date_dir in sorted(CRAWL_ROOT.iterdir()):
        if not date_dir.is_dir():
            continue
        try:
            d = datetime.strptime(date_dir.name, "%Y-%m-%d").date()
        except ValueError:
            continue  # baseline_phase1/ and friends — never archived
        if d >= cutoff:
            continue
        files = tier2_files(date_dir)
        if files:
            by_month.setdefault(d.strftime("%Y-%m"), []).append((date_dir, files))

    if not by_month:
        print(f"nothing older than {older_than} days to archive")
        return 0

    for month, entries in sorted(by_month.items()):
        tar_path = ARCHIVE_ROOT / f"crawl_{month}.tar"
        total = sum(len(f) for _, f in entries)
        print(f"\n{month}: {total} tier-2 files from {len(entries)} day(s) -> {tar_path.name}")
        if dry_run:
            for date_dir, files in entries:
                for p in files:
                    print(f"   would archive {date_dir.name}/{p.name} "
                          f"({p.stat().st_size/1e6:.1f} MB)")
                    freed += p.stat().st_size
            continue

        ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
        mode = "a" if tar_path.exists() else "w"
        staged = {}  # arcname -> (source path, sha256 before archiving)

        # Phase 1: write every member, then CLOSE the tar. Verification cannot read
        # from a tar that is still open — the trailing blocks aren't flushed yet.
        with tarfile.open(tar_path, mode) as tar:
            for date_dir, files in entries:
                for p in files:
                    arcname = f"{date_dir.name}/{p.name}"
                    staged[arcname] = (p, sha256(p))
                    tar.add(p, arcname=arcname)

        # Phase 2: re-open and verify every member byte-for-byte.
        with tarfile.open(tar_path) as check:
            for arcname, (p, digest) in staged.items():
                member = check.extractfile(arcname)
                if member is None:
                    print(f"   x {arcname} missing from archive — originals kept",
                          file=sys.stderr)
                    return 1
                h = hashlib.sha256()
                for chunk in iter(lambda: member.read(1024 * 1024), b""):
                    h.update(chunk)
                if h.hexdigest() != digest:
                    print(f"   x VERIFY FAILED for {arcname} — originals kept",
                          file=sys.stderr)
                    return 1

        # Phase 3: only now, with every byte confirmed inside the archive, delete.
        for arcname, (p, _) in staged.items():
            freed += p.stat().st_size
            p.unlink()
            moved += 1
            print(f"   archived {arcname}")

    verb = "would free" if dry_run else "freed"
    print(f"\n{moved} file(s) archived, {verb} {freed/1e6:.1f} MB from the working tree")
    print("Tier-1 files, manifests and scan_log untouched.")
    return 0


def do_verify():
    if not ARCHIVE_ROOT.exists():
        print("no archive directory yet")
        return 0
    ok = True
    for tar_path in sorted(ARCHIVE_ROOT.glob("crawl_*.tar")):
        with tarfile.open(tar_path) as tar:
            members = tar.getnames()
        print(f"{tar_path.name}: {len(members)} members, "
              f"{tar_path.stat().st_size/1e6:.1f} MB")
        # cross-check against the committed manifests
        for name in members:
            day, fname = name.split("/", 1)
            man = CRAWL_ROOT / day / "manifest.json"
            if not man.exists():
                print(f"   ! {name}: no manifest.json for that day")
                ok = False
                continue
            entry = next((f for f in json.loads(man.read_text())["files"]
                          if f["file"] == fname), None)
            if entry is None:
                print(f"   ! {name}: not listed in that day's manifest")
                ok = False
    print("OK" if ok else "issues found (above)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--older-than", type=int, default=30,
                    help="archive tier-2 files older than N days (default 30)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="list archives and cross-check against committed manifests")
    args = ap.parse_args()
    return do_verify() if args.verify else do_archive(args.older_than, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
