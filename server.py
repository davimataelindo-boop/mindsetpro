#!/usr/bin/env python3
"""mindsetpro — self-contained full-stack MVP using only Python's standard library."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from http import cookies
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib, hmac, json, os, re, secrets, sqlite3, mimetypes

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
DATA = ROOT / "data"
DB_PATH = DATA / "mente_forte.db"
PORT = int(os.getenv("PORT", "8000"))
SESSION_DAYS = int(os.getenv("SESSION_DAYS", "30"))

PLANS = {
    "foco": {
        "title": "Foco com leveza",
        "description": "Para escolher o essencial e proteger sua atenção.",
        "days": [
            ("Nomeie a prioridade", "Escreva a única tarefa que faria diferença hoje."),
            ("Bloco sem distração", "Faça 15 minutos de uma tarefa sem alternar de janela."),
            ("Volte ao agora", "Use três respirações lentas sempre que sua atenção escapar."),
            ("Diga não ao excesso", "Remova uma tarefa ou distração que não é essencial."),
            ("Feche ciclos", "Conclua uma pequena pendência antes de começar outra."),
            ("Revise seu ritmo", "Observe quando você se concentra melhor e por quê."),
            ("Escolha de novo", "Planeje a próxima semana com uma prioridade por dia."),
        ],
    },
    "confianca": {
        "title": "Confiança em ação",
        "description": "Para agir antes de se sentir 100% pronto.",
        "days": [
            ("Reconheça uma força", "Anote algo que você já aprendeu a fazer bem."),
            ("Aja pequeno", "Faça uma ação de cinco minutos em direção ao seu objetivo."),
            ("Troque a pergunta", "Em vez de 'e se der errado?', pergunte 'qual é o próximo passo?'"),
            ("Colecione evidências", "Registre uma decisão que você tomou e sustentou."),
            ("Fale consigo", "Escreva uma frase que você diria a alguém que ama."),
            ("Aceite o desconforto", "Faça algo levemente desafiador sem buscar aprovação."),
            ("Assine seu próximo passo", "Escolha uma ação concreta para repetir amanhã."),
        ],
    },
    "resiliencia": {
        "title": "Resiliência prática",
        "description": "Para se recuperar mais rápido e aprender com o caminho.",
        "days": [
            ("Separe fato e história", "Escreva o que aconteceu e o que sua mente está concluindo."),
            ("Respire antes de reagir", "Faça uma pausa de 60 segundos antes de responder."),
            ("Encontre o aprendizado", "Complete: 'da próxima vez, eu posso…'"),
            ("Peça suporte", "Envie uma mensagem honesta para alguém de confiança."),
            ("Recomece sem drama", "Retome uma tarefa interrompida por apenas cinco minutos."),
            ("Cuide do básico", "Escolha sono, comida, movimento ou pausa como prioridade."),
            ("Reconheça a travessia", "Liste três coisas difíceis que você já atravessou."),
        ],
    },
    "visao": {
        "title": "Visão com propósito",
        "description": "Para conectar as ações de hoje com a vida que você quer construir.",
        "days": [
            ("Descreva o norte", "Como você quer se sentir daqui a um ano?"),
            ("Escolha um valor", "Qual valor merece aparecer na sua agenda esta semana?"),
            ("Elimine o desvio", "O que está ocupando espaço sem aproximar você do que importa?"),
            ("Visualize o processo", "Imagine você fazendo, não apenas alcançando, seu objetivo."),
            ("Converse com o futuro", "Que conselho seu eu de um ano daria para hoje?"),
            ("Faça caber", "Transforme seu objetivo em um compromisso de 15 minutos."),
            ("Declare a direção", "Escreva uma frase curta sobre o caminho que você escolheu."),
        ],
    },
}


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def db():
    DATA.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
      token TEXT PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      expires_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS thoughts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      content TEXT NOT NULL,
      mood TEXT NOT NULL DEFAULT 'neutro',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS plans (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      focus TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT NOT NULL,
      current_day INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS checkins (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      plan_id INTEGER REFERENCES plans(id) ON DELETE CASCADE,
      day INTEGER NOT NULL,
      completed_at TEXT NOT NULL,
      UNIQUE(user_id, plan_id, day)
    );
    CREATE TABLE IF NOT EXISTS notification_settings (
      user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
      enabled INTEGER NOT NULL DEFAULT 0,
      reminder_time TEXT NOT NULL DEFAULT '08:00',
      updated_at TEXT NOT NULL
    );
    """)
    con.commit(); con.close()


