"""AI-Kaizen CLI — main entry point."""

from __future__ import annotations

import logging
import sys

import click
from rich.console import Console

from ai_kaizen.logging_config import setup_logging
from ai_kaizen.metrics import metrics
from ai_kaizen.store.database import Store
from ai_kaizen.services.core import (
    InitiativeService, OutcomeService, EvalService,
    PDCAService, PMOService, DataReadinessService,
)

console = Console()
logger = logging.getLogger(__name__)


def _store() -> Store:
    return Store()


def _fmt_money(val: float) -> str:
    if val >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    elif val >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:.0f}"


class _KaizenGroup(click.Group):
    """Custom group that logs commands and catches unhandled exceptions."""

    def invoke(self, ctx):
        setup_logging()
        cmd_name = ctx.invoked_subcommand or "help"
        logger.debug("CLI command: %s", cmd_name)
        metrics.inc("cli_commands_total")
        metrics.inc("cli_commands_total", tags={"command": cmd_name})
        try:
            return super().invoke(ctx)
        except click.exceptions.Exit:
            raise
        except click.exceptions.Abort:
            raise
        except Exception as exc:
            metrics.inc("cli_errors_total")
            logger.error("Command '%s' failed: %s", cmd_name, exc, exc_info=True)
            console.print(f"\n[bold red]Error:[/] {exc}\n")
            sys.exit(1)


@click.group(cls=_KaizenGroup)
@click.version_option(package_name="ai-kaizen")
def cli():
    """AI-Kaizen: Eval-first AI transformation toolkit."""
    pass


# ─── init ────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.option("--description", "-d", default="", help="Initiative description")
@click.option("--severity", "-s", type=click.Choice(["S0", "S1", "S2", "S3"]), default="S2")
def init(name, description, severity):
    """Create a new transformation initiative."""
    store = _store()
    svc = InitiativeService(store)
    ini = svc.create(name, description, severity)
    store.close()
    console.print(f"\n[bold green]✓[/] Created initiative: [bold]{ini['name']}[/]")
    console.print(f"  ID:       {ini['id']}")
    console.print(f"  Severity: {ini['severity_class']}")
    console.print(f"  Loop:     {ini['current_loop']} → {ini['current_phase']}")
    console.print(f"  [dim]Auto-selected as current initiative[/]\n")


# ─── select ──────────────────────────────────────────────────────────────

@cli.command()
@click.argument("initiative_id", required=False)
def select(initiative_id):
    """Set the current working initiative."""
    store = _store()
    svc = InitiativeService(store)
    if not initiative_id:
        initiatives = svc.list_all()
        if not initiatives:
            console.print("[yellow]No initiatives found. Run 'ai-kaizen init' first.[/]")
            store.close()
            return
        console.print("\n[bold]Available initiatives:[/]\n")
        for ini in initiatives:
            current = store.get_current_initiative_id()
            marker = " ◀" if ini["id"] == current else ""
            console.print(f"  {ini['id']}  {ini['name']}  [{ini['status']}]{marker}")
        console.print()
        store.close()
        return
    ini = svc.select(initiative_id)
    store.close()
    console.print(f"\n[bold green]✓[/] Selected: [bold]{ini['name']}[/] ({ini['id']})\n")


# ─── assess ──────────────────────────────────────────────────────────────

@cli.group()
def assess():
    """Run assessments (data-readiness, cultural)."""
    pass


