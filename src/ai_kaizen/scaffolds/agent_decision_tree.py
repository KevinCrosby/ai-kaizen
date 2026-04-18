"""'Should this be an agent?' decision tree — guided assessment."""

from __future__ import annotations

QUESTIONS = [
    {
        "id": "repetitive",
        "question": "Is the task repetitive (happens >10x/week)?",
        "weight": 2,
        "guidance": "Agents excel at high-frequency repetitive tasks where human fatigue causes errors.",
    },
    {
        "id": "deterministic",
        "question": "Can success be measured deterministically (clear pass/fail)?",
        "weight": 3,
        "guidance": "Without deterministic evals, you can't verify agent behavior. This is the #1 predictor of agent success.",
    },
    {
        "id": "data_available",
        "question": "Is training/reference data readily available?",
        "weight": 2,
        "guidance": "Agents need data to learn from. No data = no agent. Check your Data Readiness score.",
    },
    {
        "id": "reversible",
        "question": "Are agent actions easily reversible?",
        "weight": 2,
        "guidance": "Start with reversible actions (read, classify, recommend) before irreversible ones (delete, approve, send).",
    },
    {
        "id": "human_bottleneck",
        "question": "Is a human bottleneck causing delays?",
        "weight": 1,
        "guidance": "If humans aren't the bottleneck, an agent won't help. Look for queues, backlogs, or wait times.",
    },
    {
        "id": "structured_io",
        "question": "Are inputs and outputs well-structured?",
        "weight": 2,
        "guidance": "Structured I/O (forms, APIs, databases) is much easier to agent-ify than unstructured (free text, images).",
    },
    {
        "id": "safety_low",
        "question": "Is the safety risk low (S2-S3, not S0)?",
        "weight": 2,
        "guidance": "S0 tasks need extensive L0/L1/L2 evals before any autonomy. Start agent pilots on S2-S3 tasks.",
    },
    {
        "id": "existing_process",
        "question": "Is there a documented process today?",
        "weight": 1,
        "guidance": "Undocumented tribal knowledge is hard to encode. Document the process first, then automate.",
    },
]

THRESHOLDS = {
    "strong_yes": 12,   # >= 12: strong candidate for an agent
    "maybe": 7,         # 7-11: possible, but address gaps first
    # < 7: probably not an agent task
}


def run_assessment(answers: dict[str, bool]) -> dict:
    """
    Run the decision tree assessment.

    Args:
        answers: dict mapping question ID to True/False

    Returns:
        dict with score, max_score, recommendation, and per-question results
    """
    results = []
    score = 0
    max_score = 0

    for q in QUESTIONS:
        qid = q["id"]
        answered_yes = answers.get(qid, False)
        points = q["weight"] if answered_yes else 0
        score += points
        max_score += q["weight"]
        results.append({
            "id": qid,
            "question": q["question"],
            "answer": answered_yes,
            "points": points,
            "max_points": q["weight"],
            "guidance": q["guidance"],
        })

    if score >= THRESHOLDS["strong_yes"]:
        recommendation = "STRONG YES"
        summary = "This is a strong candidate for an agentic workflow. Proceed with eval scaffolding."
    elif score >= THRESHOLDS["maybe"]:
        recommendation = "MAYBE"
        gaps = [r for r in results if not r["answer"] and r["max_points"] >= 2]
        gap_list = ", ".join(r["id"] for r in gaps)
        summary = f"Possible agent candidate, but address gaps first: {gap_list}"
    else:
        recommendation = "NOT YET"
        summary = "This task isn't ready for an agent. Focus on process documentation, data readiness, and eval design first."

    return {
        "score": score,
        "max_score": max_score,
        "percentage": score / max_score if max_score else 0,
        "recommendation": recommendation,
        "summary": summary,
        "results": results,
    }


def render_assessment_markdown(assessment: dict) -> str:
    """Render assessment results as markdown."""
    lines = [
        f"# 🤖 Should This Be an Agent?\n",
        f"**Score: {assessment['score']}/{assessment['max_score']}** — "
        f"**{assessment['recommendation']}**\n",
        f"> {assessment['summary']}\n",
        "| # | Question | Answer | Points |",
        "|---|----------|--------|--------|",
    ]
    for i, r in enumerate(assessment["results"], 1):
        check = "✅" if r["answer"] else "❌"
        lines.append(f"| {i} | {r['question']} | {check} | {r['points']}/{r['max_points']} |")

    # Add guidance for "no" answers
    nos = [r for r in assessment["results"] if not r["answer"]]
    if nos:
        lines.append("\n## Gaps to Address\n")
        for r in nos:
            lines.append(f"- **{r['question']}** — {r['guidance']}")

    return "\n".join(lines)
