#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loganalyze.py - JSON ログを解析し、タイムスタンプのビン集計を CSV で出力するツール

前提:
  各行が JSON オブジェクトの NDJSON (newline-delimited JSON) 形式を想定。
  - 'ts' : ISO 形式のタイムスタンプ (例: "2026-02-09T10:03:21+09:00")
  - 'k'  : ログ種別文字列 (例: "INFO", "ERROR", "WARN")

使い方:
  python loganalyze.py <ログファイル>
  python loganalyze.py <ログファイル> --interval 5
  python loganalyze.py <ログファイル> --interval 30 --output result.csv

出力 CSV 例 (interval=10):
  ts_bin,total,k_ERROR,k_INFO,k_WARN
  2026-02-09T10:00,15,3,10,2
  2026-02-09T10:10,8,1,7,0
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="JSON ログをタイムスタンプでビン化し CSV に集計します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("logfile", type=Path, help="解析対象の JSON ログファイル")
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=10,
        metavar="MINUTES",
        help="ビンの間隔（分）。デフォルト: 10",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        metavar="FILE",
        help="出力 CSV ファイル名。省略時は <ログファイル名>.csv",
    )
    return parser.parse_args()


def bin_timestamp(ts: datetime, interval_minutes: int) -> datetime:
    """タイムスタンプを interval_minutes 間隔のビンに丸める"""
    minute = (ts.minute // interval_minutes) * interval_minutes
    return ts.replace(minute=minute, second=0, microsecond=0)


def parse_log(logfile: Path, interval_minutes: int):
    """
    ログファイルを読み込み、ビンごと・k ごとのカウントを返す。

    Returns:
        bin_counts : { bin_dt: { k: count } }
        all_kinds  : set of all 'k' values seen
        errors     : list of (line_no, reason) for skipped lines
    """
    bin_counts: dict[datetime, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    all_kinds: set[str] = set()
    errors: list[tuple[int, str]] = []

    with logfile.open(encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append((lineno, f"JSON パースエラー: {e}"))
                continue

            ts_raw = obj.get("ts")
            k_val = obj.get("k")

            if ts_raw is None:
                errors.append((lineno, "キー 'ts' が存在しません"))
                continue
            if k_val is None:
                errors.append((lineno, "キー 'k' が存在しません"))
                continue

            try:
                ts = datetime.fromisoformat(str(ts_raw))
            except ValueError as e:
                errors.append((lineno, f"タイムスタンプのパース失敗: {e}"))
                continue

            bin_dt = bin_timestamp(ts, interval_minutes)
            bin_counts[bin_dt][str(k_val)] += 1
            all_kinds.add(str(k_val))

    return bin_counts, all_kinds, errors


def write_csv(
    output_path: Path,
    bin_counts: dict,
    all_kinds: set,
    interval_minutes: int,
) -> None:
    sorted_kinds = sorted(all_kinds)
    fieldnames = ["ts_bin", "total"] + [f"k_{k}" for k in sorted_kinds]

    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for bin_dt in sorted(bin_counts.keys()):
            counts = bin_counts[bin_dt]
            total = sum(counts.values())
            row = {"ts_bin": bin_dt.strftime("%Y-%m-%dT%H:%M"), "total": total}
            for k in sorted_kinds:
                row[f"k_{k}"] = counts.get(k, 0)
            writer.writerow(row)


def main() -> None:
    args = parse_args()

    if not args.logfile.is_file():
        print(f"エラー: ファイルが見つかりません: {args.logfile}", file=sys.stderr)
        sys.exit(1)

    if args.interval <= 0:
        print("エラー: --interval には 1 以上の整数を指定してください。", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or args.logfile.with_suffix(".csv")

    print(f"解析対象   : {args.logfile.resolve()}")
    print(f"ビン間隔   : {args.interval} 分")
    print(f"出力先     : {output_path.resolve()}")
    print("-" * 50)

    bin_counts, all_kinds, errors = parse_log(args.logfile, args.interval)

    # スキップ行の報告
    if errors:
        print(f"警告: {len(errors)} 行をスキップしました。")
        for lineno, reason in errors:
            print(f"  行 {lineno:>6}: {reason}")
        print()

    total_records = sum(sum(c.values()) for c in bin_counts.values())
    print(f"有効レコード数 : {total_records} 件")
    print(f"ビン数         : {len(bin_counts)} 個")
    print(f"ログ種別 (k)   : {', '.join(sorted(all_kinds))}")
    print()

    if not bin_counts:
        print("集計対象のデータがありませんでした。")
        sys.exit(0)

    write_csv(output_path, bin_counts, all_kinds, args.interval)
    print(f"CSV を出力しました: {output_path.resolve()}")


if __name__ == "__main__":
    main()
    