@assess.command("data-readiness")
@click.option("--existence", type=click.IntRange(0, 3), prompt="Existence (0-3): Does data exist in digital form?")
@click.option("--accessibility", type=click.IntRange(0, 3), prompt="Accessibility (0-3): API or structured export?")
@click.option("--quality", type=click.IntRange(0, 3), prompt="Quality (0-3): Clean, validated, consistent?")
@click.option("--latency", type=click.IntRange(0, 3), prompt="Latency (0-3): Event → queryable speed?")
@click.option("--history", type=click.IntRange(0, 3), prompt="History (0-3): Enough historical data?")
@click.option("--coverage", type=click.IntRange(0, 3), prompt="Coverage (0-3): All operating conditions?")
@click.option("--notes", default="", help="Assessment notes")
def data_readiness(existence, accessibility, quality, latency, history, coverage, notes):
    """Assess data readiness (Layer 0 scorecard)."""
    store = _store()
    ini_svc = InitiativeService(store)
    ini = ini_svc.require_current()
    dr_svc = DataReadinessService(store)
    result = dr_svc.assess(
        ini["id"],
        {"existence": existence, "accessibility": accessibility,
         "quality": quality, "latency": latency,
         "history": history, "coverage": coverage},
        notes,
    )
    store.close()

    total = result["total_score"]
    color = "green" if total >= 15 else "yellow" if total >= 10 else "red" if total >= 5 else "bold red"
    console.print(f"\n[bold]Data Readiness Assessment — {ini['name']}[/]\n")
    console.print(f"  Existence:     {existence}/3")
    console.print(f"  Accessibility: {accessibility}/3")
    console.print(f"  Quality:       {quality}/3")
    console.print(f"  Latency:       {latency}/3")
    console.print(f"  History:       {history}/3")
    console.print(f"  Coverage:      {coverage}/3")
    console.print(f"\n  [bold]Total: [{color}]{total}/18[/{color}][/]")
    console.print(f"  [bold]→ {result['recommendation']}[/]\n")


# ─── outcome ─────────────────────────────────────────────────────────────

@cli.group()
def outcome():
    """Define and track business outcomes."""
    pass


@outcome.command("set")
@click.option("--metric", required=True, prompt="Metric (what changes?)")
@click.option("--baseline", required=True, prompt="Baseline (current value)")
@click.option("--target", "target_range", required=True, prompt="Target range (min-max)")
@click.option("--scope", default="", help="Which process/line/department")
@click.option("--timeframe", default="", help="By when")
@click.option("--confidence", "confidence_target", default="", help="Statistical confidence target")
@click.option("--constraint", default="", help="What must NOT degrade")
def outcome_set(metric, baseline, target_range, scope, timeframe, confidence_target, constraint):
    """Define a business outcome for the current initiative."""
    store = _store()
    ini_svc = InitiativeService(store)
    ini = ini_svc.require_current()
    out_svc = OutcomeService(store)
    result = out_svc.create(
        ini["id"], metric, baseline, target_range,
        scope=scope, timeframe=timeframe,
        confidence_target=confidence_target, constraint_desc=constraint,
    )
    store.close()
    console.print(f"\n[bold green]✓[/] Outcome defined for [bold]{ini['name']}[/]")
    console.print(f"  Metric:   {metric}")
    console.print(f"  Baseline: {baseline}")
    console.print(f"  Target:   {target_range}\n")


@outcome.command("list")
def outcome_list():
    """List outcomes for the current initiative."""
    store = _store()
    ini = InitiativeService(store).require_current()
    outcomes = OutcomeService(store).list(ini["id"])
    store.close()
    if not outcomes:
        console.print("[yellow]No outcomes defined. Run 'ai-kaizen outcome set' first.[/]")
        return
    console.print(f"\n[bold]Outcomes — {ini['name']}[/]\n")
    for o in outcomes:
        console.print(f"  [{o['id']}] {o['metric']}: {o['baseline']} → {o['target_range']}")
        if o.get("scope"):
            console.print(f"    Scope: {o['scope']}")
    console.print()


# ─── eval ────────────────────────────────────────────────────────────────

@cli.group("eval")
def eval_cmd():
    """Manage eval suites and record results."""
    pass


@eval_cmd.command("scaffold")
@click.option("--level", required=True, type=click.Choice(["L0", "L1", "L2", "L2.5", "L3"]),
              prompt="Eval level")
@click.option("--description", "-d", default="")
def eval_scaffold(level, description):
    """Create an eval suite for the current initiative."""
    store = _store()
    ini = InitiativeService(store).require_current()
    suite = EvalService(store).create_suite(ini["id"], level, description)
    store.close()
    console.print(f"\n[bold green]✓[/] Eval suite created: {suite['id']}")
    console.print(f"  Level: {level}  Initiative: {ini['name']}\n")


