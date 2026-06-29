"""
  Your Closet: Styling App Backend (single-user)
  app.py

NO EXTERNAL API REQUIRED:
(optional notification hook only, this measn your code will remain local to your drive).
NO LOGIN, NOR MULTI USER LINKS:
(that would need an API/ AWS inferences/netwrok set up. It remains One closet, one person.

Single user closet app contraints:
  - A simple "Friends" list (just names, stored locally: not separate accounts, not separate closets).
  - Borrowing: log an item as borrowed from a friend, with a due back date.
  - Lending: log an item as lent to a friend, with a due back date.
  - Returns: mark any loan as returned, which closes it out.
  - In app notifications: notifications are computed on demand from due dates and surfaced in the UI, no email/SMS/push
    service involved.
  - External notification hook: if using the NOTIFY_WEBHOOK_URL environment variable to a personal Slack/Discord webhook, overdue reminders will also be posted there. This is fully optional and the app works completely offline if you never set it.

INSTALLATION:
  pip install flask pillow requests

  python app.py
  # -> http://localhost:5000  or   # -> http://localhost:8000

  If need for external pings on overdue loans:
  export NOTIFY_WEBHOOK_URL="https://hooks.slack.com/services/..." for further research ont he topic

HOW IT WORKS CODE WORKS/BREAKDOWN
  1. UPLOAD:  upload a clothing photo, tag it, color is auto detected locally (Pillow).
  2. PROFILE: pick/create a style profile (target palette).
  3. SUGGEST: rule based outfit matcher scores combos against the active profile.
  4. FRIENDS: add friends by name (simple local list).
  5. BORROW/LEND: log an item borrowed from, or lent to, a friend, with a due back date.
  6. RETURN: mark a loan returned at any time.
  7. NOTIFY: every time the app is opened, it checks all active loans against today's date and surfaces "Due soon" (within 2 days) and "overdue" alerts in-app. No external service needed.

No network calls/API/AWS/ICLOUD/IBM are made unless explicitly set
NOTIFY_WEBHOOK_URL: everything else runs fully offline.

"""

#Remeber to set from local hoost, varies.
#This is a mockup version of the app.
#importing

import os
import sqlite3
from datetime import datetime
from itertools import product as iproduct

from flask import Flask, jsonify, request, send_from_directory
from PIL import Image
from werkzeug.utils import secure_filename

#Config 
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR  = os.path.join(BASE_DIR, "uploads")
DB_PATH     = os.path.join(BASE_DIR, "closet.db")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}
MAX_THUMB   = 800
DUE_SOON_DAYS = 2  # surface a "due soon" notification this many days before due_back

#set this env var to also post overdue/due soon alerts to a personal webhook (Slack/Discord/etc). Leave unset to stay fully offline.
#this is to avoid an API connection.
#this is where an API would be placed if it was used.
NOTIFY_WEBHOOK_URL = os.environ.get("NOTIFY_WEBHOOK_URL", "").strip()

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=None)

CATEGORIES = ["Top", "Bottom", "Dress", "Outerwear", "Shoes", "Bag", "Accessory"]

DEFAULT_PROFILES = [#Here is the setup for the type of styling profile, more can be added and defiend better for more acruate results.
    {
        "name": "Quiet Luxury",
        "description": "Beige, white, and black. Clean lines, minimal contrast.",
        "palette": ["#F4EFE4", "#FDFCFA", "#111110", "#D8CEBC", "#3D3B35"],
        "mood": "minimal",
    },
    {
        "name": "Old Money",
        "description": "Cream, navy, hunter green, camel. Tailored, heritage fabrics.",
        "palette": ["#F5F0E1", "#1B2A41", "#2F4F3E", "#C19A6B", "#FFFFFF"],
        "mood": "tailored",
    },
    {
        "name": "Soft Girl",
        "description": "Baby pink, lavender, cream. Soft textures, rounded silhouettes.",
        "palette": ["#F8D7DA", "#E6D9F2", "#FFF8F0", "#FCE8E6", "#FFFFFF"],
        "mood": "soft",
    },
    {
        "name": "Monochrome Editorial",
        "description": "Pure black and white only. Sharp, graphic, high contrast.",
        "palette": ["#000000", "#FFFFFF", "#1A1A1A", "#EDEDED"],
        "mood": "graphic",
    },
]


