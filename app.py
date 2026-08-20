import sqlite3
import os
import shutil
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file
)

from dotenv import load_dotenv


# ==================================================
# ENV
# ==================================================

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

# .env がなくてもローカルで動くようにする
if not SECRET_KEY:
    SECRET_KEY = "bhtawiki-secret-key"


# ==================================================
# APP
# ==================================================

app = Flask(__name__)

app.secret_key = SECRET_KEY

DATABASE = "database.db"


# ==================================================
# DATABASE
# ==================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ==================================================
# TIME
# ==================================================

def time_to_seconds(time_string):

    try:

        if not time_string:
            return None

        parts = time_string.strip().split(":")

        if len(parts) != 2:
            return None

        minutes = int(parts[0])
        seconds = float(parts[1])

        if minutes < 0:
            return None

        if seconds < 0 or seconds >= 60:
            return None

        return minutes * 60 + seconds

    except:

        return None


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session["admin_logged_in"] = True

            return redirect(
                url_for("admin")
            )

        return render_template(
            "login.html",
            error="ユーザー名またはパスワードが違います。"
        )

    return render_template("login.html")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect(
        url_for("index")
    )


# ==================================================
# RANKING
# ==================================================

@app.route("/")
def index():

    quest = request.args.get(
        "quest",
        ""
    )

    weapon = request.args.get(
        "weapon",
        ""
    )

    platform = request.args.get(
        "platform",
        ""
    )

    conn = get_db()

    quests = conn.execute("""
        SELECT *
        FROM quests
        ORDER BY id
    """).fetchall()

    weapons = conn.execute("""
        SELECT *
        FROM weapons
        ORDER BY id
    """).fetchall()

    platforms = conn.execute("""
        SELECT *
        FROM platforms
        ORDER BY id
    """).fetchall()

    world_record = conn.execute("""
        SELECT *
        FROM records
        ORDER BY time ASC
        LIMIT 1
    """).fetchone()

    query = """
        SELECT *
        FROM records
        WHERE 1 = 1
    """

    params = []

    if quest:

        query += """
            AND quest = ?
        """

        params.append(quest)

    if weapon:

        query += """
            AND weapon = ?
        """

        params.append(weapon)

    if platform:

        query += """
            AND platform = ?
        """

        params.append(platform)

    query += """
        ORDER BY time ASC
    """

    records = conn.execute(
        query,
        params
    ).fetchall()

    best_record = None

    if records:

        best_record = records[0]

    conn.close()

    ranked_records = []

    for rank, record in enumerate(
        records,
        start=1
    ):

        record_dict = dict(record)

        record_dict["rank"] = rank

        ranked_records.append(
            record_dict
        )

    return render_template(
        "index.html",

        records=ranked_records,

        quests=quests,

        weapons=weapons,

        platforms=platforms,

        selected_quest=quest,

        selected_weapon=weapon,

        selected_platform=platform,

        world_record=world_record,

        best_record=best_record
    )


# ==================================================
# RECORD DETAIL
# ==================================================