@eval_cmd.command("record")
@click.option("--level", required=True, type=click.Choice(["L0", "L1", "L2", "L2.5", "L3"]))
@click.option("--total", required=True, type=int, prompt="Total assertions")
@click.option("--passed", required=True, type=int, prompt="Passed")
@click.option("--notes", default="")
@click.option("--commit", "commit_ref", default="")
def eval_record(level, total, passed, notes, commit_ref):
    """Record an eval run result."""
    store = _store()
    ini = InitiativeService(store).require_current()
    suites = EvalService(store).list_suites(ini["id"])
    suite = next((s for s in suites if s["level"] == level), None)
    if not suite:
        console.print(f"[yellow]No {level} suite found. Creating one...[/]")
        suite = EvalService(store).create_suite(ini["id"], level)
    run = EvalService(store).record_run(
        ini["id"], suite["id"], level, total, passed, notes, commit_ref,
    )
    store.close()
    rate = run["pass_rate"]
    color = "green" if rate >= 0.9 else "yellow" if rate >= 0.7 else "red"
    console.print(f"\n[bold green]✓[/] Eval run recorded")
    console.print(f"  Level: {level}  Pass rate: [{color}]{rate:.1%}[/{color}] ({passed}/{total})\n")


@eval_cmd.command("check")
def eval_check():
    """Check eval thresholds for the current initiative."""
    store = _store()
    ini = InitiativeService(store).require_current()
    checks = EvalService(store).check_thresholds(ini["id"], ini["severity_class"])
    store.close()
    console.print(f"\n[bold]Eval Threshold Check — {ini['name']} ({ini['severity_class']})[/]\n")
    for c in checks:
        icon = "✓" if c["passing"] else "✗" if c["has_data"] else "○"
        color = "green" if c["passing"] else "red" if c["has_data"] else "dim"
        status = f"{c['actual']:.0%}" if c["has_data"] else "no data"
        console.print(f"  [{color}]{icon}[/{color}] {c['level']}: {status} (required: {c['required']:.0%})")
    console.print()


# ─── pdca ────────────────────────────────────────────────────────────────

@cli.group()
def pdca():
    """Track PDCA loops and check gates."""
    pass


@pdca.command("start")
@click.argument("loop", type=click.Choice(["discovery", "validation", "scaling"]))
def pdca_start(loop):
    """Start a PDCA loop."""
    store = _store()
    ini_svc = InitiativeService(store)
    ini = ini_svc.require_current()
    ini_svc.advance_loop(ini["id"], loop)
    PDCAService(store).log_entry(ini["id"], loop, "plan", f"Started {loop} loop")
    store.close()
    console.print(f"\n[bold green]✓[/] Started [bold]{loop}[/] loop for {ini['name']}")
    console.print(f"  Phase: plan\n")


@pdca.command("log")
@click.option("--phase", required=True, type=click.Choice(["plan", "do", "check", "act"]))
@click.option("--note", required=True, prompt="Note")
def pdca_log(phase, note):
    """Log a PDCA entry."""
    store = _store()
    ini = InitiativeService(store).require_current()
    entry = PDCAService(store).log_entry(ini["id"], ini["current_loop"], phase, note)
    store.close()
    console.print(f"\n[bold green]✓[/] Logged [{ini['current_loop']}] {phase}: {note[:60]}...\n")


