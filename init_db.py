import sqlite3


# =========================
# データベース接続
# =========================

conn = sqlite3.connect("database.db")


# =========================
# 武器テーブル
# =========================

conn.execute("""
    CREATE TABLE IF NOT EXISTS weapons (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE

    )
""")


# =========================
# クエストテーブル
# =========================

conn.execute("""
    CREATE TABLE IF NOT EXISTS quests (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE

    )
""")


# =========================
# Platformテーブル
# =========================

conn.execute("""
    CREATE TABLE IF NOT EXISTS platforms (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL UNIQUE

    )
""")


# =========================
# 初期武器
# =========================

weapons = [

    "大剣",
    "太刀",
    "片手剣",
    "双剣",
    "ハンマー",
    "狩猟笛",
    "ランス",
    "ガンランス",
    "スラッシュアックス",
    "チャージアックス",
    "操虫棍",
    "ライトボウガン",
    "ヘビィボウガン",
    "弓"

]


for weapon in weapons:

    conn.execute("""
        INSERT OR IGNORE INTO weapons
        (
            name
        )

        VALUES (?)

    """, (
        weapon,
    ))


# =========================
# 初期Platform
# =========================

platforms = [

    "PC",
    "PS5",
    "Xbox"

]


for platform in platforms:

    conn.execute("""
        INSERT OR IGNORE INTO platforms
        (
            name
        )

        VALUES (?)

    """, (
        platform,
    ))


# =========================
# 保存
# =========================

conn.commit()

conn.close()


print("データベースの初期設定が完了しました。")