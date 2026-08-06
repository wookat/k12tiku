"""Import dry-melon/Chinese-middle-school-English-exam-questions (CC BY 4.0)
into questions_ms_english.jsonl: junior-high English exam questions, grades 7-9."""
import json, os, glob
from huggingface_hub import snapshot_download

START_ID = int(os.environ["START_ID"])
BASE = os.path.dirname(os.path.abspath(__file__))
REPO = "dry-melon/Chinese-middle-school-English-exam-questions"

QTYPE = {
    "Multiple-Choice-Question": "单项选择",
    "Cloze-With-Multiple-Choices": "完形填空",
    "Cloze-With-Free-Responses": "完形填空",
    "Reading-Comprehension-With-Multiple-Choices": "阅读理解",
    "Reading-Comprehension-With-True-or-False": "阅读理解",
}
GRADE = {"grade7": "7年级", "grade8": "8年级", "grade9": "9年级"}

root = snapshot_download(REPO, repo_type="dataset")
rows = []
for path in sorted(glob.glob(os.path.join(root, "dataset", "grade*", "*.jsonl"))):
    grade = GRADE[os.path.basename(os.path.dirname(path))]
    kind = os.path.basename(path)[:-len(".jsonl")]
    qtype = QTYPE.get(kind, "单项选择")
    for line in open(path, encoding="utf-8"):
        rec = json.loads(line)
        ctx = (rec.get("context") or "").strip()
        qs = rec.get("questions") or []
        parts, answers, exps = [], [], []
        if ctx:
            parts.append(ctx)
        for i, q in enumerate(qs, 1):
            text = (q.get("text") or "").strip()
            head = f"{i}. {text}" if len(qs) > 1 else text
            opts = [f"{k}. {v}" for k, v in (q.get("choices") or {}).items() if v]
            if head or opts:
                parts.append("\n".join([p for p in [head, "  ".join(opts)] if p]))
            ans = (q.get("answer") or "").strip()
            if ans:
                answers.append(f"{i}. {ans}" if len(qs) > 1 else ans)
            exp = (q.get("explanation") or "").strip()
            if exp:
                exps.append(f"{i}. {exp}" if len(qs) > 1 else exp)
        question = "\n\n".join(parts).strip()
        if len(question) < 5 or not answers:
            continue
        rows.append({
            "stage": "初中", "grade": grade, "subject": "英语", "qtype": qtype,
            "difficulty": "", "question": question[:6000],
            "answer": "\n".join(answers)[:3000],
            "explanation": "\n".join(exps)[:8000],
            "source": "初中英语题库（7-9年级）",
        })

out = os.path.join(BASE, "questions_ms_english.jsonl")
with open(out, "w", encoding="utf-8") as f:
    for i, r in enumerate(rows):
        r["id"] = START_ID + i + 1
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(len(rows))
