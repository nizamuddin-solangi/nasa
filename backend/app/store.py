import json, os, sqlite3, uuid
from pathlib import Path
DB=Path(os.getenv('EARTHSCOPE_DB_PATH','earthscope.db')).resolve()
def init():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(DB) as con: con.execute('CREATE TABLE IF NOT EXISTS investigations (id TEXT PRIMARY KEY, created TEXT DEFAULT CURRENT_TIMESTAMP, payload TEXT NOT NULL)')
def save(payload):
 ident=str(uuid.uuid4())
 with sqlite3.connect(DB) as con: con.execute('INSERT INTO investigations(id,payload) VALUES (?,?)',(ident,json.dumps(payload)))
 return ident
def get(ident):
 with sqlite3.connect(DB) as con:
  row=con.execute('SELECT payload FROM investigations WHERE id=?',(ident,)).fetchone()
 return json.loads(row[0]) if row else None
def list_recent(limit=20):
 with sqlite3.connect(DB) as con:
  rows=con.execute('SELECT id, created, payload FROM investigations ORDER BY created DESC LIMIT ?',(limit,)).fetchall()
 return [{'id': ident, 'created_at': created, 'summary': json.loads(payload).get('statistics',{})} for ident,created,payload in rows]
