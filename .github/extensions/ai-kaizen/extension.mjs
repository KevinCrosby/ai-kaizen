// Extension: ai-kaizen
// AI-Kaizen transformation toolkit — manage initiatives, evals, PMO scoring,
// CxO dashboard, workforce assessments, governance, and PDCA cycles.

import { execFile } from "node:child_process";
import { joinSession } from "@github/copilot-sdk/extension";

const PYTHON = "/Users/kevincrosby/ai-kaizen/.venv/bin/python3";
const CLI_MODULE = "ai_kaizen.cli";

// Helper: run an ai-kaizen CLI command and return output
function runCli(args, env = {}) {
    return new Promise((resolve) => {
        execFile(
            PYTHON,
            ["-m", CLI_MODULE, ...args],
            {
                cwd: "/Users/kevincrosby/ai-kaizen",
                env: { ...process.env, ...env },
                timeout: 30000,
            },
            (err, stdout, stderr) => {
                if (err) resolve(`Error: ${stderr || err.message}`);
                else resolve(stdout || "(no output)");
            },
        );
    });
}

// Helper: run a Python snippet against the store directly (for features not in CLI)
function runPython(script, env = {}) {
    return new Promise((resolve) => {
        execFile(
            PYTHON,
            ["-c", script],
            {
                cwd: "/Users/kevincrosby/ai-kaizen",
                env: { ...process.env, PYTHONPATH: "src", ...env },
                timeout: 30000,
            },
            (err, stdout, stderr) => {
                if (err) resolve(`Error: ${stderr || err.message}`);
                else resolve(stdout || "(no output)");
            },
        );
    });
}