@pdca.command("gate")
def pdca_gate():
    """Check gate criteria for the current initiative."""
    store = _store()
    ini = InitiativeService(store).require_current()
    result = PDCAService(store).check_gate(ini["id"])
    store.close()

    color_map = {"passed": "green", "blocked": "red", "incomplete": "yellow"}
    icon_map = {"passed": "✓", "blocked": "✗", "incomplete": "○"}
    c = color_map.get(result["result"], "white")
    icon = icon_map.get(result["result"], "?")

    console.print(f"\n[bold]Gate Check — {ini['name']} ({ini['current_loop']})[/]\n")
    console.print(f"  [{c}]{icon} {result['result'].upper()}[/{c}]: {result['rationale']}")

    if result["kill_criteria"]:
        console.print(f"\n  [bold]Kill Criteria:[/]")
        for kc in result["kill_criteria"]:
            t = "🔴 TRIGGERED" if kc["triggered"] else "⚪ clear"
            console.print(f"    {t} — {kc['signal']}: {kc['current_value'] or '—'} (threshold: {kc['threshold']})")

    console.print(f"\n  [bold]Eval Thresholds:[/]")
    for ec in result["eval_checks"]:
        icon = "✓" if ec["passing"] else "✗" if ec["has_data"] else "○"
        col = "green" if ec["passing"] else "red" if ec["has_data"] else "dim"
        status = f"{ec['actual']:.0%}" if ec["has_data"] else "no data"
        console.print(f"    [{col}]{icon}[/{col}] {ec['level']}: {status} (required: {ec['required']:.0%})")
    console.print()


@pdca.command("history")
@click.option("--loop", type=click.Choice(["discovery", "validation", "scaling"]), default=None)
def pdca_history(loop):
    """Show PDCA entry history."""
    store = _store()
    ini = InitiativeService(store).require_current()
    entries = PDCAService(store).list_entries(ini["id"], loop)
    store.close()
    if not entries:
        console.print("[yellow]No PDCA entries yet.[/]")
        return
    console.print(f"\n[bold]PDCA History — {ini['name']}[/]\n")
    for e in entries:
        console.print(f"  [{e['loop']}] {e['phase'].upper():5s}  {e['note'][:70]}")
        console.print(f"  [dim]{e['created_at']}[/]")
    console.print()


# ─── pmo ─────────────────────────────────────────────────────────────────

@cli.group()
def pmo():
    """PMO: Portfolio management and prioritization."""
    pass


@pmo.command("score")
@click.option("--business-value", "-V", type=click.IntRange(1, 5), prompt="Business Value (1-5)")
@click.option("--measurability", "-B", type=click.IntRange(1, 5), prompt="Baseline Measurability (1-5)")
@click.option("--data", "-D", type=click.IntRange(1, 5), prompt="Data Readiness (1-5)")
@click.option("--change", "-C", type=click.IntRange(1, 5), prompt="Change Readiness (1-5)")
@click.option("--reversibility", "-R", type=click.IntRange(1, 5), prompt="Reversibility (1-5)")
@click.option("--compliance", "-X", type=click.IntRange(1, 5), prompt="Compliance Burden (1=heavy, 5=none)")
@click.option("--reuse", "-P", type=click.IntRange(1, 5), prompt="Platform Reuse (1-5)")
@click.option("--notes", default="")
def pmo_score(business_value, measurability, data, change, reversibility, compliance, reuse, notes):
    """Score the current initiative (7-dimension rubric)."""
    store = _store()
    ini = InitiativeService(store).require_current()
    result = PMOService(store).score_initiative(
        ini["id"],
        business_value=business_value,
        baseline_measurability=measurability,
        data_readiness=data,
        change_readiness=change,
        reversibility=reversibility,
        compliance_burden=compliance,
        platform_reuse=reuse,
        notes=notes,
    )
    store.close()

    total = result["total"]
    if total >= 30:
        rec, color = "FAST-TRACK", "green"
    elif total >= 22:
        rec, color = "QUALIFIED", "blue"
    elif total >= 15:
        rec, color = "CONDITIONAL", "yellow"
    else:
        rec, color = "DECLINE", "red"

    console.print(f"\n[bold]Initiative Score — {ini['name']}[/]\n")
    console.print(f"  V={business_value}×2  B={measurability}  D={data}  C={change}  R={reversibility}  X={compliance}  P={reuse}")
    console.print(f"\n  [bold]Total: [{color}]{total}/40[/{color}]  →  {rec}[/]\n")


