export async function postJson(path, body = {}) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  let data = null;
  try {
    data = await res.json();
  } catch {
    data = { ok: false, error: `Non-JSON response (${res.status})` };
  }
  return { ok: res.ok && data?.ok !== false, status: res.status, data };
}

export async function getHealth() {
  const res = await fetch("/api/health", { headers: { Accept: "application/json" } });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}