const session = await joinSession({
    hooks: {
        onUserPromptSubmitted: async (input) => {
            const p = input.prompt.toLowerCase();
            const triggers = [
                "kaizen", "initiative", "eval", "pdca", "gemba",
                "transformation", "cxo", "executive dashboard",
                "pmo", "roi", "workforce", "governance",
                "data readiness", "kill criter", "gate check",
            ];
            if (triggers.some((t) => p.includes(t))) {
                return {
                    additionalContext: [
                        "The user has the AI-Kaizen toolkit installed at ~/ai-kaizen.",
                        "Use the ai-kaizen-* tools to manage initiatives, evals, PDCA, PMO, and CxO metrics.",
                        "The toolkit uses a SQLite DB at ~/.ai-kaizen/kaizen.db.",
                        "Web UI available via `ai-kaizen serve` (port 5001).",
                        "Framework docs: ~/ai-kaizen/docs/framework-v2.md and ~/ai-kaizen/docs/pmo-framework.md",
                    ].join("\n"),
                };
            }
        },
    },
    tools: [
        // ── Initiative Management ────────────────────────────────────
        {
            name: "ai-kaizen-init",
            description: "Create a new AI transformation initiative with name, severity (S0-S3), and transformation type (optimize/redesign/reinvent)",
            parameters: {
                type: "object",
                properties: {
                    name: { type: "string", description: "Initiative name" },
                    severity: {
                        type: "string",
                        enum: ["S0", "S1", "S2", "S3"],
                        description: "Severity class: S0=safety, S1=production, S2=efficiency, S3=advisory",
                    },
                    description: { type: "string", description: "Brief description of the initiative" },
                },
                required: ["name"],
            },
            skipPermission: true,
            handler: async (args) => {
                const cmdArgs = ["init", args.name];
                if (args.severity) cmdArgs.push("--severity", args.severity);
                if (args.description) cmdArgs.push("--description", args.description);
                return runCli(cmdArgs);
            },
        },
        {
            name: "ai-kaizen-list",
            description: "List all AI transformation initiatives with their status, severity, loop, phase, and autonomy level",
            parameters: {
                type: "object",
                properties: {
                    status: {
                        type: "string",
                        enum: ["active", "paused", "killed", "completed", "archived"],
                        description: "Filter by status (optional)",
                    },
                },
            },
            skipPermission: true,
            handler: async (args) => {
                const cmdArgs = ["status"];
                return runCli(cmdArgs);
            },
        },
        {
            name: "ai-kaizen-select",
            description: "Select an initiative as the current working initiative by its ID",
            parameters: {
                type: "object",
                properties: {
                    initiative_id: { type: "string", description: "Initiative ID to select" },
                },
                required: ["initiative_id"],
            },
            skipPermission: true,
            handler: async (args) => runCli(["select", args.initiative_id]),
        },

        // ── Outcomes ─────────────────────────────────────────────────
        {
            name: "ai-kaizen-outcome",
            description: "Define a measurable outcome for the current initiative (metric, baseline, target)",
            parameters: {
                type: "object",
                properties: {
                    metric: { type: "string", description: "What to measure (e.g., 'ticket resolution time')" },
                    baseline: { type: "string", description: "Current state (e.g., '45 min avg')" },
                    target: { type: "string", description: "Target range (e.g., '15-25 min')" },
                    timeframe: { type: "string", description: "Target timeframe (e.g., '90 days')" },
                },
                required: ["metric", "baseline", "target"],
            },
            skipPermission: true,
            handler: async (args) => {
                const cmdArgs = ["outcome", "set",
                    "--metric", args.metric,
                    "--baseline", args.baseline,
                    "--target", args.target,
                ];
                if (args.timeframe) cmdArgs.push("--timeframe", args.timeframe);
                return runCli(cmdArgs);
            },
        },

        // ── Eval Management ──────────────────────────────────────────
        {
            name: "ai-kaizen-eval-scaffold",
            description: "Create an eval suite for the current initiative at a specific level (L0-L3)",
            parameters: {
                type: "object",
                properties: {
                    level: {
                        type: "string",
                        enum: ["L0", "L1", "L2", "L2.5", "L3"],
                        description: "Eval level: L0=safety, L1=assertions, L2=human+model, L2.5=monitoring, L3=experiments",
                    },
                    description: { type: "string", description: "What this eval suite tests" },
                },
                required: ["level"],
            },
            skipPermission: true,
            handler: async (args) => {
                const cmdArgs = ["eval", "scaffold", "--level", args.level];
                if (args.description) cmdArgs.push("--description", args.description);
                return runCli(cmdArgs);
            },
        },
        {
            name: "ai-kaizen-eval-record",
            description: "Record an eval run result (total tests, passed, notes)",
            parameters: {
                type: "object",
                properties: {
                    level: { type: "string", enum: ["L0", "L1", "L2", "L2.5", "L3"] },
                    total: { type: "integer", description: "Total test count" },
                    passed: { type: "integer", description: "Passed test count" },
                    notes: { type: "string", description: "Run notes" },
                },
                required: ["level", "total", "passed"],
            },
            skipPermission: true,
            handler: async (args) => {
                const cmdArgs = ["eval", "record",
                    "--level", args.level,
                    "--total", String(args.total),
                    "--passed", String(args.passed),
                ];
                if (args.notes) cmdArgs.push("--notes", args.notes);
                return runCli(cmdArgs);
            },
        },

        // ── PDCA Cycles ──────────────────────────────────────────────
        {
            name: "ai-kaizen-pdca",
            description: "Log a PDCA entry (Plan/Do/Check/Act) for the current initiative",
            parameters: {
                type: "object",
                properties: {
                    phase: { type: "string", enum: ["plan", "do", "check", "act"] },
                    note: { type: "string", description: "What was done/learned in this phase" },
                },
                required: ["phase", "note"],
            },
            skipPermission: true,
            handler: async (args) => runCli(["pdca", "log", "--phase", args.phase, "--note", args.note]),
        },
        {
            name: "ai-kaizen-gate",
            description: "Run a gate check on the current initiative — checks kill criteria and eval thresholds",
            parameters: { type: "object", properties: {} },
            skipPermission: true,
            handler: async () => runCli(["pdca", "gate"]),
        },

        // ── Data Readiness ───────────────────────────────────────────
        {
            name: "ai-kaizen-data-readiness",
            description: "Assess data readiness for the current initiative across 6 dimensions (0-3 each): existence, accessibility, quality, latency, history, coverage",
            parameters: {
                type: "object",
                properties: {
                    existence: { type: "integer", minimum: 0, maximum: 3 },
                    accessibility: { type: "integer", minimum: 0, maximum: 3 },
                    quality: { type: "integer", minimum: 0, maximum: 3 },
                    latency: { type: "integer", minimum: 0, maximum: 3 },
                    history: { type: "integer", minimum: 0, maximum: 3 },
                    coverage: { type: "integer", minimum: 0, maximum: 3 },
                },
                required: ["existence", "accessibility", "quality", "latency", "history", "coverage"],
            },
            skipPermission: true,
            handler: async (args) => runCli([
                "assess", "data-readiness",
                "--existence", String(args.existence),
                "--accessibility", String(args.accessibility),
                "--quality", String(args.quality),
                "--latency", String(args.latency),
                "--history", String(args.history),
                "--coverage", String(args.coverage),
            ]),
        },

        // ── PMO Scoring ──────────────────────────────────────────────
        {
            name: "ai-kaizen-pmo-score",
            description: "Score an initiative on 7 PMO dimensions (1-5 each): business_value, measurability, data_readiness, change_risk, reversibility, compliance_risk, reuse_potential. Returns total score/40 and intake recommendation.",
            parameters: {
                type: "object",
                properties: {
                    business_value: { type: "integer", minimum: 1, maximum: 5 },
                    measurability: { type: "integer", minimum: 1, maximum: 5 },
                    data_readiness: { type: "integer", minimum: 1, maximum: 5 },
                    change_risk: { type: "integer", minimum: 1, maximum: 5 },
                    reversibility: { type: "integer", minimum: 1, maximum: 5 },
                    compliance_risk: { type: "integer", minimum: 1, maximum: 5 },
                    reuse_potential: { type: "integer", minimum: 1, maximum: 5 },
                },
                required: ["business_value", "measurability", "data_readiness", "change_risk", "reversibility", "compliance_risk", "reuse_potential"],
            },
            skipPermission: true,
            handler: async (args) => runCli([
                "pmo", "score",
                "-V", String(args.business_value),
                "-B", String(args.measurability),
                "-D", String(args.data_readiness),
                "-C", String(args.change_risk),
                "-R", String(args.reversibility),
                "-X", String(args.compliance_risk),
                "-P", String(args.reuse_potential),
            ]),
        },
        {
            name: "ai-kaizen-pmo-rank",
            description: "Show the ranked initiative backlog ordered by PMO score",
            parameters: { type: "object", properties: {} },
            skipPermission: true,
            handler: async () => runCli(["pmo", "rank"]),
        },

        // ── ROI Tracking ─────────────────────────────────────────────
        {
            name: "ai-kaizen-roi",
            description: "Record an ROI data point for the current initiative",
            parameters: {
                type: "object",
                properties: {
                    value_created: { type: "number", description: "Annualized value created ($)" },
                    value_captured: { type: "number", description: "Annualized value captured ($)" },
                    tco: { type: "number", description: "Total cost of ownership to date ($)" },
                    confidence: {
                        type: "string",
                        enum: ["projected", "estimated", "measured", "validated"],
                        description: "ROI confidence level (projected=±50%, validated=±10%)",
                    },
                },
                required: ["value_created", "value_captured", "tco", "confidence"],
            },
            skipPermission: true,
            handler: async (args) => runCli([
                "roi", "track",
                "--value-created", String(args.value_created),
                "--value-captured", String(args.value_captured),
                "--tco", String(args.tco),
                "--confidence", args.confidence,
            ]),
        },

        // ── CxO Executive Dashboard ──────────────────────────────────
        {
            name: "ai-kaizen-executive-snapshot",
            description: "Get the full CxO Executive Dashboard snapshot — 7 metric categories: ROI, pilot-to-scale pipeline, workforce readiness, governance, readiness gap, transformation depth, cost transparency",
            parameters: { type: "object", properties: {} },
            skipPermission: true,
            handler: async () => {
                const script = `
import json
from ai_kaizen.store.database import Store
from ai_kaizen.services.core import CxODashboardService
store = Store()
cxo = CxODashboardService(store)
snap = cxo.full_snapshot()
# Convert to serializable format
def clean(obj):
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean(i) for i in obj]
    return obj
print(json.dumps(clean(snap), indent=2, default=str))
store.close()
`;
                return runPython(script);
            },
        },
        {
            name: "ai-kaizen-workforce-assess",
            description: "Record a workforce readiness assessment — tracks AI fluency, training coverage, role redesign, and upskilling progress",
            parameters: {
                type: "object",
                properties: {
                    total_headcount: { type: "integer", description: "Total org headcount" },
                    ai_trained_count: { type: "integer", description: "Number of AI-trained employees" },
                    ai_fluency_score: { type: "number", description: "Org AI fluency score (0-5)" },
                    roles_redesigned: { type: "integer", description: "Number of roles redesigned for AI" },
                    roles_total: { type: "integer", description: "Total roles in scope" },
                    upskilling_completion_pct: { type: "number", description: "Upskilling completion %" },
                    notes: { type: "string", description: "Assessment notes" },
                },
                required: ["total_headcount", "ai_trained_count", "ai_fluency_score", "roles_redesigned", "roles_total", "upskilling_completion_pct"],
            },
            skipPermission: true,
            handler: async (args) => {
                const script = `
import json
from ai_kaizen.store.database import Store
from ai_kaizen.services.core import CxODashboardService
store = Store()
cxo = CxODashboardService(store)
result = cxo.record_workforce(
    total_headcount=${args.total_headcount},
    ai_trained_count=${args.ai_trained_count},
    ai_fluency_score=${args.ai_fluency_score},
    roles_redesigned=${args.roles_redesigned},
    roles_total=${args.roles_total},
    upskilling_completion_pct=${args.upskilling_completion_pct},
    notes=${JSON.stringify(args.notes || "")},
)
print(json.dumps(dict(result), indent=2, default=str))
store.close()
`;
                return runPython(script);
            },
        },

        // ── Portfolio Summary ────────────────────────────────────────
        {
            name: "ai-kaizen-portfolio",
            description: "Show portfolio-level summary: ROI, capacity, ranked backlog",
            parameters: { type: "object", properties: {} },
            skipPermission: true,
            handler: async () => runCli(["pmo", "dashboard"]),
        },

        // ── Export ───────────────────────────────────────────────────
        {
            name: "ai-kaizen-export",
            description: "Export the current initiative data as JSON",
            parameters: {
                type: "object",
                properties: {
                    format: { type: "string", enum: ["json", "markdown"], description: "Export format" },
                },
            },
            skipPermission: true,
            handler: async (args) => {
                const cmdArgs = ["export"];
                if (args.format) cmdArgs.push("--format", args.format);
                return runCli(cmdArgs);
            },
        },

        // ── Web Server ──────────────────────────────────────────────
        {
            name: "ai-kaizen-serve",
            description: "Start the AI-Kaizen web dashboard (returns URL). Use this when the user wants to see the visual dashboard.",
            parameters: {
                type: "object",
                properties: {
                    port: { type: "integer", description: "Port number (default 5001)" },
                },
            },
            skipPermission: true,
            handler: async (args) => {
                const port = args.port || 5001;
                // Fire and forget — start server in background
                const proc = execFile(
                    PYTHON,
                    ["-m", "ai_kaizen.web", "--port", String(port), "--host", "0.0.0.0"],
                    { cwd: "/Users/kevincrosby/ai-kaizen", detached: true, stdio: "ignore" },
                );
                proc.unref();
                return `AI-Kaizen web dashboard starting at http://localhost:${port}\n` +
                       `Executive Dashboard: http://localhost:${port}/executive\n` +
                       `Portfolio ROI: http://localhost:${port}/portfolio/roi`;
            },
        },
    ],
});

await session.log("AI-Kaizen toolkit loaded — 16 tools available");