@pmo.command("rank")
def pmo_rank():
    """Show prioritized initiative backlog."""
    store = _store()
    scores = PMOService(store).ranked_backlog()
    store.close()
    if not scores:
        console.print("[yellow]No initiatives scored yet. Run 'ai-kaizen pmo score' first.[/]")
        return
    console.print(f"\n[bold]Prioritized Backlog[/]\n")
    console.print(f"  {'Score':>5}  {'Rec':12s}  {'Loop':12s}  {'Status':10s}  Name")
    console.print(f"  {'─'*5}  {'─'*12}  {'─'*12}  {'─'*10}  {'─'*30}")
    for s in scores:
        total = s["total"]
        if total >= 30:
            rec = "Fast-Track"
        elif total >= 22:
            rec = "Qualified"
        elif total >= 15:
            rec = "Conditional"
        else:
            rec = "Decline"
        console.print(f"  {total:>5}/40  {rec:12s}  {s.get('current_loop', '—'):12s}  {s.get('status', '—'):10s}  {s['name']}")
    console.print()


@pmo.command("dashboard")
def pmo_dashboard():
    """Portfolio health dashboard."""
    store = _store()
    pmo_svc = PMOService(store)
    ini_svc = InitiativeService(store)

    active = ini_svc.list_all("active")
    all_ini = ini_svc.list_all()
    killed = [i for i in all_ini if i["status"] == "killed"]
    capacity = pmo_svc.capacity_check()
    roi_summary = pmo_svc.portfolio_summary()

    store.close()

    console.print(f"\n[bold]═══ AI-KAIZEN PORTFOLIO DASHBOARD ═══[/]\n")
    wip_color = "green" if capacity["within_limit"] else "red"
    console.print(f"  Active: [{wip_color}]{capacity['active_count']}/{capacity['wip_limit']}[/{wip_color}] (WIP limit)    Killed: {len(killed)}    Total: {len(all_ini)}")
    console.print()

    if active:
        console.print(f"  [bold]Active Initiatives:[/]")
        for ini in active:
            console.print(f"    {ini['severity_class']} {ini['name']}")
            console.print(f"       [dim]{ini['current_loop']} → {ini['current_phase']}  |  Autonomy: {ini['autonomy_level']}[/]")
        console.print()

    # Loop distribution
    disc = capacity["by_loop"].get("discovery", [])
    val = capacity["by_loop"].get("validation", [])
    scale = capacity["by_loop"].get("scaling", [])
    console.print(f"  [bold]Loop Distribution:[/]  Discovery: {len(disc)}  Validation: {len(val)}  Scaling: {len(scale)}")

    # ROI
    if roi_summary.get("initiative_count") and roi_summary["initiative_count"] > 0:
        console.print(f"\n  [bold]Portfolio ROI:[/]")
        console.print(f"    Value Created:  {_fmt_money(roi_summary.get('total_value_created', 0) or 0)}")
        console.print(f"    Value Captured: {_fmt_money(roi_summary.get('total_value_captured', 0) or 0)}")
        console.print(f"    Total TCO:      {_fmt_money(roi_summary.get('total_tco', 0) or 0)}")
        console.print(f"    Net Value:      {_fmt_money(roi_summary.get('total_net_value', 0))}")
        cr = roi_summary.get("capture_rate", 0)
        console.print(f"    Capture Rate:   {cr:.0%}")
    console.print()


@pmo.command("capacity")
@click.option("--wip-limit", default=5, help="Max active initiatives")
def pmo_capacity(wip_limit):
    """Check WIP limits and bottlenecks."""
    store = _store()
    result = PMOService(store).capacity_check(wip_limit)
    store.close()
    color = "green" if result["within_limit"] else "red"
    console.print(f"\n[bold]Capacity Check[/]\n")
    console.print(f"  Active: [{color}]{result['active_count']}/{result['wip_limit']}[/{color}]")
    for loop, names in result["by_loop"].items():
        console.print(f"  {loop.capitalize():12s}: {len(names)}")
        for n in names:
            console.print(f"    • {n}")
    console.print()


