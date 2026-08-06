"""Generate batched INSERT SQL files from questions.jsonl."""
import json, os

BASE = os.path.dirname(__file__)
os.makedirs(os.path.join(BASE, "sql"), exist_ok=True)

def esc(s):
    return "'" + str(s).replace("'", "''") + "'"

rows = [json.loads(l) for l in open(os.path.join(BASE, "questions.jsonl"), encoding="utf-8")]
CHUNK = 800
files = 0
for i in range(0, len(rows), CHUNK):
    parts = []
    for r in rows[i:i+CHUNK]:
        parts.append("(%d,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (
            r["id"], esc(r["stage"]), esc(r["grade"]), esc(r["subject"]),
            esc(r["qtype"]), esc(r["difficulty"]), esc(r["question"]),
            esc(r["answer"]), esc(r["explanation"]), esc(r["source"])))
    sql = "INSERT INTO q(id,stage,grade,subject,qtype,difficulty,question,answer,explanation,source) VALUES\n" + ",\n".join(parts) + ";\n"
    with open(os.path.join(BASE, "sql", f"batch_{i//CHUNK:03d}.sql"), "w", encoding="utf-8") as f:
        f.write(sql)
    files += 1
with open(os.path.join(BASE, "sql", "zz_fts.sql"), "w") as f:
    f.write("INSERT INTO q_fts(rowid, question) SELECT id, question FROM q;\n")
print("files", files, "rows", len(rows))
