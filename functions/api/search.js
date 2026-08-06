export async function onRequestGet(context) {
  const { request, env } = context;
  const u = new URL(request.url);
  const q = (u.searchParams.get("q") || "").trim();
  const stage = u.searchParams.get("stage") || "";
  const subject = u.searchParams.get("subject") || "";
  const qtype = u.searchParams.get("qtype") || "";
  const page = Math.max(1, parseInt(u.searchParams.get("page") || "1", 10));
  const per = 20;

  const conds = [];
  const binds = [];
  if (stage) { conds.push("q.stage = ?"); binds.push(stage); }
  if (subject) { conds.push("q.subject = ?"); binds.push(subject); }
  if (qtype) { conds.push("q.qtype = ?"); binds.push(qtype); }

  let from, order;
  if (q && q.length >= 3) {
    from = "q_fts JOIN q ON q.id = q_fts.rowid";
    conds.unshift("q_fts MATCH ?");
    binds.unshift('"' + q.replace(/"/g, "") + '"');
    order = "ORDER BY rank";
  } else if (q) {
    from = "q";
    conds.push("q.question LIKE ?");
    binds.push("%" + q + "%");
    order = "ORDER BY q.id";
  } else {
    from = "q";
    order = "ORDER BY q.id";
  }
  const where = conds.length ? "WHERE " + conds.join(" AND ") : "";

  const cnt = await env.DB.prepare(
    `SELECT COUNT(*) AS n FROM ${from} ${where}`
  ).bind(...binds).first();

  const rows = await env.DB.prepare(
    `SELECT q.id, q.stage, q.grade, q.subject, q.qtype, q.difficulty,
            substr(q.question, 1, 300) AS question, q.source
     FROM ${from} ${where} ${order} LIMIT ${per} OFFSET ${(page - 1) * per}`
  ).bind(...binds).all();

  return Response.json(
    { total: cnt.n, page, per, results: rows.results },
    { headers: { "cache-control": "public, max-age=300" } }
  );
}
