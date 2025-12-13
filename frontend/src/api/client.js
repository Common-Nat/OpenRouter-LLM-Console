export async function apiGet(path) {
  const r = await fetch(path, { headers: { "Accept": "application/json" } });
  if (!r.ok) throw new Error(await safeText(r));
  return r.json();
}

export async function apiPost(path, body) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await safeText(r));
  return r.json();
}

export async function apiPut(path, body) {
  const r = await fetch(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await safeText(r));
  return r.json();
}

export async function apiDelete(path) {
  const r = await fetch(path, { method: "DELETE", headers: { "Accept": "application/json" } });
  if (!r.ok) throw new Error(await safeText(r));
  return r.text();
}

async function safeText(r) {
  try { return await r.text(); } catch { return `${r.status}`; }
}
