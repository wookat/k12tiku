export async function onRequestGet(context) {
  const { env } = context;
  const rows = await env.DB.prepare(
    "SELECT stage, subject, COUNT(*) AS n FROM q GROUP BY stage, subject"
  ).all();
  const types = await env.DB.prepare(
    "SELECT qtype, COUNT(*) AS n FROM q WHERE qtype != '' GROUP BY qtype ORDER BY n DESC LIMIT 12"
  ).all();
  return Response.json(
    { subjects: rows.results, qtypes: types.results },
    { headers: { "cache-control": "public, max-age=3600" } }
  );
}
