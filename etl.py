"""Normalize CMATH / CJEval / GAOKAO-Bench into a unified questions.jsonl."""
import json, os, re, glob

OUT = os.path.join(os.path.dirname(__file__), "questions.jsonl")
rows = []

def _s(v):
    if v is None:
        return ""
    if isinstance(v, dict):
        return "\n".join(f"{k}: {_s(x)}" for k, x in v.items()).strip()
    if isinstance(v, (list, tuple)):
        return "\n".join(_s(x) for x in v).strip()
    return str(v).strip()

def add(stage, subject, qtype, difficulty, question, answer, explanation, source, grade=""):
    q = _s(question)
    if len(q) < 5:
        return
    rows.append({
        "stage": stage, "grade": grade, "subject": subject,
        "qtype": qtype or "", "difficulty": difficulty or "",
        "question": q[:6000],
        "answer": _s(answer)[:3000],
        "explanation": _s(explanation)[:8000],
        "source": source,
    })

# ---- CMATH: elementary math ----
for line in open("/tmp/cmath/datasets/cmath_dev.jsonl", encoding="utf-8"):
    d = json.loads(line)
    add("小学", "数学", "应用题", "", d["input"], d["golden"], "", "CMATH",
        grade=f"{d['grade']}年级")

# ---- CJEval: junior high, 10 subjects ----
for path in glob.glob("/tmp/cjeval/data/CJEval_data/*/*.json"):
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        subj = d.get("subject", "").replace("初中", "")
        content = _s(d.get("ques_content", ""))
        content = re.sub(r"^(题目内容|问题描述)[:：]\s*", "", content)
        add("初中", subj, d.get("ques_type", ""), d.get("ques_difficulty", ""),
            content, d.get("ques_answer", ""), d.get("ques_analyze", ""), "CJEval")

# ---- GAOKAO-Bench: senior high ----
SUBJ = {"English": "英语", "Biology": "生物", "Chemistry": "化学", "Chinese": "语文",
        "Geography": "地理", "History": "历史", "Math": "数学", "Physics": "物理",
        "Political": "政治"}
for path in glob.glob("/tmp/gaokao/Data/*/*.json"):
    name = os.path.basename(path)
    subject = next((v for k, v in SUBJ.items() if k in name), None)
    if not subject:
        continue
    qtype = "选择题" if "MCQ" in name else ("填空题" if "Fill" in name else "解答题")
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    for e in data.get("example", []):
        year = e.get("year", "")
        add("高中", subject, qtype, "", e.get("question", ""), e.get("answer", ""),
            e.get("analysis", ""), f"高考真题 {year}")

with open(OUT, "w", encoding="utf-8") as f:
    for i, r in enumerate(rows):
        r["id"] = i + 1
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

from collections import Counter
c = Counter((r["stage"], r["subject"]) for r in rows)
print(len(rows))
for k, v in sorted(c.items()):
    print(k, v)
