#!/usr/bin/env python3
"""Opt-in skill copies for native Codex repo discovery. Never overwrite differences."""
import argparse
import sys
from pathlib import Path
from skill_catalog import load_skill


def install(target: Path, skills: list[str], dry_run: bool = False) -> list[str]:
    target = target.resolve()
    if not (target / ".git").exists():
        raise ValueError("target must be the root of an existing git repository")
    # Preflight *all* requested skills before writing any, to avoid partial installs.
    planned = []
    for name in skills:
        data = load_skill(name)
        path = target / ".agents" / "skills" / name / "SKILL.md"
        if any(component.is_symlink() for component in (target / ".agents", target / ".agents" / "skills", path.parent, path)):
            raise ValueError("refusing symlink destination: " + str(path))
        if path.exists() and path.read_text(encoding="utf-8") != data:
            raise ValueError("existing different skill will not be overwritten: " + str(path))
        planned.append((data, path))
    output = []
    for data, path in planned:
        if path.parent.is_symlink() or path.is_symlink():
            raise ValueError("refusing symlink destination: " + str(path))
        if path.exists():
            if path.read_text(encoding="utf-8") != data:
                raise ValueError("existing different skill will not be overwritten: " + str(path))
            output.append("unchanged: " + str(path))
            continue
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive create: never replace a skill created concurrently.
            with path.open("x", encoding="utf-8") as stream:
                stream.write(data)
        output.append(("would install: " if dry_run else "installed: ") + str(path))
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--skill", action="append", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        for row in install(args.target, args.skill, args.dry_run):
            print(row)
    except (OSError, ValueError) as exc:
        print("skill install refused: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
