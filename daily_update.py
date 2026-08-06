"""Daily incremental import of newly published open question sets into D1.

Checks known continuously-updated open sources for splits/years not yet in the
database, normalizes them with clean.clean, and appends new rows (plus FTS).

Usage: CF=<api token> python3 daily_update.py
"""
import io
import json
import os
import re
import time
import urllib.request

import clean as cleaner

TOK = os.environ["CF"]
ACC = "ddff52d24ee44e21a021c15eaffcc86d"
DB = "f10af997-668f-4c0d-8095-e3dfaf2e16b2"
URL = f"https://api.cloudflare.com/client/v4/accounts/{ACC}/d1/database/{DB}/query"
PREFIX = ("INSERT OR IGNORE INTO q(id,stage,grade,subject,qtype,difficulty,"
          "question,answer,explanation,source) VALUES ")
MAX_BYTES = 85000
LSUBJ = {"math": "数学", "physics": "物理", "chemistry": "化学", "biology": "生物"}


def d1(sql):
    for attempt in range(5):
        try:
            req = urllib.request.Request(
                URL, data=json.dumps({"sql": sql}).encode(),
                headers={"Authorization": "Bearer " + TOK,
                         "Content-Type": "application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=180).read())
            if r["success"]:
                return r["result"][0]
            print("d1 fail", r["errors"], flush=True)
        except Exception as e:
            print("d1 err", e, flush=True)
        time.sleep(2 * (attempt + 1))
    raise SystemExit("D1 unreachable")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "k12tiku-daily"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def esc(s):
    return "'" + str(s).replace("'", "''") + "'"


def existing_sources():
    rows = d1("SELECT DISTINCT source FROM q")["results"]
    return {r["source"] for r in rows}


def livek12_new_records(known_sources):
    """Import any livek12bench zh_* splits whose batch label is not in D1 yet."""
    import pandas as pd

    api = ("https://huggingface.co/api/datasets/Shawn-wxh/livek12bench/"
           "tree/main?recursive=true")
    try:
        files = fetch_json(api)
    except Exception as e:
        print("hf list failed", e)
        return []
    out = []
    for f in files:
        m = re.match(r"zh_(\d{4})-.*\.parquet$", os.path.basename(f.get("path", "")))
        if not m:
            continue
        batch = m.group(1)
        label = f"20{batch[:2]}年{int(batch[2:])}月模拟/联考"
        if label in known_sources:
            continue
        url = ("https://huggingface.co/datasets/Shawn-wxh/livek12bench/"
               f"resolve/main/{f['path']}")
        req = urllib.request.Request(url, headers={"User-Agent": "k12tiku-daily"})
        df = pd.read_parquet(io.BytesIO(urllib.request.urlopen(req, timeout=300).read()))
        for r in df.to_dict("records"):
            subj = LSUBJ.get(str(r.get("subject", "")).lower())
            if not subj:
                continue
            q = cleaner.clean(str(r.get("question", "")))
            if len(q) < 5:
                continue
            out.append({
                "stage": "高中", "grade": "", "subject": subj,
                "qtype": str(r.get("question_type", "") or ""),
                "difficulty": "",
                "question": q,
                "answer": cleaner.clean(str(r.get("answer", ""))),
                "explanation": cleaner.clean(str(r.get("solution", "") or "")),
                "source": label,
            })
        print(f"livek12 {label}: {len(df)} raw")
    return out


def insert(rows):
    next_id = d1("SELECT COALESCE(MAX(id),0)+1 AS n FROM q")["results"][0]["n"]
    parts, size, done = [], 0, 0
    for i, r in enumerate(rows):
        v = "(%d,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (
            next_id + i, esc(r["stage"]), esc(r["grade"]), esc(r["subject"]),
            esc(r["qtype"]), esc(r["difficulty"]), esc(r["question"]),
            esc(r["answer"]), esc(r["explanation"]), esc(r["source"]))
        b = len(v.encode())
        if size + b > MAX_BYTES and parts:
            d1(PREFIX + ",".join(parts) + ";")
            done += len(parts)
            parts, size = [], 0
        parts.append(v)
        size += b
    if parts:
        d1(PREFIX + ",".join(parts) + ";")
        done += len(parts)
    d1(f"INSERT INTO q_fts(rowid, question) SELECT id, question FROM q "
       f"WHERE id >= {next_id}")
    return done


def main():
    known = existing_sources()
    rows = livek12_new_records(known)
    if not rows:
        print("no new records today")
        return
    n = insert(rows)
    print(f"imported {n} new questions")


if __name__ == "__main__":
    main()