@pmo.command("estimate")
@click.option("--size", required=True, type=click.Choice(["S", "M", "L", "XL"]), prompt="T-shirt size")
def pmo_estimate(size):
    """Estimate effort/cost by t-shirt size."""
    store = _store()
    result = PMOService(store).estimate_effort(size)
    store.close()
    console.print(f"\n[bold]Effort Estimate — Size {size}[/]\n")
    d = result["discovery"]
    v = result["validation"]
    t = result["year1_tco"]
    console.print(f"  Discovery:   {_fmt_money(d[0])} – {_fmt_money(d[1])}")
    console.print(f"  Validation:  {_fmt_money(v[0])} – {_fmt_money(v[1])}")
    console.print(f"  Year 1 TCO:  {_fmt_money(t[0])} – {_fmt_money(t[1])}")
    console.print()


# ─── roi ─────────────────────────────────────────────────────────────────

@cli.group()
def roi():
    """Track ROI and value realization."""
    pass


@roi.command("track")
@click.option("--value-created", type=float, required=True, prompt="Annualized value created ($)")
@click.option("--value-captured", type=float, required=True, prompt="Annualized value captured ($)")
@click.option("--tco", "tco_to_date", type=float, required=True, prompt="TCO to date ($)")
@click.option("--confidence", type=click.Choice(["projected", "estimated", "measured", "validated"]),
              default="projected", prompt="Confidence level")
@click.option("--notes", default="")
def roi_track(value_created, value_captured, tco_to_date, confidence, notes):
    """Record an ROI data point."""
    store = _store()
    ini = InitiativeService(store).require_current()
    result = PMOService(store).record_roi(
        ini["id"], confidence, value_created, value_captured, tco_to_date, notes,
    )
    store.close()
    net = value_captured - tco_to_date
    cr = value_captured / value_created if value_created else 0
    color = "green" if net > 0 else "red"
    console.print(f"\n[bold green]✓[/] ROI recorded for {ini['name']}")
    console.print(f"  Confidence:    {confidence}")
    console.print(f"  Created:       {_fmt_money(value_created)}")
    console.print(f"  Captured:      {_fmt_money(value_captured)} ({cr:.0%} capture rate)")
    console.print(f"  TCO:           {_fmt_money(tco_to_date)}")
    console.print(f"  [{color}]Net Value:     {_fmt_money(net)}[/{color}]\n")


@roi.command("portfolio")
def roi_portfolio():
    """Show portfolio-level ROI summary."""
    store = _store()
    summary = PMOService(store).portfolio_summary()
    store.close()
    if not summary.get("initiative_count") or summary["initiative_count"] == 0:
        console.print("[yellow]No ROI data recorded yet.[/]")
        return
    console.print(f"\n[bold]Portfolio ROI Summary[/]\n")
    console.print(f"  Initiatives:     {summary['initiative_count']}")
    console.print(f"  Value Created:   {_fmt_money(summary.get('total_value_created', 0) or 0)}")
    console.print(f"  Value Captured:  {_fmt_money(summary.get('total_value_captured', 0) or 0)}")
    console.print(f"  Total TCO:       {_fmt_money(summary.get('total_tco', 0) or 0)}")
    net = summary.get("total_net_value", 0)
    color = "green" if net > 0 else "red"
    console.print(f"  [{color}]Net Value:       {_fmt_money(net)}[/{color}]")
    console.print(f"  Capture Rate:    {summary.get('capture_rate', 0):.0%}")
    console.print(f"  Portfolio ROI:   {summary.get('portfolio_roi', 0):.1%}")
    console.print()


# ─── status ──────────────────────────────────────────────────────────────

@cli.command()
@click.option("--initiative", "-i", default=None, help="Deep-dive into specific initiative")
def status(initiative):
    """Portfolio dashboard or initiative deep-dive."""
    store = _store()
    if initiative:
        _status_detail(store, initiative)
    else:
        _status_overview(store)
    store.close()


