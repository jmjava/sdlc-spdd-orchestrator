#!/usr/bin/env node
/**
 * Local-only: run real Cursor agents against a seeded consumer repo.
 *
 * This does NOT click the IDE `/` slash menu. It loads each installed
 * `.cursor/commands/<name>.md` and executes it with the Cursor SDK local
 * runtime (same agent harness + models as Cursor) against that cwd, then
 * asserts side-effects with verify-agent-command-effects.sh.
 *
 * Requires: CURSOR_API_KEY (https://cursor.com/dashboard/integrations)
 *
 * Usage:
 *   LIVE_CONSUMER_ROOT=/tmp/sdlc-spdd-live node run-slash-matrix.mjs
 *   LIVE_CONSUMER_ROOT=/tmp/sdlc-spdd-live node run-slash-matrix.mjs --only init,plan,claim
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { Agent, CursorAgentError } from "@cursor/sdk";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const WORK_ID = process.env.LIVE_WORK_ID || "FEAT-001-hello-live";
const ROOT = process.env.LIVE_CONSUMER_ROOT || "/tmp/sdlc-spdd-live";
const MODEL = process.env.LIVE_CURSOR_MODEL || "composer-2.5";
const API_KEY = process.env.CURSOR_API_KEY;

function liveHome(root) {
  const home = path.join(root, "sdlc-spdd");
  return fs.existsSync(home) ? home : root;
}

function liveScripts(root) {
  return path.join(liveHome(root), "scripts");
}

function homeRel(subpath) {
  const home = liveHome(ROOT);
  if (home === ROOT) return subpath;
  return path.join("sdlc-spdd", subpath);
}

// Lifecycle order matches Fowler SPDD: analysis → plan → architect → code → …
const STEPS = [
  {
    slug: "sdlc-spdd-init",
    userArgs: "",
    verify: ["init"],
  },
  {
    slug: "sdlc-claim",
    userArgs: `${WORK_ID} --force`,
    verify: [],
    shellCheck: ["claim-pointer"],
  },
  {
    slug: "sdlc-spdd-analysis",
    userArgs: `@requirements/milestones/${WORK_ID}.md`,
    verify: [],
    fileCheck: [homeRel(`spdd/analysis/${WORK_ID}-analysis.md`)],
    mustCreate: [homeRel(`spdd/analysis/${WORK_ID}-analysis.md`)],
  },
  {
    slug: "sdlc-spdd-plan",
    userArgs: `@${homeRel(`spdd/analysis/${WORK_ID}-analysis.md`)} @${homeRel(`requirements/milestones/${WORK_ID}.md`)} @${homeRel("ROADMAP.md")}`,
    verify: ["plan"],
    mustCreate: [
      homeRel(`spdd/canvas/${WORK_ID}.md`),
      homeRel(`requirements/milestones/${WORK_ID}.md`),
    ],
  },
  {
    slug: "sdlc-spdd-architect",
    userArgs: `@${homeRel(`spdd/canvas/${WORK_ID}.md`)}`,
    verify: ["architect"],
    mustCreate: [homeRel(`spdd/canvas/${WORK_ID}.md`)],
  },
  {
    slug: "sdlc-spdd-code",
    userArgs: `@${homeRel(`spdd/canvas/${WORK_ID}.md`)} operation T01`,
    verify: ["code"],
    mustCreate: [
      homeRel(`spdd/canvas/${WORK_ID}.md`),
      "src/hello.py",
    ],
  },
  {
    slug: "sdlc-spdd-api-test",
    userArgs: `@spdd/canvas/${WORK_ID}.md`,
    verify: [],
    soft: true,
  },
  {
    slug: "sdlc-spdd-review",
    userArgs: `@spdd/canvas/${WORK_ID}.md`,
    verify: ["review"],
    mustCreate: [homeRel(`spdd/reviews/${WORK_ID}-review.md`)],
  },
  {
    slug: "sdlc-spdd-sync",
    userArgs: `@spdd/canvas/${WORK_ID}.md`,
    verify: ["sync"],
    mustCreate: [homeRel(`spdd/sync/${WORK_ID}-sync.md`)],
  },
  {
    slug: "sdlc-spdd-retro",
    userArgs: `@spdd/canvas/${WORK_ID}.md`,
    verify: ["retro"],
    mustCreate: [homeRel("spdd/memory/lessons.jsonl")],
  },
  {
    slug: "sdlc-spdd-prompt-update",
    userArgs: `@spdd/canvas/${WORK_ID}.md clarify T01 acceptance wording`,
    verify: ["prompt-update"],
    soft: true,
    mustCreate: [homeRel(".sdlc/staged/lessons.jsonl")],
  },
  {
    slug: "sdlc-spdd-commit-message",
    userArgs: "",
    verify: [],
    soft: true,
  },
  {
    slug: "sdlc-spdd-whereami",
    userArgs: "",
    verify: [],
    soft: true,
  },
  {
    slug: "sdlc-next",
    userArgs: "",
    verify: [],
    soft: true,
  },
  {
    slug: "sdlc-team",
    userArgs: "",
    verify: [],
    soft: true,
  },
  {
    slug: "sdlc-advance",
    userArgs: "--force",
    verify: [],
    soft: true,
  },
  {
    slug: "sdlc-shelf",
    userArgs: "--reason live-cursor-agent-matrix",
    verify: [],
    soft: true,
  },
];

function parseOnly() {
  const idx = process.argv.indexOf("--only");
  if (idx === -1) return null;
  return new Set(
    (process.argv[idx + 1] || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) =>
        s.startsWith("sdlc-")
          ? s
          : ["claim", "next", "team", "advance", "shelf"].includes(s)
            ? `sdlc-${s}`
            : `sdlc-spdd-${s}`,
      ),
  );
}

function missingFiles(rels = []) {
  return rels.filter((rel) => !fs.existsSync(path.join(ROOT, rel)));
}

function buildPrompt(commandPath, slug, userArgs, mustCreate = []) {
  const body = fs.readFileSync(commandPath, "utf8");
  const must =
    mustCreate.length === 0
      ? []
      : [
          "",
          "Hard requirements for this live matrix run:",
          `- Work ID is exactly: ${WORK_ID}`,
          "- You MUST create or update every Output path listed in the command definition.",
          "- Especially ensure these exist before you finish:",
          ...mustCreate.map((p) => `  - ${p}`),
        ];
  return [
    `Execute the Cursor project slash command /${slug} against this repository.`,
    `The canonical command definition is below (from .cursor/commands/${slug}.md).`,
    `Follow its Required Behavior and Output exactly. Use tools to inspect and edit files.`,
    `Work ID for this live matrix: ${WORK_ID}`,
    userArgs ? `User arguments: ${userArgs}` : "User arguments: (none)",
    "",
    "Constraints:",
    "- Stay inside this repository working tree.",
    "- Prefer small, targeted edits that satisfy the command.",
    `- When the command says to run sdlc.sh, use ${path.join(liveScripts(ROOT), "sdlc.sh")}.`,
    "- When finished, summarize what files you created or changed.",
    ...must,
    "",
    "----- BEGIN COMMAND DEFINITION -----",
    body.trim(),
    "----- END COMMAND DEFINITION -----",
  ].join("\n");
}

function buildRepairPrompt(slug, missing, verifyStderr = "") {
  return [
    `Repair incomplete /${slug} for Work ID ${WORK_ID}.`,
    "The previous agent turn finished but required artifacts are still missing.",
    "Create ONLY the missing files now (minimal valid content is fine).",
    "",
    "Missing paths:",
    ...missing.map((p) => `- ${p}`),
    "",
    verifyStderr ? `Verifier output:\n${verifyStderr}` : "",
  ].join("\n");
}

function runVerify(step) {
  const script = path.join(liveScripts(ROOT), "verify-agent-command-effects.sh");
  const r = spawnSync(
    script,
    ["--target", ROOT, "--work-id", WORK_ID, "--step", step, "--operation", "T01"],
    { encoding: "utf8" },
  );
  return { ok: r.status === 0, stdout: r.stdout, stderr: r.stderr, status: r.status };
}

function checkPointerClaimed() {
  const r = spawnSync(
    path.join(liveScripts(ROOT), "sdlc-pointer.sh"),
    ["get"],
    { encoding: "utf8", env: { ...process.env, SDLC_ROOT: ROOT } },
  );
  return (r.stdout || "").trim() === WORK_ID;
}

async function runAgentPrompt(agent, prompt) {
  const run = await agent.send(prompt);
  const result = await run.wait();
  return { runId: run.id, result };
}

function evaluateStep(step) {
  const failures = [];
  for (const v of step.verify || []) {
    const vr = runVerify(v);
    if (vr.ok) {
      console.log(`  ok   verify --step ${v}`);
    } else {
      console.error(`  FAIL verify --step ${v}`);
      if (vr.stderr) console.error(vr.stderr.trim());
      failures.push({ kind: "verify", step: v, stderr: vr.stderr || "" });
    }
  }
  for (const rel of step.fileCheck || []) {
    if (fs.existsSync(path.join(ROOT, rel))) console.log(`  ok   file ${rel}`);
    else {
      console.error(`  FAIL file missing ${rel}`);
      failures.push({ kind: "file", path: rel });
    }
  }
  if ((step.shellCheck || []).includes("claim-pointer")) {
    if (checkPointerClaimed()) console.log("  ok   pointer claimed");
    else {
      console.error("  FAIL pointer not claimed");
      failures.push({ kind: "pointer" });
    }
  }
  const stillMissing = missingFiles(step.mustCreate || []);
  for (const rel of stillMissing) {
    console.error(`  FAIL must-create missing ${rel}`);
    failures.push({ kind: "must-create", path: rel });
  }
  return { ok: failures.length === 0, failures, missing: stillMissing };
}

async function main() {
  if (!API_KEY) {
    console.error("CURSOR_API_KEY is not set.");
    console.error("Create a key at https://cursor.com/dashboard/integrations");
    console.error("then: export CURSOR_API_KEY=...");
    process.exit(1);
  }
  if (!fs.existsSync(path.join(ROOT, ".cursor/commands"))) {
    console.error(`Consumer missing Cursor commands: ${ROOT}`);
    console.error("Run: ./tests/live-consumer/run-cursor-agent-matrix.sh");
    process.exit(1);
  }

  const only = parseOnly();
  const steps = STEPS.filter((s) => {
    if (!only) return true;
    return only.has(s.slug) || [...only].some((o) => s.slug === o || s.slug.endsWith(`-${o}`) || s.slug === `sdlc-spdd-${o}` || s.slug === `sdlc-${o}`);
  });

  console.log("Cursor SDK local slash matrix");
  console.log(`  consumer: ${ROOT}`);
  console.log(`  work-id:  ${WORK_ID}`);
  console.log(`  model:    ${MODEL}`);
  console.log(`  steps:    ${steps.map((s) => s.slug).join(", ")}`);
  console.log();

  let pass = 0;
  let fail = 0;
  let softFail = 0;

  const agent = await Agent.create({
    apiKey: API_KEY,
    model: { id: MODEL },
    local: {
      cwd: ROOT,
      settingSources: ["project"],
    },
  });

  try {
    console.log(`  agentId: ${agent.agentId}`);
    console.log();

    for (const step of steps) {
      const cmdPath = path.join(ROOT, ".cursor/commands", `${step.slug}.md`);
      if (!fs.existsSync(cmdPath)) {
        console.error(`  FAIL missing command file: ${cmdPath}`);
        fail += 1;
        continue;
      }

      const prompt = buildPrompt(cmdPath, step.slug, step.userArgs, step.mustCreate || []);
      console.log(`== /${step.slug} ==`);
      process.stdout.write("  running agent... ");

      try {
        const { runId, result } = await runAgentPrompt(agent, prompt);
        console.log(`runId=${runId}`);
        if (result.status !== "finished") {
          console.error(`  FAIL run status=${result.status}`);
          if (step.soft) softFail += 1;
          else fail += 1;
          console.log();
          continue;
        }
        console.log("  ok   agent finished");
      } catch (err) {
        if (err instanceof CursorAgentError) {
          console.error(`  FAIL startup: ${err.message} retryable=${err.isRetryable}`);
        } else {
          console.error(`  FAIL unexpected: ${err}`);
        }
        fail += 1;
        console.log();
        continue;
      }

      let evaluation = evaluateStep(step);

      // One repair turn if required artifacts are still missing.
      if (!evaluation.ok && evaluation.missing.length > 0) {
        const verifyErr = evaluation.failures
          .filter((f) => f.kind === "verify")
          .map((f) => f.stderr)
          .join("\n");
        console.log("  repairing missing artifacts...");
        try {
          const repair = buildRepairPrompt(step.slug, evaluation.missing, verifyErr);
          const { runId, result } = await runAgentPrompt(agent, repair);
          console.log(`  repair runId=${runId} status=${result.status}`);
          if (result.status === "finished") {
            evaluation = evaluateStep(step);
          }
        } catch (err) {
          console.error(`  FAIL repair: ${err}`);
        }
      }

      if (evaluation.ok) pass += 1;
      else if (step.soft) softFail += 1;
      else fail += 1;
      console.log();
    }
  } finally {
    if (typeof agent[Symbol.asyncDispose] === "function") {
      await agent[Symbol.asyncDispose]();
    } else if (typeof agent.close === "function") {
      await agent.close();
    }
  }

  console.log(`Results: ${pass} passed, ${fail} failed, ${softFail} soft-failed`);
  process.exit(fail > 0 ? 2 : 0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
