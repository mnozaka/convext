#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
dirconv.py - 特定パターンのフォルダ名から末尾のバージョン番号を除去するCLIツール

対象パターン:
  <アルファベット>_<数字>.<数字>.<数字>.<数字>.<数字>

変換例:
  foobar_123.4.5.6.7  →  foobar_123.4.5.6

使い方:
  python dirconv.py <対象ディレクトリ>
  python dirconv.py <対象ディレクトリ> --dry-run
"""

import argparse
import logging
import re
import sys
from pathlib import Path

LOG_FILE = "dirconv.log"

# 対象パターン: アルファベット列_数字列.数字列.数字列.数字列.数字列
PATTERN = re.compile(r'^([A-Za-z]+_\d+\.\d+\.\d+\.\d+)\.\d+$')


def setup_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("dirconv")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="特定パターンのフォルダ名から末尾のバージョン番号を除去します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("directory", type=Path, help="探索を開始するルートディレクトリ")
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="実際には変換せず、変換前後のフォルダ名を表示するだけ",
    )
    return parser.parse_args()


def collect_target_dirs(root: Path) -> list[Path]:
    """
    対象パターンに一致するディレクトリを深い階層から順に収集する。
    深い階層から処理することで、親フォルダのリネームによるパス不整合を防ぐ。
    """
    targets = []
    for path in root.rglob("*"):
        if path.is_dir() and PATTERN.match(path.name):
            targets.append(path)
    # 深い階層（パス長が長い）順にソート
    targets.sort(key=lambda p: len(p.parts), reverse=True)
    return targets


def rename_dirs(
    targets: list[Path],
    dry_run: bool,
    logger: logging.Logger,
) -> tuple[int, int]:
    success, failed = 0, 0

    for src in targets:
        m = PATTERN.match(src.name)
        if not m:
            continue

        new_name = m.group(1)
        dst = src.parent / new_name

        if dst.exists():
            logger.warning("スキップ（同名フォルダが既に存在）: %s", src)
            failed += 1
            continue

        if dry_run:
            logger.info("[DRY-RUN] %s  →  %s", src, new_name)
        else:
            try:
                src.rename(dst)
                logger.info("変換完了: %s  →  %s", src, new_name)
                success += 1
            except OSError as e:
                logger.error("変換失敗: %s  エラー: %s", src, e)
                failed += 1

    return success, failed


def main() -> None:
    args = parse_args()

    log_path = Path(__file__).parent / LOG_FILE
    logger = setup_logger(log_path)

    logger.info("=" * 60)
    logger.info("dirconv 開始")
    logger.info("対象ディレクトリ : %s", args.directory.resolve())
    if args.dry_run:
        logger.info("モード           : ドライラン（実際には変換しません）")
    logger.info("=" * 60)

    if not args.directory.is_dir():
        logger.error("ディレクトリが見つかりません: %s", args.directory)
        sys.exit(1)

    targets = collect_target_dirs(args.directory)

    if not targets:
        logger.info("対象パターンに一致するフォルダが見つかりませんでした。")
        sys.exit(0)

    logger.info("対象フォルダ数: %d 件", len(targets))

    success, failed = rename_dirs(targets, args.dry_run, logger)

    logger.info("-" * 60)
    if args.dry_run:
        logger.info("ドライラン完了: %d 件が変換対象です。", len(targets))
    else:
        logger.info("処理完了: 成功 %d 件 / スキップ・失敗 %d 件", success, failed)
    logger.info("ログ出力先: %s", log_path.resolve())


if __name__ == "__main__":
    main()
    
