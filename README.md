# k12tiku — 题库搜索（小学/初中/高中各学科）

线上：https://k12tiku.pages.dev

Cloudflare Pages + Pages Functions + D1（SQLite FTS5 trigram 全文检索）。

## 数据来源

- CMATH（小米，CC BY 4.0）：小学 1-6 年级数学应用题
- CJEval（MIT）：初中十学科 2.6 万题，含题型/难度/答案/解析
- GAOKAO-Bench：2010-2022 高考各学科真题及解析

## 构建数据

```bash
# 克隆三个上游数据集到 /tmp/{cmath,cjeval,gaokao}
python3 etl.py            # 归一化 -> questions.jsonl
CF=<D1 token> python3 load_rest.py   # 通过 D1 REST /query 分批写入并重建 FTS
```

## 部署

```bash
CLOUDFLARE_ACCOUNT_ID=... CLOUDFLARE_API_TOKEN=... npx wrangler pages deploy
```
