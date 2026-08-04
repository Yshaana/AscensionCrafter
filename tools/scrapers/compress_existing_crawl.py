#!/usr/bin/env python3
"""
compress_existing_crawl.py — one-off: gzip .jsonl captures written before the
gzip switch (session 0b, 2026-08-04).

Converts data/source/crawl/**/*.jsonl -> *.jsonl.gz, verifying the round-trip
(line count and every line's bytes) before deleting the original. Exists so the
already-captured data doesn't have to be re-fetched from someone else's API.

Safe to re-run: files already having a .gz twin are skipped.

Usage: py tools/scrapers/compress_existing_crawl.py [--dry-run]
"""
import argparse
import gzip
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CRAWL_ROOT = REPO_ROOT / "data" / "source" / "crawl"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plain = sorted(CRAWL_ROOT.rglob("*.jsonl"))
    if not plain:
        print("nothing to compress")
        return 0

    before = after = 0
    converted = skipped = 0
    for src in plain:
        dst = src.with_suffix(".jsonl.gz")
        if dst.exists():
            print(f"  [skip] {dst.name} already exists")
            skipped += 1
            continue
        size = src.stat().st_size
        print(f"  {src.relative_to(REPO_ROOT)}  ({size/1e6:.1f} MB)")
        if args.dry_run:
            before += size
            continue

        with src.open("rb") as fin, gzip.open(dst, "wb") as fout:
            shutil.copyfileobj(fin, fout, length=1024 * 1024)

        # verify byte-exact round trip before removing the source
        with src.open("rb") as a, gzip.open(dst, "rb") as b:
            while True:
                ca, cb = a.read(1024 * 1024), b.read(1024 * 1024)
                if ca != cb:
                    print(f"    ✗ VERIFY FAILED — leaving {src.name} in place", file=sys.stderr)
                    dst.unlink(missing_ok=True)
                    return 1
                if not ca:
                    break

        before += size
        after += dst.stat().st_size
        src.unlink()
        converted += 1

    if args.dry_run:
        print(f"\ndry run: {len(plain)} files, {before/1e6:.1f} MB would be compressed")
        return 0
    print(f"\n{converted} converted, {skipped} skipped")
    if before:
        print(f"{before/1e6:.1f} MB -> {after/1e6:.1f} MB ({before/max(after,1):.1f}x smaller)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
