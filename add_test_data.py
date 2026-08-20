import sqlite3


conn = sqlite3.connect("database.db")


records = [
    ("Player A", "レ・ダウ", "大剣", 151.42, "PC", "https://youtube.com/"),
    ("Player B", "レ・ダウ", "大剣", 155.18, "PC", "https://youtube.com/"),
    ("Player C", "レ・ダウ", "大剣", 159.51, "PC", "https://youtube.com/")
]


conn.executemany("""
INSERT INTO records
(player, quest, weapon, time, platform, video_url)
VALUES (?, ?, ?, ?, ?, ?)
""", records)


conn.commit()

conn.close()


print("テストデータを登録しました！")