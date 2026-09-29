#!/usr/bin/env python3
"""Install this local skill without replacing existing content or accessing the network."""
import argparse
import os
from pathlib import Path
import shutil
import sys

NAME = 'college-innovation-project-skill'


def install(source, destination, dry_run=False):
    source = Path(source).resolve()
    destination = Path(destination).expanduser().resolve()
    target = destination / NAME
    if not (source / 'SKILL.md').is_file():
        raise ValueError('Source skill is missing SKILL.md')
    if target == source or source in target.parents:
        raise ValueError('Destination cannot be inside the source skill')
    if target.exists() or target.is_symlink():
        raise FileExistsError(f'Existing skill preserved: {target}')
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
        # copytree refuses existing targets; do not use dirs_exist_ok.
        shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.DS_Store'))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default_home = Path(os.environ.get('CODEX_HOME') or (Path.home() / '.codex'))
    parser.add_argument('--destination', type=Path, default=default_home / 'skills')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        target = install(Path(__file__).resolve().parents[1], args.destination, args.dry_run)
        print(('Would install: ' if args.dry_run else 'Installed: ') + str(target))
    except (OSError, ValueError) as exc:
        print(f'Installation stopped: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
