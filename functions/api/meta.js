import { sourceCond } from "./_source.js";

export async function onRequestGet(context) {
  const { request, env } = context;
  const src = new URL(request.url).searchParams.get("src") || "";
  const cond = sourceCond(src, "source");
  const where = cond ? ` WHERE ${cond}` : "";
  const rows = await env.DB.prepare(
    `SELECT stage, subject, COUNT(*) AS n FROM q${where} GROUP BY stage, subject`
  ).all();
  const types = await env.DB.prepare(
    `SELECT qtype, COUNT(*) AS n FROM q${where}${cond ? " AND" : " WHERE"} qtype != '' GROUP BY qtype ORDER BY n DESC LIMIT 12`
  ).all();
  return Response.json(
    { subjects: rows.results, qtypes: types.results },
    { headers: { "cache-control": "public, max-age=3600" } }
  );
}
