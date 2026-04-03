#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト用サンプルデータ自動生成スクリプト
"""

import argparse
import csv
import random
import sys
from datetime import date, timedelta

# ─────────────────────────────────────────
# 定数定義
# ─────────────────────────────────────────

SHIP_MODES = [
    "即日配送",
    "ファースト クラス",
    "ファーストクラス",
    "通常配送",
    "セカンド クラス",
    "セカンドクラス",
]

CUSTOMER_SEGMENTS = ["消費者", "大企業", "小規模事業者"]

# 姓リスト (50種)
LAST_NAMES = [
    "佐藤", "鈴木", "高橋", "田中", "渡辺",
    "伊藤", "山本", "中村", "小林", "加藤",
    "吉田", "山田", "佐々木", "山口", "松本",
    "井上", "木村", "林", "斎藤", "清水",
    "山崎", "阿部", "森", "池田", "橋本",
    "石川", "前田", "藤田", "後藤", "岡田",
    "長谷川", "村上", "近藤", "石井", "坂本",
    "遠藤", "青木", "藤井", "西村", "福田",
    "太田", "三浦", "岡本", "松田", "中野",
    "小川", "中島", "和田", "田村", "竹内",
]

# 名リスト (50種)
FIRST_NAMES = [
    "蓮", "陽翔", "湊", "蒼", "樹",
    "大翔", "悠真", "颯太", "海斗", "律",
    "さくら", "陽葵", "凛", "結菜", "葵",
    "芽依", "紬", "柚希", "ひなた", "美桜",
    "翔太", "健太", "拓哉", "雄大", "直樹",
    "誠", "亮", "浩二", "達也", "和也",
    "美咲", "彩香", "愛", "麻衣", "千尋",
    "優子", "恵", "裕子", "由美", "幸",
    "涼", "悠", "空", "碧", "晴",
    "朝陽", "光希", "優斗", "蒼汰", "晃",
]

# 都道府県 → (地域, 代表的な市区町村リスト)
PREF_DATA = {
    "北海道": ("北海道", ["札幌市中央区", "旭川市", "函館市", "小樽市", "釧路市", "帯広市", "北見市", "苫小牧市"]),
    "青森": ("東北地方", ["青森市", "弘前市", "八戸市", "十和田市"]),
    "岩手": ("東北地方", ["盛岡市", "一関市", "奥州市", "花巻市"]),
    "宮城": ("東北地方", ["仙台市青葉区", "石巻市", "気仙沼市", "大崎市"]),
    "秋田": ("東北地方", ["秋田市", "横手市", "大仙市", "能代市"]),
    "山形": ("東北地方", ["山形市", "鶴岡市", "酒田市", "新庄市"]),
    "福島": ("東北地方", ["福島市", "郡山市", "いわき市", "会津若松市"]),
    "茨城": ("関東地方", ["水戸市", "つくば市", "日立市", "土浦市"]),
    "栃木": ("関東地方", ["宇都宮市", "小山市", "栃木市", "足利市"]),
    "群馬": ("関東地方", ["前橋市", "高崎市", "桐生市", "太田市"]),
    "埼玉": ("関東地方", ["さいたま市大宮区", "川越市", "所沢市", "越谷市"]),
    "千葉": ("関東地方", ["千葉市中央区", "船橋市", "松戸市", "柏市"]),
    "東京": ("関東地方", ["新宿区", "渋谷区", "港区", "豊島区", "世田谷区", "品川区", "江東区"]),
    "神奈川": ("関東地方", ["横浜市中区", "川崎市川崎区", "相模原市中央区", "横須賀市"]),
    "新潟": ("中部地方", ["新潟市中央区", "長岡市", "上越市", "三条市"]),
    "富山": ("中部地方", ["富山市", "高岡市", "射水市", "魚津市"]),
    "石川": ("中部地方", ["金沢市", "白山市", "小松市", "輪島市"]),
    "福井": ("中部地方", ["福井市", "敦賀市", "越前市", "坂井市"]),
    "山梨": ("中部地方", ["甲府市", "富士吉田市", "甲州市", "笛吹市"]),
    "長野": ("中部地方", ["長野市", "松本市", "上田市", "飯田市"]),
    "岐阜": ("中部地方", ["岐阜市", "大垣市", "高山市", "各務原市"]),
    "静岡": ("中部地方", ["静岡市葵区", "浜松市中区", "沼津市", "富士市"]),
    "愛知": ("中部地方", ["名古屋市中区", "豊田市", "岡崎市", "一宮市"]),
    "三重": ("関西地方", ["津市", "四日市市", "鈴鹿市", "松阪市"]),
    "滋賀": ("関西地方", ["大津市", "草津市", "長浜市", "東近江市"]),
    "京都": ("関西地方", ["京都市中京区", "宇治市", "亀岡市", "長岡京市"]),
    "大阪": ("関西地方", ["大阪市北区", "堺市堺区", "東大阪市", "豊中市"]),
    "兵庫": ("関西地方", ["神戸市中央区", "姫路市", "尼崎市", "西宮市"]),
    "奈良": ("関西地方", ["奈良市", "橿原市", "大和郡山市", "天理市"]),
    "和歌山": ("関西地方", ["和歌山市", "田辺市", "橋本市", "有田市"]),
    "鳥取": ("中国地方", ["鳥取市", "米子市", "倉吉市", "境港市"]),
    "島根": ("中国地方", ["松江市", "出雲市", "浜田市", "益田市"]),
    "岡山": ("中国地方", ["岡山市北区", "倉敷市", "津山市", "総社市"]),
    "広島": ("中国地方", ["広島市中区", "福山市", "呉市", "東広島市"]),
    "山口": ("中国地方", ["下関市", "山口市", "宇部市", "周南市"]),
    "徳島": ("四国地方", ["徳島市", "阿南市", "鳴門市", "吉野川市"]),
    "香川": ("四国地方", ["高松市", "丸亀市", "坂出市", "善通寺市"]),
    "愛媛": ("四国地方", ["松山市", "今治市", "新居浜市", "西条市"]),
    "高知": ("四国地方", ["高知市", "南国市", "四万十市", "香南市"]),
    "福岡": ("九州", ["福岡市博多区", "北九州市小倉北区", "久留米市", "飯塚市"]),
    "佐賀": ("九州", ["佐賀市", "唐津市", "鳥栖市", "伊万里市"]),
    "長崎": ("九州", ["長崎市", "佐世保市", "諫早市", "大村市"]),
    "熊本": ("九州", ["熊本市中央区", "八代市", "天草市", "玉名市"]),
    "大分": ("九州", ["大分市", "別府市", "中津市", "日田市"]),
    "宮崎": ("九州", ["宮崎市", "都城市", "延岡市", "日南市"]),
    "鹿児島": ("九州", ["鹿児島市", "霧島市", "薩摩川内市", "鹿屋市"]),
    "沖縄": ("九州", ["那覇市", "沖縄市", "うるま市", "宜野湾市"]),
}

PREFECTURES = list(PREF_DATA.keys())


def make_customer_list(n=100):
    """重複なしの顧客リストを生成する"""
    customers = {}  # name -> {id, segment, city, pref, region}
    used_ids = set()
    names_pool = set()

    while len(customers) < n:
        last = random.choice(LAST_NAMES)
        first = random.choice(FIRST_NAMES)
        full_name = f"{last} {first}"
        if full_name in names_pool:
            continue
        names_pool.add(full_name)

        # 顧客ID
        cid_num = random.randint(30000, 39999)
        while cid_num in used_ids:
            cid_num = random.randint(30000, 39999)
        used_ids.add(cid_num)

        # イニシャル: 姓の先頭1文字 + 名の先頭1文字
        initial = last[0] + first[0]
        customer_id = f"{initial}-{cid_num}"

        # 顧客区分
        segment = random.choice(CUSTOMER_SEGMENTS)

        # 市区町村・都道府県・地域
        pref = random.choice(PREFECTURES)
        region, cities = PREF_DATA[pref]
        city = random.choice(cities)

        customers[full_name] = {
            "customer_id": customer_id,
            "segment": segment,
            "city": city,
            "prefecture": pref,
            "region": region,
        }

    return customers


def random_date_in_year(year: int) -> date:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate(output_file: str, num_rows: int, year: int, order_id_start: int):
    customers_map = make_customer_list(100)
    customer_names = list(customers_map.keys())

    order_id_current = order_id_start
    rows = []

    for row_id in range(1, num_rows + 1):
        # オーダーID
        offset = random.randint(1, 10)
        order_id_current += offset
        order_id = f"JP-{year}-{order_id_current:07d}"

        # 受注日 (年度内)
        order_date = random_date_in_year(year)

        # 出荷日 (受注日から0～30日後)
        ship_date = order_date + timedelta(days=random.randint(0, 30))

        # 出荷モード
        ship_mode = random.choice(SHIP_MODES)

        # 顧客
        name = random.choice(customer_names)
        cust = customers_map[name]

        rows.append([
            row_id,
            order_id,
            order_date.strftime("%Y/%m/%d"),
            ship_date.strftime("%Y/%m/%d"),
            ship_mode,
            cust["customer_id"],
            name,
            cust["segment"],
            cust["city"],
            cust["prefecture"],
            "日本",
            cust["region"],
        ])

    header = [
        "行ID", "オーダーID", "受注日", "出荷日", "出荷モード",
        "顧客 ID", "顧客名", "顧客区分", "市区町村", "都道府県", "国", "地域",
    ]

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"✅ {num_rows} 行のサンプルデータを '{output_file}' に出力しました。")


def main():
    current_year = date.today().year

    parser = argparse.ArgumentParser(
        description="テスト用サンプルCSVデータを生成します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python generate_sample_data.py
  python generate_sample_data.py -o output.csv -n 500 -y 2023 -s 1000
        """,
    )
    parser.add_argument(
        "-o", "--output",
        default="sample_data.csv",
        metavar="FILE",
        help="出力ファイル名 (デフォルト: sample_data.csv)",
    )
    parser.add_argument(
        "-n", "--num-rows",
        type=int,
        default=1000,
        metavar="N",
        help="生成する行数 (デフォルト: 1000)",
    )
    parser.add_argument(
        "-y", "--year",
        type=int,
        default=current_year,
        metavar="YEAR",
        help=f"年度 (デフォルト: {current_year})",
    )
    parser.add_argument(
        "-s", "--order-id-start",
        type=int,
        default=1000000,
        metavar="START",
        help="オーダーID開始番号 (デフォルト: 1000000)",
    )

    args = parser.parse_args()

    if args.num_rows < 1:
        print("エラー: 行数は1以上を指定してください。", file=sys.stderr)
        sys.exit(1)

    if args.year < 1900 or args.year > 9999:
        print("エラー: 年度は 1900〜9999 の範囲で指定してください。", file=sys.stderr)
        sys.exit(1)

    generate(args.output, args.num_rows, args.year, args.order_id_start)


if __name__ == "__main__":
    main()
    
