"""受控分类、复制并迁移文件型 SQLite；绝不原地修改源文件。"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.schema_management import (
    adopt_known_mixed_sqlite,
    classify_sqlite,
    migrate_managed_sqlite_copy,
)


def _print_classification(path: Path) -> None:
    result = classify_sqlite(path)
    print(f"path={path.resolve()}")
    print(f"kind={result.kind.value}")
    print(f"revision={result.revision or '-'}")
    print(f"reason={result.reason or '-'}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="分类或复制迁移 SQLite；源文件始终保持不变",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify_parser = subparsers.add_parser("classify", help="只读分类 SQLite")
    classify_parser.add_argument("source", type=Path)

    upgrade_parser = subparsers.add_parser(
        "upgrade-copy",
        help="复制并升级合法 Alembic 旧库",
    )
    upgrade_parser.add_argument("source", type=Path)
    upgrade_parser.add_argument("target", type=Path)

    adopt_parser = subparsers.add_parser(
        "adopt-copy",
        help="复制并采用与当前 ORM 完全一致的无版本库",
    )
    adopt_parser.add_argument("source", type=Path)
    adopt_parser.add_argument("target", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "classify":
            _print_classification(args.source)
            return 0
        if args.command == "upgrade-copy":
            result = migrate_managed_sqlite_copy(args.source, args.target)
        else:
            result = adopt_known_mixed_sqlite(args.source, args.target)
    except (FileExistsError, OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"target={args.target.resolve()}")
    print(f"kind={result.kind.value}")
    print(f"revision={result.revision or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