#Database creation
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        dominant_color TEXT NOT NULL,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        palette TEXT NOT NULL,
        mood TEXT
    );

    CREATE TABLE IF NOT EXISTS saved_outfits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_name TEXT,
        item_ids TEXT NOT NULL,
        label TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,                  -- NULL allowed if item was later deleted
        item_name_snapshot TEXT NOT NULL, -- captured at loan time, survives item deletion
        friend_id INTEGER NOT NULL,
        direction TEXT NOT NULL,          -- 'borrowed' (from friend) or 'lent' (to friend)
        borrowed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        due_back TEXT NOT NULL,           -- YYYY-MM-DD
        returned_at TEXT,                 -- NULL while active
        notes TEXT
    );
    """)
    existing = conn.execute("SELECT COUNT(*) c FROM profiles").fetchone()["c"]
    if existing == 0:
        for p in DEFAULT_PROFILES:
            conn.execute(
                "INSERT INTO profiles (name, description, palette, mood) VALUES (?,?,?,?)",
                (p["name"], p["description"], ",".join(p["palette"]), p["mood"]),
            )
    conn.commit()
    conn.close()


#color extrcation (from locla, no api, but this can be altered for api usuage)
def extract_dominant_color(image_path: str) -> str:
    img = Image.open(image_path).convert("RGB")
    img = img.resize((50, 50))
    paletted = img.convert("P", palette=Image.ADAPTIVE, colors=6)
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    most_common_idx = color_counts[0][1]
    r = palette[most_common_idx * 3]
    g = palette[most_common_idx * 3 + 1]
    b = palette[most_common_idx * 3 + 2]
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def hex_to_rgb(hexstr: str):
    hexstr = hexstr.lstrip("#")
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))


def color_distance(hex_a: str, hex_b: str) -> float:
    ra, ga, ba = hex_to_rgb(hex_a)
    rb, gb, bb = hex_to_rgb(hex_b)
    dist = ((ra - rb) ** 2 + (ga - gb) ** 2 + (ba - bb) ** 2) ** 0.5
    return dist / 441.67


def closest_palette_distance(item_hex: str, palette: list) -> float:
    return min(color_distance(item_hex, p) for p in palette)


#Outfit scoring (rule base, no api used, this cna be altered)
def score_outfit(item_colors: list, palette: list) -> float:
    distances = [closest_palette_distance(c, palette) for c in item_colors]
    avg_dist = sum(distances) / len(distances)
    palette_score = max(0, 1 - avg_dist) * 70

    pairwise = []
    for i in range(len(item_colors)):
        for j in range(i + 1, len(item_colors)):
            pairwise.append(color_distance(item_colors[i], item_colors[j]))
    if pairwise:
        avg_pairwise = sum(pairwise) / len(pairwise)
        cohesion_score = max(0, 1 - avg_pairwise) * 30
    else:
        cohesion_score = 30

    return round(palette_score + cohesion_score, 1)


def generate_outfit_candidates(items: list, max_results: int = 12) -> list:
    tops      = [i for i in items if i["category"] == "Top"]
    bottoms   = [i for i in items if i["category"] == "Bottom"]
    dresses   = [i for i in items if i["category"] == "Dress"]
    outerwear = [i for i in items if i["category"] == "Outerwear"] or [None]
    shoes     = [i for i in items if i["category"] == "Shoes"] or [None]
    bags      = [i for i in items if i["category"] == "Bag"] or [None]

    cores = []
    for t, b in iproduct(tops, bottoms):
        cores.append([t, b])
    for d in dresses:
        cores.append([d])

    combos = []
    for core in cores:
        for o, sh, bg in iproduct(outerwear, shoes, bags):
            combo = [x for x in core + [o, sh, bg] if x is not None]
            if len(combo) >= 2:
                combos.append(combo)

    return combos[: max_results * 6]


#Item loan status/ notifviations (local)
def compute_loan_status(due_back_str: str, returned_at) -> str:
    if returned_at:
        return "returned"
    due = datetime.strptime(due_back_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    if due < today:
        return "overdue"
    if (due - today).days <= DUE_SOON_DAYS:
        return "due_soon"
    return "active"


def maybe_send_webhook(message: str):
    """
    Optional external notification. Only runs if NOTIFY_WEBHOOK_URL
    is set. Uses `requests` if available; silently no-ops otherwise
    so the app never crashes from a missing optional dependency.
    """
    if not NOTIFY_WEBHOOK_URL:
        return
    try:
        import requests
        requests.post(NOTIFY_WEBHOOK_URL, json={"text": message}, timeout=5)
    except Exception as e:
        print(f"[notify] Webhook send failed (non-fatal): {e}")


#Flask routes: core pages
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


#Routes: closet items
@app.route("/api/items", methods=["GET"])
def list_items():
    conn = get_db()
    rows = conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/items", methods=["POST"])
def upload_item():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    name = request.form.get("name", "Untitled item").strip()
    category = request.form.get("category", "Top").strip()
    notes = request.form.get("notes", "").strip()

    if category not in CATEGORIES:
        return jsonify({"error": f"Invalid category. Must be one of {CATEGORIES}"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        return jsonify({"error": f"Unsupported file type .{ext}"}), 400

    safe_name = secure_filename(f"item_{os.urandom(6).hex()}.{ext}")
    save_path = os.path.join(UPLOAD_DIR, safe_name)

    img = Image.open(file.stream).convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_THUMB:
        scale = MAX_THUMB / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img.save(save_path, format="JPEG", quality=88)

    dominant_color = extract_dominant_color(save_path)

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO items (filename, name, category, dominant_color, notes) VALUES (?,?,?,?,?)",
        (safe_name, name, category, dominant_color, notes),
    )
    conn.commit()
    item_id = cur.lastrowid
    conn.close()

    return jsonify({
        "id": item_id, "filename": safe_name, "name": name,
        "category": category, "dominant_color": dominant_color, "notes": notes,
    })


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    conn = get_db()
    row = conn.execute("SELECT filename FROM items WHERE id=?", (item_id,)).fetchone()
    if row:
        path = os.path.join(UPLOAD_DIR, row["filename"])
        if os.path.exists(path):
            os.remove(path)
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
    conn.close()
    return jsonify({"deleted": item_id})


#route profiles--> whos broowing what 
@app.route("/api/profiles", methods=["GET"])
def list_profiles():
    conn = get_db()
    rows = conn.execute("SELECT * FROM profiles ORDER BY name").fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d["palette"] = d["palette"].split(",")
        out.append(d)
    return jsonify(out)


@app.route("/api/profiles", methods=["POST"])
def create_profile():
    body = request.get_json(force=True)
    name = (body.get("name") or "").strip()
    palette = body.get("palette") or []
    description = (body.get("description") or "").strip()
    mood = (body.get("mood") or "").strip()

    if not name or not palette:
        return jsonify({"error": "name and palette (list of hex colors) are required"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO profiles (name, description, palette, mood) VALUES (?,?,?,?)",
            (name, description, ",".join(palette), mood),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"Profile '{name}' already exists"}), 409
    conn.close()
    return jsonify({"name": name, "description": description, "palette": palette, "mood": mood})


#routes outfit suggestions, this can also use use a different algo the larger this gets.
@app.route("/api/suggest", methods=["GET"])
def suggest_outfits():
    profile_name = request.args.get("profile", "").strip()
    limit = int(request.args.get("limit", 6))

    conn = get_db()
    profile_row = conn.execute("SELECT * FROM profiles WHERE name=?", (profile_name,)).fetchone()
    if not profile_row:
        conn.close()
        return jsonify({"error": f"Profile '{profile_name}' not found"}), 404
    palette = profile_row["palette"].split(",")

    items_rows = conn.execute("SELECT * FROM items").fetchall()
    conn.close()
    items = [dict(r) for r in items_rows]

    if len(items) < 2:
        return jsonify({"error": "Add at least 2 items to your closet to get outfit suggestions"}), 400

    combos = generate_outfit_candidates(items, max_results=limit)
    scored = []
    for combo in combos:
        colors = [it["dominant_color"] for it in combo]
        score = score_outfit(colors, palette)
        scored.append({"score": score, "items": combo})

    scored.sort(key=lambda x: x["score"], reverse=True)
    seen_sets = set()
    unique = []
    for combo in scored:
        id_set = frozenset(it["id"] for it in combo["items"])
        if id_set in seen_sets:
            continue
        seen_sets.add(id_set)
        unique.append(combo)
        if len(unique) >= limit:
            break

    return jsonify({"profile": profile_name, "palette": palette, "outfits": unique})


@app.route("/api/outfits", methods=["POST"])
def save_outfit():
    body = request.get_json(force=True)
    item_ids = body.get("item_ids", [])
    profile_name = body.get("profile_name", "")
    label = body.get("label", "")

    if not item_ids:
        return jsonify({"error": "item_ids required"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO saved_outfits (profile_name, item_ids, label) VALUES (?,?,?)",
        (profile_name, ",".join(str(i) for i in item_ids), label),
    )
    conn.commit()
    conn.close()
    return jsonify({"saved": True})


@app.route("/api/outfits", methods=["GET"])
def list_saved_outfits():
    conn = get_db()
    rows = conn.execute("SELECT * FROM saved_outfits ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


#Routes: friends/smiple local lists, this can then be chnaged to have an api for external use outside of one computer.
@app.route("/api/friends", methods=["GET"])
def list_friends():
    conn = get_db()
    rows = conn.execute("SELECT * FROM friends ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/friends", methods=["POST"])
def add_friend():
    """JSON body: { name, notes }"""
    body = request.get_json(force=True)
    name = (body.get("name") or "").strip()
    notes = (body.get("notes") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    conn = get_db()
    try:
        cur = conn.execute("INSERT INTO friends (name, notes) VALUES (?,?)", (name, notes))
        conn.commit()
        friend_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"'{name}' is already in your friends list"}), 409
    conn.close()
    return jsonify({"id": friend_id, "name": name, "notes": notes})


@app.route("/api/friends/<int:friend_id>", methods=["DELETE"])
def delete_friend(friend_id):
    conn = get_db()
    active = conn.execute(
        "SELECT COUNT(*) c FROM loans WHERE friend_id=? AND returned_at IS NULL", (friend_id,)
    ).fetchone()["c"]
    if active > 0:
        conn.close()
        return jsonify({"error": "This friend has active loans. Mark them returned first."}), 400
    conn.execute("DELETE FROM friends WHERE id=?", (friend_id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": friend_id})


#routes: loan constraints (borrow/lend/return)
@app.route("/api/loans", methods=["POST"])
def create_loan():
    """
    JSON body: { item_id, friend_id, direction, due_back: 'YYYY-MM-DD', notes }
    direction: 'borrowed' (item is coming FROM the friend, into your use)
               'lent'     (item is going TO the friend, out of your closet)
    """
    body = request.get_json(force=True)
    item_id = body.get("item_id")
    friend_id = body.get("friend_id")
    direction = (body.get("direction") or "").strip()
    due_back = (body.get("due_back") or "").strip()
    notes = (body.get("notes") or "").strip()

    if direction not in ("borrowed", "lent"):
        return jsonify({"error": "direction must be 'borrowed' or 'lent'"}), 400
    if not item_id or not friend_id or not due_back:
        return jsonify({"error": "item_id, friend_id, and due_back are required"}), 400
    try:
        datetime.strptime(due_back, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "due_back must be in YYYY-MM-DD format"}), 400

    conn = get_db()
    item = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    friend = conn.execute("SELECT * FROM friends WHERE id=?", (friend_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"error": "Item not found"}), 404
    if not friend:
        conn.close()
        return jsonify({"error": "Friend not found"}), 404

    conn.execute(
        "INSERT INTO loans (item_id, item_name_snapshot, friend_id, direction, due_back, notes) VALUES (?,?,?,?,?,?)",
        (item_id, item["name"], friend_id, direction, due_back, notes),
    )
    conn.commit()
    conn.close()

    verb = "Borrowed" if direction == "borrowed" else "Lent"
    prep = "from" if direction == "borrowed" else "to"
    maybe_send_webhook(f"{verb} \"{item['name']}\" {prep} {friend['name']} — due back {due_back}")

    return jsonify({"created": True, "item_id": item_id, "friend_id": friend_id, "direction": direction, "due_back": due_back})


@app.route("/api/loans", methods=["GET"])
def list_loans():
    """
    GET /api/loans?status=active|overdue|due_soon|returned|all (default: all)
    GET /api/loans?direction=borrowed|lent
    Returns loans joined with friend name + item info, with computed status.
    """
    status_filter = request.args.get("status", "").strip()
    direction_filter = request.args.get("direction", "").strip()

    conn = get_db()
    rows = conn.execute("""
        SELECT l.*, f.name AS friend_name,
               i.filename AS item_filename, i.category AS item_category
        FROM loans l
        JOIN friends f ON f.id = l.friend_id
        LEFT JOIN items i ON i.id = l.item_id
        ORDER BY l.due_back ASC
    """).fetchall()
    conn.close()

    out = []
    for r in rows:
        d = dict(r)
        d["status"] = compute_loan_status(d["due_back"], d["returned_at"])
        if direction_filter and d["direction"] != direction_filter:
            continue
        if status_filter and status_filter != "all" and d["status"] != status_filter:
            continue
        out.append(d)
    return jsonify(out)


@app.route("/api/loans/<int:loan_id>/return", methods=["POST"])
def return_loan(loan_id):
    conn = get_db()
    loan = conn.execute("SELECT * FROM loans WHERE id=?", (loan_id,)).fetchone()
    if not loan:
        conn.close()
        return jsonify({"error": "Loan not found"}), 404
    conn.execute("UPDATE loans SET returned_at=? WHERE id=?", (datetime.now().isoformat(), loan_id))
    conn.commit()
    conn.close()
    return jsonify({"returned": True, "loan_id": loan_id})


@app.route("/api/loans/<int:loan_id>", methods=["DELETE"])
def delete_loan(loan_id):
    """Remove a loan record entirely (e.g. logged by mistake)."""
    conn = get_db()
    conn.execute("DELETE FROM loans WHERE id=?", (loan_id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": loan_id})


#routes: notifications(in-app, computed on demand
@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """
    Computes "due soon" and "overdue" alerts from active loans
    every time this is called — no background job, no stored
    notification state, fully derived from due_back vs today.
    """
    conn = get_db()
    rows = conn.execute("""
        SELECT l.*, f.name AS friend_name, i.category AS item_category
        FROM loans l
        JOIN friends f ON f.id = l.friend_id
        LEFT JOIN items i ON i.id = l.item_id
        WHERE l.returned_at IS NULL
        ORDER BY l.due_back ASC
    """).fetchall()
    conn.close()

    notifications = []
    for r in rows:
        d = dict(r)
        status = compute_loan_status(d["due_back"], d["returned_at"])
        if status not in ("due_soon", "overdue"):
            continue
        verb = "borrowing" if d["direction"] == "borrowed" else "lending"
        prep = "from" if d["direction"] == "borrowed" else "to"
        if status == "overdue":
            message = f"Overdue: you're {verb} \"{d['item_name_snapshot']}\" {prep} {d['friend_name']} — was due {d['due_back']}"
        else:
            message = f"Due soon: \"{d['item_name_snapshot']}\" {prep} {d['friend_name']} is due back {d['due_back']}"
        notifications.append({
            "loan_id": d["id"], "status": status, "message": message,
            "direction": d["direction"], "friend_name": d["friend_name"],
            "item_name": d["item_name_snapshot"], "due_back": d["due_back"],
        })
        if status == "overdue":
            maybe_send_webhook(message)

    return jsonify(notifications)


if __name__ == "__main__":
    init_db()
    print(f"Closet DB: {DB_PATH}")
    print(f"Uploads dir: {UPLOAD_DIR}")
    if NOTIFY_WEBHOOK_URL:
        print(f"External webhook notifications: ENABLED -> {NOTIFY_WEBHOOK_URL}")
    else:
        print("External webhook notifications: disabled (fully offline). Set NOTIFY_WEBHOOK_URL to enable.")
    app.run(debug=True, port=5000)
