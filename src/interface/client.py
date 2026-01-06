"""Command-line interface for DynamicCBOM.

Provides a Typer-based CLI for managing bpftrace cryptographic tracing,
log processing, and bill of materials generation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import typer

from interface.chartGenerator import ChartGenerator
from interface.config import settings
from interface.dependencyInstaller import DependencyInstaller
from interface.logPostProcessor import LogPostProcessor
from interface.options.attachByPid import AttachByPID
from interface.options.globalTrace import GlobalTrace
from interface.options.runNewTarget import RunNewTarget
from interface.options.runPythonTest import RunPythonTest

app = typer.Typer(no_args_is_help=True, add_completion=False)
installer = DependencyInstaller()


@app.command()
def banner() -> None:
    """Display the application banner."""
    try:
        art_text = Path("./docs/neoBanner.txt").read_text(encoding="utf-8")
    except OSError:
        art_text = ""

    if art_text:
        sys.stdout.write(art_text)
        if not art_text.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()


@app.command()
def install_dependencies() -> None:
    """Install required dependencies (bpftrace and scripts)."""
    installer.install()


@app.command()
def uninstall_dependencies() -> None:
    """Uninstall previously installed dependencies."""
    installer.uninstall()


@app.command()
def parse_log(
    log_file: str = typer.Argument(..., help="Path to the bpftrace log file"),
    output_path: str = typer.Option(
        settings.default_output_path, help="Output path for CBOM JSON file"
    ),
    verbose: bool = typer.Option(False, help="Enable verbose logging"),
) -> None:
    """Parse a bpftrace log file and generate a CBOM document."""
    try:
        log_processor = LogPostProcessor(yaml_path=settings.default_rules_path, verbose=verbose)
        log_processor.process_log(log_file, output_path=output_path)
        fig_path = Path(output_path).with_suffix(".png")
        log_processor.generate_wordCloud(log_file, output_path=fig_path)
    except Exception as e:
        typer.echo(f"Error parsing log file: {e}", err=True)
        raise typer.Exit(code=2)


@app.command()
def generate_chart(
    dyn_cbom_path: str = typer.Argument(..., help="Path to the dynamic CBOM JSON file"),
    ibm_cbom_path: str = typer.Option(None, help="Path to the IBM CBOM JSON file (optional)"),
    gt_cbom_path: str = typer.Argument(..., help="Path to the ground truth CBOM JSON file"),
    output_path: str = typer.Option(..., help="Output path for the generated chart"),
    verbose: bool = typer.Option(False, help="Enable verbose logging"),
) -> None:
    """Generate comparison charts from CBOM documents."""
    try:
        chart_gen = ChartGenerator(verbose=verbose)

        if ibm_cbom_path is not None:
            chart_gen.generate_comparisons(
                dyn_path=dyn_cbom_path,
                ibm_path=ibm_cbom_path,
                gt_path=gt_cbom_path,
                output_path=output_path,
            )
        else:
            chart_gen.generate_singular(
                dyn_path=dyn_cbom_path, gt_path=gt_cbom_path, output_path=output_path
            )
    except Exception as e:
        typer.echo(f"Error generating chart: {e}", err=True)
        raise typer.Exit(code=2)


@app.command()
def attach_pid(
    pid: int = typer.Argument(..., help="Process ID to attach to"),
    bpftrace_binary: str = typer.Option(
        settings.default_bpftrace_binary_path, help="Path to bpftrace executable"
    ),
    script: str = typer.Option(
        settings.default_bpftrace_script_path, help="Path to bpftrace script"
    ),
    log_file: str = typer.Option(settings.default_log_path, help="Output path for trace log"),
) -> None:
    """Attach bpftrace to an existing process by PID."""
    try:
        tracer = AttachByPID(bpftrace_binary=bpftrace_binary)
        tracer.run(pid=pid, script=script, log_file=log_file)
    except Exception as e:
        typer.echo(f"Error attaching to PID {pid}: {e}", err=True)
        raise typer.Exit(code=2)


@app.command()
def global_trace(
    bpftrace_binary: str = typer.Option(
        settings.default_bpftrace_binary_path, help="Path to bpftrace executable"
    ),
    script: str = typer.Option(
        settings.default_bpftrace_script_path, help="Path to bpftrace script"
    ),
    log_file: str = typer.Option(settings.default_log_path, help="Output path for trace log"),
) -> None:
    """Start a global bpftrace trace across the entire system."""
    try:
        tracer = GlobalTrace(bpftrace_binary=bpftrace_binary)
        tracer.run(script=script, log_file=log_file)
    except Exception as e:
        typer.echo(f"Error starting global trace: {e}", err=True)
        raise typer.Exit(code=2)


@app.command()
def run_new_target(
    cmd: List[str] = typer.Argument(
        ..., help="Command to run under bpftrace (use: -- cmd arg1 arg2 ...)"
    ),
    bpftrace_binary: str = typer.Option(
        settings.default_bpftrace_binary_path, help="Path to bpftrace executable"
    ),
    script: str = typer.Option(
        settings.default_bpftrace_script_path, help="Path to bpftrace script"
    ),
    log_file: str = typer.Option(settings.default_log_path, help="Output path for trace log"),
) -> None:
    """Run a new target command under bpftrace and trace it."""
    if not cmd:
        typer.echo("error: no command provided for run-new-target", err=True)
        raise typer.Exit(code=2)
    try:
        tracer = RunNewTarget(bpftrace_binary=bpftrace_binary)
        tracer.run(script=script, log_file=log_file, target_cmd=list(cmd))
    except Exception as e:
        typer.echo(f"Error running new target {' '.join(cmd)}: {e}", err=True)
        raise typer.Exit(code=2)


@app.command()
def run_python_test(
    test_program: str = typer.Argument(..., help="Path to the Python test program"),
    bpftrace_binary: str = typer.Option(
        settings.default_bpftrace_binary_path, help="Path to bpftrace executable"
    ),
    script: str = typer.Option(
        settings.default_bpftrace_script_path, help="Path to bpftrace script"
    ),
    log_file: str = typer.Option(settings.default_log_path, help="Output path for trace log"),
) -> None:
    """Run a Python test program under bpftrace and trace it."""
    try:
        tracer = RunPythonTest(bpftrace_binary=bpftrace_binary)
        tracer.run(script=script, log_file=log_file, test_program=test_program)
    except Exception as e:
        typer.echo(f"Error running python test {test_program}: {e}", err=True)
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
