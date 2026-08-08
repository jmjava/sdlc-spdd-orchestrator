#!/usr/bin/env node
/**
 * Smoke: Vue3 console first-slice acceptance — POST /api/persistence/status.
 * Expects Flask ops console on CONSOLE_API (default http://127.0.0.1:5051).
 */
const base = (process.env.CONSOLE_API || "http://127.0.0.1:5051").replace(/\/$/, "");
const target = process.env.CONSOLE_TARGET || process.cwd();

async function main() {
  const healthRes = await fetch(`${base}/api/health`);
  if (!healthRes.ok) {
    throw new Error(`health ${healthRes.status}`);
  }
  const health = await healthRes.json();
  console.log("health", health);

  const res = await fetch(`${base}/api/persistence/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ target }),
  });
  const data = await res.json();
  if (!res.ok || data.ok === false) {
    throw new Error(`persistence status failed: ${JSON.stringify(data)}`);
  }
  console.log("persistence.ok", data.ok);
  console.log("persistence.backends", data.backends || data.available);
  console.log("smoke passed");
}

main().catch((err) => {
  console.error("smoke failed:", err.message || err);
  process.exit(1);
});