def _status_overview(store: Store):
    ini_svc = InitiativeService(store)
    all_ini = ini_svc.list_all()
    if not all_ini:
        console.print("[yellow]No initiatives. Run 'ai-kaizen init' to create one.[/]")
        return
    current_id = store.get_current_initiative_id()
    console.print(f"\n[bold]═══ AI-KAIZEN STATUS ═══[/]\n")
    console.print(f"  {'':2s} {'Sev':4s} {'Loop':12s} {'Phase':7s} {'Auto':4s} {'Status':10s} Name")
    console.print(f"  {'':2s} {'─'*4} {'─'*12} {'─'*7} {'─'*4} {'─'*10} {'─'*30}")
    for ini in all_ini:
        marker = "▶" if ini["id"] == current_id else " "
        console.print(
            f"  {marker} {ini['severity_class']:4s} {ini['current_loop']:12s} "
            f"{ini['current_phase']:7s} {ini['autonomy_level']:4s} {ini['status']:10s} {ini['name']}"
        )
    console.print()


def _status_detail(store: Store, initiative_id: str):
    ini = store.get_initiative(initiative_id)
    if not ini:
        console.print(f"[red]Initiative '{initiative_id}' not found.[/]")
        return

    console.print(f"\n[bold]═══ {ini['name']} ═══[/]\n")
    console.print(f"  ID:        {ini['id']}")
    console.print(f"  Severity:  {ini['severity_class']}")
    console.print(f"  Autonomy:  {ini['autonomy_level']}")
    console.print(f"  Loop:      {ini['current_loop']} → {ini['current_phase']}")
    console.print(f"  Status:    {ini['status']}")

    # Outcomes
    outcomes = store.list_outcomes(ini["id"])
    if outcomes:
        console.print(f"\n  [bold]Outcomes:[/]")
        for o in outcomes:
            console.print(f"    {o['metric']}: {o['baseline']} → {o['target_range']}")

    # Data readiness
    dr = store.get_data_readiness(ini["id"])
    if dr:
        total = dr["existence"] + dr["accessibility"] + dr["quality"] + dr["latency"] + dr["history"] + dr["coverage"]
        console.print(f"\n  [bold]Data Readiness:[/] {total}/18")

    # Eval suites + latest runs
    suites = store.list_eval_suites(ini["id"])
    if suites:
        console.print(f"\n  [bold]Eval Suites:[/]")
        for s in suites:
            run = store.latest_eval_run(ini["id"], s["level"])
            if run:
                rate = run["pass_rate"]
                color = "green" if rate >= 0.9 else "yellow" if rate >= 0.7 else "red"
                console.print(f"    {s['level']}: [{color}]{rate:.0%}[/{color}] ({run['passed']}/{run['total']})")
            else:
                console.print(f"    {s['level']}: [dim]no runs yet[/]")

    # Score
    score = store.get_initiative_score(ini["id"])
    if score:
        console.print(f"\n  [bold]PMO Score:[/] {score['total']}/40")

    # Latest ROI
    roi_entry = store.latest_roi(ini["id"])
    if roi_entry:
        net = roi_entry["value_captured"] - roi_entry["tco_to_date"]
        color = "green" if net > 0 else "red"
        console.print(f"\n  [bold]ROI ({roi_entry['confidence']}):[/]")
        console.print(f"    Created: {_fmt_money(roi_entry['value_created'])}  "
                      f"Captured: {_fmt_money(roi_entry['value_captured'])}  "
                      f"TCO: {_fmt_money(roi_entry['tco_to_date'])}  "
                      f"[{color}]Net: {_fmt_money(net)}[/{color}]")

    # Kill criteria
    criteria = store.list_kill_criteria(ini["id"])
    if criteria:
        console.print(f"\n  [bold]Kill Criteria:[/]")
        for kc in criteria:
            icon = "🔴" if kc["triggered"] else "⚪"
            console.print(f"    {icon} {kc['signal']}: {kc['current_value'] or '—'} (threshold: {kc['threshold']})")

    console.print()


# ─── export ──────────────────────────────────────────────────────────────