def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"pbkdf2_sha256$210000${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$")
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
        return hmac.compare_digest(test, digest_hex)
    except (ValueError, TypeError):
        return False


def json_response(handler, payload, status=200, extra_headers=None):
    body = json.dumps(payload, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    for key, value in (extra_headers or {}).items(): handler.send_header(key, value)
    handler.end_headers(); handler.wfile.write(body)


def error(handler, message, status=400): json_response(handler, {"error": message}, status)


def valid_email(value): return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value or ""))


def user_from_request(handler):
    raw = handler.headers.get("Cookie", "")
    jar = cookies.SimpleCookie(); jar.load(raw)
    morsel = jar.get("session")
    if not morsel: return None
    con = db(); row = con.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires_at>?", (morsel.value, now_iso())).fetchone(); con.close()
    return row


def session_cookie(token):
    jar = cookies.SimpleCookie(); jar["session"] = token
    jar["session"]["path"] = "/"; jar["session"]["max-age"] = str(SESSION_DAYS * 86400)
    jar["session"]["httponly"] = True; jar["session"]["samesite"] = "Lax"
    return jar.output(header="").strip()


def start_session(user_id):
    token = secrets.token_urlsafe(40); expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).replace(microsecond=0).isoformat()
    con = db(); con.execute("INSERT INTO sessions(token,user_id,expires_at) VALUES(?,?,?)", (token, user_id, expires)); con.commit(); con.close(); return token


def parse_json(handler):
    try:
        length = int(handler.headers.get("Content-Length", "0")); raw = handler.rfile.read(length)
        return json.loads(raw.decode() or "{}")
    except (ValueError, json.JSONDecodeError): return None


