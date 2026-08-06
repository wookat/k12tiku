export async function onRequestGet(context) {
  const { request, env } = context;
  const id = parseInt(new URL(request.url).searchParams.get("id") || "0", 10);
  if (!id) return new Response("bad id", { status: 400 });
  const row = await env.DB.prepare("SELECT * FROM q WHERE id = ?").bind(id).first();
  if (!row) return new Response("not found", { status: 404 });
  return Response.json(row, { headers: { "cache-control": "public, max-age=3600" } });
}
