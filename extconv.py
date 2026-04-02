#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extconv.py - .log ファイルの拡張子にポストフィックスを一括付与するCLIツール

使い方:
  python extconv.py <対象ディレクトリ> <ポストフィックス>

例:
  python extconv.py C:\\logs 2026-02-09
  python extconv.py C:\\logs 2026-02-09 --dry-run

変換例:
  foobar.log  →  foobar.log.2026-02-09
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

TARGET_EXT = ".log"
LOG_FILE = "extconv.log"


def setup_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("extconv")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ファイル出力
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # コンソール出力
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=".log ファイルの拡張子にポストフィックスを一括付与します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("directory", type=Path, help="対象ディレクトリのパス")
    parser.add_argument("postfix", help="拡張子に付与するポストフィックス文字列（例: 2026-02-09）")
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="実際には変換せず、対象ファイルの一覧を表示するだけ",
    )
    return parser.parse_args()


def collect_log_files(directory: Path) -> list[Path]:
    """対象ディレクトリを再帰的に探索し、.log ファイルを収集する"""
    return sorted(directory.rglob(f"*{TARGET_EXT}"))


def rename_files(
    files: list[Path],
    postfix: str,
    dry_run: bool,
    logger: logging.Logger,
) -> tuple[int, int]:
    success, failed = 0, 0

    for src in files:
        dst = src.with_name(src.name + "." + postfix)

        if dst.exists():
            logger.warning("スキップ（同名ファイルが既に存在）: %s", src)
            failed += 1
            continue

        if dry_run:
            logger.info("[DRY-RUN] %s  →  %s", src, dst.name)
        else:
            try:
                src.rename(dst)
                logger.info("変換完了: %s  →  %s", src, dst.name)
                success += 1
            except OSError as e:
                logger.error("変換失敗: %s  エラー: %s", src, e)
                failed += 1

    return success, failed


def main() -> None:
    args = parse_args()

    # ログファイルはスクリプトと同じディレクトリに出力
    log_path = Path(__file__).parent / LOG_FILE
    logger = setup_logger(log_path)

    logger.info("=" * 60)
    logger.info("extconv 開始")
    logger.info("対象ディレクトリ : %s", args.directory.resolve())
    logger.info("ポストフィックス : %s", args.postfix)
    logger.info("再帰処理         : あり")
    if args.dry_run:
        logger.info("モード           : ドライラン（実際には変換しません）")
    logger.info("=" * 60)

    # ディレクトリ存在確認
    if not args.directory.is_dir():
        logger.error("ディレクトリが見つかりません: %s", args.directory)
        sys.exit(1)

    files = collect_log_files(args.directory)

    if not files:
        logger.info("対象ファイルが見つかりませんでした（拡張子: %s）", TARGET_EXT)
        sys.exit(0)

    logger.info("対象ファイル数: %d 件", len(files))

    success, failed = rename_files(files, args.postfix, args.dry_run, logger)

    logger.info("-" * 60)
    if args.dry_run:
        logger.info("ドライラン完了: %d 件が変換対象です。", len(files))
    else:
        logger.info("処理完了: 成功 %d 件 / スキップ・失敗 %d 件", success, failed)
    logger.info("ログ出力先: %s", log_path.resolve())


if __name__ == "__main__":
    main()