@app.route("/record/<int:record_id>")
def record_detail(record_id):

    conn = get_db()

    record = conn.execute("""
        SELECT *
        FROM records
        WHERE id = ?
    """, (
        record_id,
    )).fetchone()

    if record is None:

        conn.close()

        return "記録が見つかりません。", 404

    better_records = conn.execute("""
        SELECT COUNT(*) AS count
        FROM records
        WHERE
            quest = ?
            AND time < ?
    """, (
        record["quest"],
        record["time"]
    )).fetchone()

    rank = better_records["count"] + 1

    quest_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM records
        WHERE quest = ?
    """, (
        record["quest"],
    )).fetchone()["count"]

    quest_world_record = conn.execute("""
        SELECT *
        FROM records
        WHERE quest = ?
        ORDER BY time ASC
        LIMIT 1
    """, (
        record["quest"],
    )).fetchone()

    conn.close()

    return render_template(
        "record.html",

        record=record,

        rank=rank,

        quest_count=quest_count,

        quest_world_record=quest_world_record
    )


# ==================================================
# PLAYER PAGE
# ==================================================

@app.route("/player/<path:player_name>")
def player_page(player_name):

    conn = get_db()

    records = conn.execute("""
        SELECT *
        FROM records
        WHERE player = ?
        ORDER BY quest ASC, time ASC
    """, (
        player_name,
    )).fetchall()

    conn.close()

    if not records:

        return "プレイヤーが見つかりません。", 404

    return render_template(
        "player.html",

        player=player_name,

        records=records
    )


# ==================================================
# QUEST LIST / SEARCH
# ==================================================

@app.route("/quests")
def quests():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db()

    if search:

        quest_list = conn.execute("""
            SELECT *
            FROM quests
            WHERE name LIKE ?
            ORDER BY id
        """, (
            "%" + search + "%",
        )).fetchall()

    else:

        quest_list = conn.execute("""
            SELECT *
            FROM quests
            ORDER BY id
        """).fetchall()

    conn.close()

    return render_template(
        "quests.html",

        quests=quest_list,

        search=search
    )


# ==================================================
# QUEST PAGE
# ==================================================

@app.route("/quest/<path:quest_name>")
def quest_page(quest_name):

    conn = get_db()

    records = conn.execute("""
        SELECT *
        FROM records
        WHERE quest = ?
        ORDER BY weapon ASC, time ASC
    """, (
        quest_name,
    )).fetchall()

    world_record = conn.execute("""
        SELECT *
        FROM records
        WHERE quest = ?
        ORDER BY time ASC
        LIMIT 1
    """, (
        quest_name,
    )).fetchone()

    conn.close()

    weapon_groups = {}

    for record in records:

        weapon_name = record["weapon"]

        if weapon_name not in weapon_groups:

            weapon_groups[weapon_name] = []

        weapon_groups[weapon_name].append(
            record
        )

    return render_template(
        "quest.html",

        quest_name=quest_name,

        weapon_groups=weapon_groups,

        world_record=world_record
    )


# ==================================================
# RULES
# ==================================================

@app.route("/rules")
def rules():

    return render_template(
        "rules.html"
    )


# ==================================================
# ADMIN
# ==================================================

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("login")
        )

    conn = get_db()

    if request.method == "POST":

        player = request.form.get(
            "player",
            ""
        ).strip()

        quest = request.form.get(
            "quest",
            ""
        ).strip()

        weapon = request.form.get(
            "weapon",
            ""
        ).strip()

        time_string = request.form.get(
            "time",
            ""
        ).strip()

        platform = request.form.get(
            "platform",
            ""
        ).strip()

        # YouTube URLは任意
        video_url = request.form.get(
            "video_url",
            ""
        ).strip()

        time_seconds = time_to_seconds(
            time_string
        )

        # 必須項目だけチェック
        if (
            not player
            or not quest
            or not weapon
            or not platform
            or time_seconds is None
        ):

            conn.close()

            return redirect(
                url_for("admin")
            )

        duplicate = conn.execute("""
            SELECT id
            FROM records
            WHERE
                player = ?
                AND quest = ?
                AND weapon = ?
                AND time = ?
                AND platform = ?
            LIMIT 1
        """, (
            player,
            quest,
            weapon,
            time_seconds,
            platform
        )).fetchone()

        if duplicate:

            conn.close()

            return redirect(
                url_for("admin")
            )

        conn.execute("""
            INSERT INTO records
            (
                player,
                quest,
                weapon,
                time,
                platform,
                video_url
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            player,
            quest,
            weapon,
            time_seconds,
            platform,
            video_url
        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for("admin")
        )

    quests = conn.execute("""
        SELECT *
        FROM quests
        ORDER BY id
    """).fetchall()

    weapons = conn.execute("""
        SELECT *
        FROM weapons
        ORDER BY id
    """).fetchall()

    platforms = conn.execute("""
        SELECT *
        FROM platforms
        ORDER BY id
    """).fetchall()

    records = conn.execute("""
        SELECT *
        FROM records
        ORDER BY time ASC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",

        quests=quests,

        weapons=weapons,

        platforms=platforms,

        records=records
    )


# ==================================================
# ADD QUEST
# ==================================================

@app.route(
    "/admin/quest/add",
    methods=["POST"]
)
def add_quest():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("login")
        )

    quest_name = request.form.get(
        "quest_name",
        ""
    ).strip()

    if quest_name:

        conn = get_db()

        conn.execute("""
            INSERT OR IGNORE INTO quests
            (name)
            VALUES (?)
        """, (
            quest_name,
        ))

        conn.commit()

        conn.close()

    return redirect(
        url_for("admin")
    )


# ==================================================
# DELETE QUEST
# ==================================================

@app.route(
    "/admin/quest/delete/<int:quest_id>",
    methods=["POST"]
)
def delete_quest(quest_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("login")
        )

    conn = get_db()

    quest = conn.execute("""
        SELECT name
        FROM quests
        WHERE id = ?
    """, (
        quest_id,
    )).fetchone()

    if quest is None:

        conn.close()

        return redirect(
            url_for("admin")
        )

    quest_name = quest["name"]

    # クエストに紐づく記録も削除
    conn.execute("""
        DELETE FROM records
        WHERE quest = ?
    """, (
        quest_name,
    ))

    # クエスト削除
    conn.execute("""
        DELETE FROM quests
        WHERE id = ?
    """, (
        quest_id,
    ))

    conn.commit()

    conn.close()

    return redirect(
        url_for("admin")
    )


# ==================================================
# ADD WEAPON
# ==================================================

@app.route(
    "/admin/weapon/add",
    methods=["POST"]
)
def add_weapon():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("login")
        )

    weapon_name = request.form.get(
        "weapon_name",
        ""
    ).strip()

    if weapon_name:

        conn = get_db()

        conn.execute("""
            INSERT OR IGNORE INTO weapons
            (name)
            VALUES (?)
        """, (
            weapon_name,
        ))

        conn.commit()

        conn.close()

    return redirect(
        url_for("admin")
    )


# ==================================================
# ADD PLATFORM
# ==================================================

@app.route(
    "/admin/platform/add",
    methods=["POST"]
)
def add_platform():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("login")
        )

    platform_name = request.form.get(
        "platform_name",
        ""
    ).strip()

    if platform_name:

        conn = get_db()

        conn.execute("""
            INSERT OR IGNORE INTO platforms
            (name)
            VALUES (?)
        """, (
            platform_name,
        ))

        conn.commit()

        conn.close()

    return redirect(
        url_for("admin")
    )


# ==================================================
# EDIT RECORD
# ==================================================

@app.route(
    "/admin/edit/<int:record_id>",
    methods=["GET", "POST"]
)
def edit_record(record_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("login")
        )

    conn = get_db()

    if request.method == "POST":

        player = request.form.get(
            "player",
            ""
        ).strip()

        quest = request.form.get(
            "quest",
            ""
        ).strip()

        weapon = request.form.get(
            "weapon",
            ""
        ).strip()

        time_string = request.form.get(
            "time",
            ""
        ).strip()

        platform = request.form.get(
            "platform",
            ""
        ).strip()

        # YouTube URLは任意
        video_url = request.form.get(
            "video_url",
            ""
        ).strip()

        time_seconds = time_to_seconds(
            time_string
        )

        if (
            not player
            or not quest
            or not weapon
            or not platform
            or time_seconds is None
        ):

            conn.close()

            return redirect(
                url_for("admin")
            )

        conn.execute("""
            UPDATE records
            SET
                player = ?,
                quest = ?,
                weapon = ?,
                time = ?,
                platform = ?,
                video_url = ?
            WHERE id = ?
        """, (
            player,
            quest,
            weapon,
            time_seconds,
            platform,
            video_url,
            record_id
        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for("admin")
        )

    record = conn.execute("""
        SELECT *
        FROM records
        WHERE id = ?
    """, (
        record_id,
    )).fetchone()

    if record is None:

        conn.close()

        return "記録が見つかりません。", 404

    quests = conn.execute("""
        SELECT *
        FROM quests
        ORDER BY id
    """).fetchall()

    weapons = conn.execute("""
        SELECT *
        FROM weapons
        ORDER BY id
    """).fetchall()

    platforms = conn.execute("""
        SELECT *
        FROM platforms
        ORDER BY id
    """).fetchall()

    conn.close()

    return render_template(
        "edit.html",

        record=record,

        quests=quests,

        weapons=weapons,

        platforms=platforms
    )


# ==================================================
# DELETE RECORD
# ==================================================

@app.route(
    "/admin/delete/<int:record_id>"
)
def delete_record(record_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("login")
        )

    conn = get_db()

    conn.execute("""
        DELETE FROM records
        WHERE id = ?
    """, (
        record_id,
    ))

    conn.commit()

    conn.close()

    return redirect(
        url_for("admin")
    )


# ==================================================
# BACKUP
# ==================================================

@app.route(
    "/admin/backup"
)
def backup_database():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("login")
        )

    if not os.path.exists(
        DATABASE
    ):

        return "database.db が見つかりません。"

    backup_dir = "backups"

    os.makedirs(
        backup_dir,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"database_{timestamp}.db"
    )

    path = os.path.join(
        backup_dir,
        filename
    )

    shutil.copy2(
        DATABASE,
        path
    )

    return send_file(
        path,
        as_attachment=True,
        download_name=filename
    )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )