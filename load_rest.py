"""Load questions into remote D1 via REST /query, in small chunks."""
import os, json, time, urllib.request, urllib.error

TOK = os.environ["CF"]
URL = "https://api.cloudflare.com/client/v4/accounts/ddff52d24ee44e21a021c15eaffcc86d/d1/database/f10af997-668f-4c0d-8095-e3dfaf2e16b2/query"
BASE = os.path.dirname(os.path.abspath(__file__))

def run(sql):
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, data=json.dumps({"sql": sql}).encode(),
                headers={"Authorization": "Bearer " + TOK, "Content-Type": "application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=120).read())
            if r["success"]:
                return True
            print("fail", r["errors"])
        except urllib.error.HTTPError as e:
            print("http", e.code, e.read()[:200])
        except Exception as e:
            print("err", e)
        time.sleep(2 * (attempt + 1))
    raise SystemExit("giving up")

def esc(s):
    return "'" + str(s).replace("'", "''") + "'"

rows = [json.loads(l) for l in open(os.path.join(BASE, "questions.jsonl"), encoding="utf-8")]
PREFIX = "INSERT OR IGNORE INTO q(id,stage,grade,subject,qtype,difficulty,question,answer,explanation,source) VALUES "
MAX_BYTES = 85000
start = int(os.environ.get("START", "0"))
parts, size, done = [], 0, start
def flush():
    global parts, size, done
    if not parts:
        return
    run(PREFIX + ",".join(parts) + ";")
    done += len(parts)
    if done % 3000 < len(parts):
        print(done, flush=True)
    parts, size = [], 0
for r in rows[start:]:
    v = "(%d,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (
        r["id"], esc(r["stage"]), esc(r["grade"]), esc(r["subject"]),
        esc(r["qtype"]), esc(r["difficulty"]), esc(r["question"]),
        esc(r["answer"]), esc(r["explanation"]), esc(r["source"]))
    b = len(v.encode())
    if size + b > MAX_BYTES:
        flush()
    parts.append(v); size += b
flush()
print("rows done")
run("DELETE FROM q_fts;")
run("INSERT INTO q_fts(rowid, question) SELECT id, question FROM q;")
print("fts done")