def plan_for_user(con, user_id):
    row = con.execute("SELECT * FROM plans WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    if not row: return None
    focus = row["focus"]; definition = PLANS.get(focus, PLANS["foco"])
    completed = {r["day"] for r in con.execute("SELECT day FROM checkins WHERE user_id=? AND plan_id=?", (user_id, row["id"]))}
    today_day = min(max(row["current_day"], 1), len(definition["days"]))
    return {"id": row["id"], "focus": focus, "title": row["title"], "description": row["description"], "current_day": today_day, "total_days": len(definition["days"]), "days": [{"day": i+1, "title": d[0], "description": d[1], "completed": i+1 in completed} for i,d in enumerate(definition["days"])]}


def streak(con, user_id):
    dates = [r["d"] for r in con.execute("SELECT DISTINCT substr(completed_at,1,10) d FROM checkins WHERE user_id=? ORDER BY d DESC", (user_id,))]
    if not dates: return 0
    count = 0; current = datetime.now(timezone.utc).date()
    for date_text in dates:
        date = datetime.strptime(date_text, "%Y-%m-%d").date()
        if date == current - timedelta(days=count): count += 1
        elif date < current - timedelta(days=count): break
    return count


class App(BaseHTTPRequestHandler):
    server_version = "MenteForte/1.0"

    def log_message(self, fmt, *args):
        if os.getenv("QUIET") != "1": super().log_message(fmt, *args)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/me": return self.api_me()
        if path == "/api/dashboard": return self.api_dashboard()
        if path == "/api/thoughts": return self.api_thoughts()
        if path == "/api/notifications": return self.api_notifications()
        if path == "/health": return json_response(self, {"ok": True, "service": "mindsetpro"})
        return self.static_file(path)

    def do_POST(self):
        path = urlparse(self.path).path
        routes = {"/api/register": self.api_register, "/api/login": self.api_login, "/api/logout": self.api_logout, "/api/thoughts": self.api_add_thought, "/api/checkins": self.api_checkin, "/api/plans": self.api_create_plan, "/api/notifications": self.api_save_notifications}
        if path in routes: return routes[path]()
        return error(self, "Rota não encontrada", 404)

    def auth(self):
        user = user_from_request(self)
        if not user: error(self, "Faça login para continuar", 401)
        return user

    def api_register(self):
        data = parse_json(self)
        if not data: return error(self, "Envie os dados do cadastro")
        name = str(data.get("name", "")).strip()[:80]; email = str(data.get("email", "")).strip().lower()[:160]; password = str(data.get("password", ""))
        if len(name) < 2: return error(self, "Digite seu nome")
        if not valid_email(email): return error(self, "Digite um e-mail válido")
        if len(password) < 8: return error(self, "A senha precisa ter pelo menos 8 caracteres")
        con = db()
        try:
            cur = con.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)", (name,email,hash_password(password),now_iso())); uid = cur.lastrowid
            focus = str(data.get("focus", "foco")); definition = PLANS.get(focus, PLANS["foco"])
            con.execute("INSERT INTO plans(user_id,focus,title,description,created_at) VALUES(?,?,?,?,?)", (uid,focus,definition["title"],definition["description"],now_iso()))
            con.execute("INSERT INTO notification_settings(user_id,updated_at) VALUES(?,?)", (uid,now_iso())); con.commit()
        except sqlite3.IntegrityError:
            con.close(); return error(self, "Já existe uma conta com esse e-mail", 409)
        con.close(); return json_response(self, {"ok": True, "user": {"id": uid, "name": name, "email": email}}, 201, {"Set-Cookie": session_cookie(start_session(uid))})

    def api_login(self):
        data = parse_json(self)
        email = str((data or {}).get("email", "")).strip().lower(); password = str((data or {}).get("password", ""))
        con = db(); user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone(); con.close()
        if not user or not verify_password(password, user["password_hash"]): return error(self, "E-mail ou senha incorretos", 401)
        return json_response(self, {"ok": True, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}, 200, {"Set-Cookie": session_cookie(start_session(user["id"]))})

    def api_logout(self):
        raw = self.headers.get("Cookie", ""); jar = cookies.SimpleCookie(); jar.load(raw); morsel = jar.get("session")
        if morsel:
            con = db(); con.execute("DELETE FROM sessions WHERE token=?", (morsel.value,)); con.commit(); con.close()
        return json_response(self, {"ok": True}, 200, {"Set-Cookie": "session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"})

    def api_me(self):
        user = user_from_request(self)
        if not user: return json_response(self, {"authenticated": False})
        return json_response(self, {"authenticated": True, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}})

    def api_dashboard(self):
        user = self.auth()
        if not user: return
        con = db(); plan = plan_for_user(con, user["id"]); thought_count = con.execute("SELECT COUNT(*) c FROM thoughts WHERE user_id=?", (user["id"],)).fetchone()["c"]; checkins = con.execute("SELECT COUNT(*) c FROM checkins WHERE user_id=?", (user["id"],)).fetchone()["c"]; settings = con.execute("SELECT enabled,reminder_time FROM notification_settings WHERE user_id=?", (user["id"],)).fetchone(); current_streak = streak(con, user["id"]); con.close()
        current = plan["current_day"] if plan else 1; score = checkins * 25 + thought_count * 10 + current_streak * 15
        return json_response(self, {"user": {"name": user["name"], "email": user["email"]}, "score": score, "streak": current_streak, "thought_count": thought_count, "checkins": checkins, "plan": plan, "notifications": {"enabled": bool(settings["enabled"]) if settings else False, "reminder_time": settings["reminder_time"] if settings else "08:00"}, "today": {"day": current, "done": any(d["day"] == current and d["completed"] for d in (plan["days"] if plan else []))}})

    def api_thoughts(self):
        user = self.auth()
        if not user: return
        con = db(); rows = con.execute("SELECT id,content,mood,created_at FROM thoughts WHERE user_id=? ORDER BY id DESC LIMIT 30", (user["id"],)).fetchall(); con.close()
        return json_response(self, {"thoughts": [dict(r) for r in rows]})

    def api_add_thought(self):
        user = self.auth()
        if not user: return
        data = parse_json(self); content = str((data or {}).get("content", "")).strip()[:2000]; mood = str((data or {}).get("mood", "neutro"))[:20]
        if len(content) < 3: return error(self, "Escreva pelo menos uma frase")
        con = db(); cur = con.execute("INSERT INTO thoughts(user_id,content,mood,created_at) VALUES(?,?,?,?)", (user["id"],content,mood,now_iso())); con.commit(); row = con.execute("SELECT id,content,mood,created_at FROM thoughts WHERE id=?", (cur.lastrowid,)).fetchone(); con.close()
        return json_response(self, {"ok": True, "thought": dict(row)}, 201)

    def api_checkin(self):
        user = self.auth()
        if not user: return
        data = parse_json(self); plan_id = int((data or {}).get("plan_id", 0)); day = int((data or {}).get("day", 0))
        con = db(); plan = con.execute("SELECT * FROM plans WHERE id=? AND user_id=?", (plan_id,user["id"])).fetchone()
        if not plan: con.close(); return error(self, "Plano não encontrado", 404)
        definition = PLANS.get(plan["focus"], PLANS["foco"])
        if day < 1 or day > len(definition["days"]): con.close(); return error(self, "Dia inválido")
        try: con.execute("INSERT INTO checkins(user_id,plan_id,day,completed_at) VALUES(?,?,?,?)", (user["id"],plan_id,day,now_iso())); con.execute("UPDATE plans SET current_day=? WHERE id=?", (min(day+1,len(definition["days"])),plan_id)); con.commit()
        except sqlite3.IntegrityError: pass
        con.close(); return json_response(self, {"ok": True})

    def api_create_plan(self):
        user = self.auth()
        if not user: return
        data = parse_json(self); focus = str((data or {}).get("focus", "foco")); definition = PLANS.get(focus)
        if not definition: return error(self, "Escolha um foco válido")
        con = db(); cur = con.execute("INSERT INTO plans(user_id,focus,title,description,created_at) VALUES(?,?,?,?,?)", (user["id"],focus,definition["title"],definition["description"],now_iso())); con.commit(); con.close()
        return json_response(self, {"ok": True, "plan_id": cur.lastrowid}, 201)

    def api_notifications(self):
        user = self.auth()
        if not user: return
        con = db(); row = con.execute("SELECT enabled,reminder_time FROM notification_settings WHERE user_id=?", (user["id"],)).fetchone(); con.close(); return json_response(self, {"enabled": bool(row["enabled"]), "reminder_time": row["reminder_time"]} if row else {"enabled": False, "reminder_time": "08:00"})

    def api_save_notifications(self):
        user = self.auth()
        if not user: return
        data = parse_json(self); enabled = 1 if data.get("enabled") else 0; reminder = str(data.get("reminder_time", "08:00"));
        if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", reminder): return error(self, "Horário inválido")
        con = db(); con.execute("INSERT INTO notification_settings(user_id,enabled,reminder_time,updated_at) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET enabled=excluded.enabled, reminder_time=excluded.reminder_time, updated_at=excluded.updated_at", (user["id"],enabled,reminder,now_iso())); con.commit(); con.close(); return json_response(self, {"ok": True, "enabled": bool(enabled), "reminder_time": reminder})

    def static_file(self, path):
        if path == "/": path = "/index.html"
        file_path = (STATIC / path.lstrip("/")).resolve()
        try: file_path.relative_to(STATIC.resolve())
        except ValueError: return error(self, "Arquivo não encontrado", 404)
        if not file_path.is_file(): return error(self, "Arquivo não encontrado", 404)
        if not file_path.is_file():
            flat_path = (ROOT / path.lstrip("/")).resolve()
            try: flat_path.relative_to(ROOT.resolve())
            except ValueError: return error(self, "Arquivo não encontrado", 404)
            if flat_path.is_file(): file_path = flat_path
        if not file_path.is_file(): return error(self, "Arquivo não encontrado", 404)
        data = file_path.read_bytes(); content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200); self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") or content_type in ("application/javascript", "application/json") else "")); self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-cache"); self.end_headers(); self.wfile.write(data)


if __name__ == "__main__":
    init_db(); print(f"mindsetpro rodando em http://127.0.0.1:{PORT}"); ThreadingHTTPServer(("0.0.0.0", PORT), App).serve_forever()