@cli.command()
@click.option("--format", "fmt", type=click.Choice(["markdown", "json"]), default="markdown")
def export(fmt):
    """Export initiative report."""
    store = _store()
    ini = InitiativeService(store).require_current()
    outcomes = OutcomeService(store).list(ini["id"])
    suites = EvalService(store).list_suites(ini["id"])
    entries = PDCAService(store).list_entries(ini["id"])
    dr = DataReadinessService(store).get(ini["id"])
    score = store.get_initiative_score(ini["id"])
    roi_entry = store.latest_roi(ini["id"])

    if fmt == "json":
        import json
        data = {
            "initiative": ini,
            "outcomes": outcomes,
            "eval_suites": suites,
            "pdca_entries": entries,
            "data_readiness": dr,
            "score": score,
            "roi": roi_entry,
        }
        click.echo(json.dumps(data, indent=2, default=str))
        return

    # Markdown
    lines = [
        f"# {ini['name']}",
        f"\n**ID:** {ini['id']}  ",
        f"**Severity:** {ini['severity_class']}  **Autonomy:** {ini['autonomy_level']}  ",
        f"**Loop:** {ini['current_loop']} → {ini['current_phase']}  **Status:** {ini['status']}",
    ]
    if outcomes:
        lines.append("\n## Outcomes\n")
        for o in outcomes:
            lines.append(f"- **{o['metric']}**: {o['baseline']} → {o['target_range']}")
    if dr:
        lines.append(f"\n## Data Readiness: {dr['total_score']}/18\n")
        lines.append(f"→ {dr['recommendation']}")
    if score:
        lines.append(f"\n## PMO Score: {score['total']}/40")
    if suites:
        lines.append("\n## Eval Suites\n")
        lines.append("| Level | Latest Pass Rate |")
        lines.append("|-------|-----------------|")
        for s in suites:
            run = store.latest_eval_run(ini["id"], s["level"]) if hasattr(store, 'latest_eval_run') else None
            rate = f"{run['pass_rate']:.0%}" if run else "—"
            lines.append(f"| {s['level']} | {rate} |")
    if entries:
        lines.append("\n## PDCA History\n")
        for e in entries:
            lines.append(f"- **[{e['loop']}] {e['phase']}**: {e['note']}")
    if roi_entry:
        net = roi_entry["value_captured"] - roi_entry["tco_to_date"]
        lines.append(f"\n## ROI ({roi_entry['confidence']})\n")
        lines.append(f"- Created: ${roi_entry['value_created']:,.0f}")
        lines.append(f"- Captured: ${roi_entry['value_captured']:,.0f}")
        lines.append(f"- TCO: ${roi_entry['tco_to_date']:,.0f}")
        lines.append(f"- Net: ${net:,.0f}")

    click.echo("\n".join(lines))


# ─── serve ──────────────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default="127.0.0.1", help="Bind address (default: localhost only)")
@click.option("--port", default=5000, type=int, help="Port to listen on")
@click.option("--debug/--no-debug", default=False, help="Enable debug mode")
def serve(host, port, debug):
    """Start the AI-Kaizen web UI."""
    from ai_kaizen.web.app import create_app

    app = create_app()
    console.print(f"\n  ⚡ AI-Kaizen Web UI")
    console.print(f"  → http://{host}:{port}")
    console.print(f"  Press Ctrl+C to stop\n")
    app.run(host=host, port=port, debug=debug)


# ─── metrics ────────────────────────────────────────────────────────────

@cli.command("metrics")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def metrics_cmd(as_json):
    """Show process metrics snapshot (counters, histograms)."""
    import json as _json
    snap = metrics.snapshot()
    if as_json:
        click.echo(_json.dumps(snap, indent=2))
    else:
        console.print(f"\n[bold]Process Metrics[/]  (uptime: {snap['uptime_seconds']}s)\n")
        if snap["counters"]:
            console.print("[bold]Counters:[/]")
            for k, v in sorted(snap["counters"].items()):
                console.print(f"  {k}: {v}")
        if snap["histograms"]:
            console.print("\n[bold]Histograms:[/]")
            for k, v in sorted(snap["histograms"].items()):
                line = f"  {k}: count={v['count']} min={v['min']}ms avg={v['avg']}ms max={v['max']}ms p50={v['p50']}ms"
                if v.get("p95"):
                    line += f" p95={v['p95']}ms"
                console.print(line)
        if not snap["counters"] and not snap["histograms"]:
            console.print("  [dim]No metrics recorded yet[/]")
        console.print()


if __name__ == "__main__":
    cli()
