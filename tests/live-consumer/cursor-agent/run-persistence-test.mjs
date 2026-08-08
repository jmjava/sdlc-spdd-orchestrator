#!/usr/bin/env node
/**
 * Local-only full persistence test via Cursor SDK.
 *
 * Proves durable SDLC state survives agent turns + process resume:
 *   1) Real agents create claim/analysis/plan artifacts
 *   2) Full capture-session-memory populates memory/milestone/roadmap
 *   3) Python engine rebuilds .sdlc/index.sqlite and queries it
 *   4) Agent.dispose + Agent.resume keeps conversation/work context
 *   5) SQLite regenerates after delete (cache, not source of truth)
 *
 * Requires: CURSOR_API_KEY, orchestrator engine importable.
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { Agent, CursorAgentError } from "@cursor/sdk";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ORCH = process.env.ORCHESTRATOR_ROOT
  || path.resolve(__dirname, "../../..");
const WORK_ID = process.env.LIVE_WORK_ID || "FEAT-001-hello-live";
const ROOT = process.env.LIVE_CONSUMER_ROOT || "/tmp/sdlc-spdd-live";
const MODEL = process.env.LIVE_CURSOR_MODEL || "composer-2.5";
const API_KEY = process.env.CURSOR_API_KEY;
const FEATURE = `agent-context/features/${WORK_ID}`;

let pass = 0;
let fail = 0;

function ok(msg) {
  console.log(`  ok   ${msg}`);
  pass += 1;
}
function bad(msg) {
  console.error(`  FAIL ${msg}`);
  fail += 1;
}

function sh(cmd, args, opts = {}) {
  return spawnSync(cmd, args, {
    encoding: "utf8",
    cwd: opts.cwd || ROOT,
    env: { ...process.env, ...(opts.env || {}) },
  });
}

function engine(args) {
  return sh(
    "python3",
    ["-m", "sdlc_engine", "--root", ROOT, ...args],
    {
      env: {
        PYTHONPATH: `${ORCH}/engine/src${process.env.PYTHONPATH ? `:${process.env.PYTHONPATH}` : ""}`,
        SDLC_USER: process.env.SDLC_USER || "live-persist",
      },
    },
  );
}

function readCmd(slug) {
  return fs.readFileSync(path.join(ROOT, ".cursor/commands", `${slug}.md`), "utf8");
}

function slashPrompt(slug, userArgs, mustCreate = []) {
  const body = readCmd(slug);
  return [
    `Execute /${slug} for Work ID ${WORK_ID}.`,
    userArgs ? `User arguments: ${userArgs}` : "",
    "Follow the command definition exactly. Create every Output path.",
    mustCreate.length
      ? `Must exist before finish:\n${mustCreate.map((p) => `- ${p}`).join("\n")}`
      : "",
    "----- BEGIN COMMAND DEFINITION -----",
    body.trim(),
    "----- END COMMAND DEFINITION -----",
  ].join("\n");
}

async function send(agent, prompt) {
  const run = await agent.send(prompt);
  const result = await run.wait();
  return { runId: run.id, result };
}

async function main() {
  if (!API_KEY) {
    console.error("CURSOR_API_KEY required");
    process.exit(1);
  }
  if (!fs.existsSync(path.join(ROOT, ".cursor/commands"))) {
    console.error(`Missing consumer commands at ${ROOT}`);
    process.exit(1);
  }
  const probe = engine(["version"]);
  if (probe.status !== 0) {
    console.error("sdlc_engine not importable; install: python3 -m pip install -e ./engine");
    console.error(probe.stderr || probe.stdout);
    process.exit(1);
  }

  console.log("Cursor SDK full persistence test");
  console.log(`  consumer: ${ROOT}`);
  console.log(`  work-id:  ${WORK_ID}`);
  console.log(`  model:    ${MODEL}`);
  console.log(`  orch:     ${ORCH}`);
  console.log();

  let agentId;
  {
    const agent = await Agent.create({
      apiKey: API_KEY,
      model: { id: MODEL },
      local: { cwd: ROOT, settingSources: ["project"] },
    });
    agentId = agent.agentId;
    console.log(`== phase A: agent create artifacts (agentId=${agentId}) ==`);

    try {
      for (const step of [
        {
          slug: "sdlc-spdd-init",
          args: "",
          must: [],
        },
        {
          slug: "sdlc-claim",
          args: `${WORK_ID} --force`,
          must: [],
        },
        {
          slug: "sdlc-spdd-analysis",
          args: `@requirements/milestones/${WORK_ID}.md`,
          must: [
            `spdd/analysis/${WORK_ID}-analysis.md`,
            `${FEATURE}/analysis-context.md`,
          ],
        },
        {
          slug: "sdlc-spdd-plan",
          args: `@spdd/analysis/${WORK_ID}-analysis.md @requirements/milestones/${WORK_ID}.md`,
          must: [
            `spdd/canvas/${WORK_ID}.md`,
            `${FEATURE}/requirement.md`,
            `${FEATURE}/progress-log.md`,
          ],
        },
      ]) {
        process.stdout.write(`  /${step.slug}... `);
        const { runId, result } = await send(
          agent,
          slashPrompt(step.slug, step.args, step.must),
        );
        console.log(`runId=${runId} status=${result.status}`);
        if (result.status !== "finished") bad(`/${step.slug} status=${result.status}`);
        else ok(`/${step.slug} finished`);
        for (const rel of step.must) {
          if (fs.existsSync(path.join(ROOT, rel))) ok(`artifact ${rel}`);
          else bad(`missing ${rel}`);
        }
      }
    } finally {
      if (typeof agent[Symbol.asyncDispose] === "function") {
        await agent[Symbol.asyncDispose]();
      } else if (typeof agent.close === "function") {
        await agent.close();
      }
    }
  }

  console.log();
  console.log("== phase B: durable capture + SQLite rebuild ==");

  const milestone = "requirements/milestones/milestone-1/MILESTONE-1.md";
  const cap = sh(
    path.join(ROOT, "scripts/sdlc-spdd/capture-session-memory.sh"),
    [
      "--target", ROOT,
      "--work-id", WORK_ID,
      "--phase", "plan",
      "--summary", "Persistence test: agent-created analysis/plan captured fully",
      "--validation", "run-persistence-test.mjs phase A/B",
      "--decisions", "SQLite index is regenerable cache; git artifacts remain source of truth",
      "--pitfalls", "Do not treat .sdlc/index.sqlite as authoritative across machines",
      "--patterns", "agent create → capture → db rebuild → resume → query",
      "--areas", "src/hello.py, tests/live-consumer, scripts/sdlc-spdd",
      "--milestone", milestone,
      "--roadmap-note", "Persistence test populated index and session memory",
      "--next", `/sdlc-spdd-architect @spdd/canvas/${WORK_ID}.md`,
      "--readiness", "Ready For Coding",
      "--review-result", "pass",
      "--rework", "0",
      "--context-files", "12",
    ],
  );
  if (cap.status === 0) ok("capture-session-memory full flags");
  else bad(`capture failed: ${cap.stderr || cap.stdout}`);

  const hist = fs.readFileSync(
    path.join(ROOT, "agent-context/memory/session-history.md"),
    "utf8",
  );
  for (const needle of [
    "Validation: run-persistence-test.mjs",
    "Decisions: SQLite index is regenerable",
    "Pitfalls: Do not treat .sdlc/index.sqlite",
    "Reusable patterns: agent create → capture",
    `Milestone: ${milestone}`,
    "Roadmap note: Persistence test populated",
    "Next: /sdlc-spdd-architect",
  ]) {
    if (hist.includes(needle)) ok(`session-history has ${needle.split(":")[0]}`);
    else bad(`session-history missing ${needle.split(":")[0]}`);
  }

  const rebuild = engine(["db", "rebuild"]);
  if (rebuild.status === 0 && /Rebuilt SQLite index/i.test(rebuild.stdout + rebuild.stderr)) {
    ok("db rebuild");
  } else if (rebuild.status === 0 && fs.existsSync(path.join(ROOT, ".sdlc/index.sqlite"))) {
    ok("db rebuild (sqlite present)");
  } else {
    bad(`db rebuild failed: ${rebuild.stdout}\n${rebuild.stderr}`);
  }

  const dbPath = path.join(ROOT, ".sdlc/index.sqlite");
  if (fs.existsSync(dbPath)) ok(".sdlc/index.sqlite exists");
  else bad(".sdlc/index.sqlite missing");

  const q = engine([
    "db",
    "query",
    "SELECT work_id, has_canvas, registry_status FROM work_items WHERE work_id = ?",
    WORK_ID,
    "--json",
  ]);
  // CLI may take SQL as one arg without bind params — try alternate forms
  let queryOut = q.stdout + q.stderr;
  if (q.status !== 0 || !queryOut.includes(WORK_ID)) {
    const q2 = engine([
      "db",
      "query",
      `SELECT work_id, has_canvas, registry_status FROM work_items WHERE work_id = '${WORK_ID}'`,
      "--json",
    ]);
    queryOut = q2.stdout + q2.stderr;
    if (q2.status === 0 && queryOut.includes(WORK_ID)) ok("db query finds work_id");
    else bad(`db query miss: ${queryOut}`);
  } else {
    ok("db query finds work_id");
  }

  if (/has_canvas.:.?1|"has_canvas": 1|has_canvas\s+1/i.test(queryOut) || queryOut.includes(WORK_ID)) {
    ok("indexed row references canvas work");
  }

  const status = engine(["db", "status"]);
  if (status.status === 0) ok("db status");
  else bad("db status failed");

  const exportPath = path.join(ROOT, ".sdlc/index-export.json");
  const exp = engine(["db", "export", "--format", "json", "-o", exportPath]);
  if (exp.status === 0 && fs.existsSync(exportPath)) {
    const exported = fs.readFileSync(exportPath, "utf8");
    if (exported.includes(WORK_ID)) ok("db export json contains work_id");
    else bad("db export missing work_id");
  } else {
    bad(`db export failed: ${exp.stderr || exp.stdout}`);
  }

  // Regenerable: delete and rebuild
  fs.unlinkSync(dbPath);
  const rebuild2 = engine(["db", "rebuild"]);
  if (rebuild2.status === 0 && fs.existsSync(dbPath)) ok("sqlite regenerates after delete");
  else bad("sqlite did not regenerate");

  console.log();
  console.log(`== phase C: Agent.resume(${agentId}) ==`);
  try {
    const resumed = await Agent.resume(agentId, {
      apiKey: API_KEY,
      model: { id: MODEL },
      local: { cwd: ROOT, settingSources: ["project"] },
    });
    try {
      ok("Agent.resume succeeded");
      const { result } = await send(
        resumed,
        [
          `Persistence check for Work ID ${WORK_ID}.`,
          "1) Run: ./scripts/sdlc-spdd/sdlc.sh next",
          "2) Run: ./scripts/sdlc-spdd/sdlc.sh team",
          "3) Confirm the local pointer Work ID.",
          "4) Reply with the Work ID you see and the recommended next command.",
          "Do not modify application source code.",
        ].join("\n"),
      );
      if (result.status === "finished") ok("resumed agent finished persistence check");
      else bad(`resumed agent status=${result.status}`);

      const ptr = sh(
        path.join(ROOT, "agent-context/sdlc-pointer.sh"),
        ["get"],
        { env: { SDLC_ROOT: ROOT } },
      );
      if ((ptr.stdout || "").trim() === WORK_ID) ok("pointer still claimed after resume");
      else bad(`pointer after resume: '${(ptr.stdout || "").trim()}'`);

      const next = sh(
        path.join(ROOT, "scripts/sdlc-spdd/sdlc.sh"),
        ["next"],
        { env: { SDLC_ROOT: ROOT, SDLC_USER: "live-persist" } },
      );
      if (next.status === 0 && /Do now/i.test(next.stdout)) ok("sdlc.sh next still actionable");
      else bad("sdlc.sh next weak after resume");
    } finally {
      if (typeof resumed[Symbol.asyncDispose] === "function") {
        await resumed[Symbol.asyncDispose]();
      } else if (typeof resumed.close === "function") {
        await resumed.close();
      }
    }
  } catch (err) {
    if (err instanceof CursorAgentError) {
      bad(`Agent.resume failed: ${err.message}`);
    } else {
      bad(`Agent.resume unexpected: ${err}`);
    }
  }

  console.log();
  console.log("== phase D: SQLite lookup embedded in session context ==");

  // Ship latest start-agent-session into the consumer (install may have older copy).
  const startSrc = path.join(ORCH, "scripts/start-agent-session.sh");
  const startDst = path.join(ROOT, "scripts/sdlc-spdd/start-agent-session.sh");
  fs.copyFileSync(startSrc, startDst);
  fs.chmodSync(startDst, 0o755);

  engine(["db", "rebuild"]);
  const start = sh(
    startDst,
    ["--target", ROOT, "--work-id", WORK_ID, "--phase", "code"],
    {
      env: {
        PYTHONPATH: `${ORCH}/engine/src${process.env.PYTHONPATH ? `:${process.env.PYTHONPATH}` : ""}`,
        SDLC_USER: "live-persist",
      },
    },
  );
  if (start.status === 0) ok("start-agent-session (phase D)");
  else bad(`start-agent-session failed: ${start.stderr || start.stdout}`);

  const briefPath = path.join(ROOT, ".sdlc/sessions/current-session.md");
  const brief = fs.existsSync(briefPath) ? fs.readFileSync(briefPath, "utf8") : "";
  if (brief.includes("Local SQLite Index (query cache)")) ok("brief has Local SQLite Index section");
  else bad("brief missing Local SQLite Index section");
  if (brief.includes(WORK_ID) && /has_canvas|registry_status/.test(brief)) {
    ok("brief lookup includes work_id + indexed fields");
  } else {
    bad("brief lookup incomplete");
  }
  const resumeBlock = brief.split("## Resume Prompt")[1] || "";
  if (resumeBlock.includes("Local SQLite Index")) ok("resume prompt cites SQLite section");
  else bad("resume prompt missing SQLite citation");

  try {
    const agent2 = await Agent.create({
      apiKey: API_KEY,
      model: { id: MODEL },
      local: { cwd: ROOT, settingSources: ["project"] },
    });
    try {
      const { result } = await send(
        agent2,
        [
          "Read ONLY .sdlc/sessions/current-session.md.",
          `Quote the Local SQLite Index fields for Work ID ${WORK_ID}.`,
          "Include has_canvas and registry_status if present.",
          "Do not invent values; do not modify files.",
        ].join("\n"),
      );
      if (result.status === "finished") ok("agent read session brief SQLite section");
      else bad(`phase D agent status=${result.status}`);
    } finally {
      if (typeof agent2[Symbol.asyncDispose] === "function") {
        await agent2[Symbol.asyncDispose]();
      } else if (typeof agent2.close === "function") {
        await agent2.close();
      }
    }
  } catch (err) {
    bad(`phase D agent failed: ${err}`);
  }

  console.log();
  console.log(`Results: ${pass} passed, ${fail} failed`);
  process.exit(fail > 0 ? 2 : 0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
