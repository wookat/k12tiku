"""Load a questions jsonl file into remote D1 via the REST /query endpoint.

Usage: CF=<api token> python3 load_d1.py questions_ms_english.jsonl [--no-fts]
"""
import json, os, sys, time, urllib.request, urllib.error

TOK = os.environ["CF"]
URL = ("https://api.cloudflare.com/client/v4/accounts/ddff52d24ee44e21a021c15eaffcc86d"
       "/d1/database/f10af997-668f-4c0d-8095-e3dfaf2e16b2/query")
BASE = os.path.dirname(os.path.abspath(__file__))
PREFIX = ("INSERT OR IGNORE INTO q(id,stage,grade,subject,qtype,difficulty,"
          "question,answer,explanation,source) VALUES ")
MAX_BYTES = 85000


def run(sql):
    for attempt in range(5):
        try:
            req = urllib.request.Request(
                URL, data=json.dumps({"sql": sql}).encode(),
                headers={"Authorization": "Bearer " + TOK, "Content-Type": "application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=180).read())
            if r["success"]:
                return r
            print("fail", r["errors"], flush=True)
        except urllib.error.HTTPError as e:
            print("http", e.code, e.read()[:200], flush=True)
        except Exception as e:
            print("err", e, flush=True)
        time.sleep(2 * (attempt + 1))
    raise SystemExit("giving up")


def esc(s):
    return "'" + str(s).replace("'", "''") + "'"


def main():
    path = os.path.join(BASE, sys.argv[1])
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    parts, size, done = [], 0, 0
    for r in rows:
        v = "(%d,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (
            r["id"], esc(r["stage"]), esc(r["grade"]), esc(r["subject"]), esc(r["qtype"]),
            esc(r["difficulty"]), esc(r["question"]), esc(r["answer"]),
            esc(r["explanation"]), esc(r["source"]))
        b = len(v.encode())
        if size + b > MAX_BYTES and parts:
            run(PREFIX + ",".join(parts) + ";")
            done += len(parts)
            print(done, flush=True)
            parts, size = [], 0
        parts.append(v)
        size += b
    if parts:
        run(PREFIX + ",".join(parts) + ";")
        done += len(parts)
    print("rows done", done)
    if "--no-fts" not in sys.argv:
        run("DELETE FROM q_fts;")
        run("INSERT INTO q_fts(rowid, question) SELECT id, question FROM q;")
        print("fts rebuilt")


main()
