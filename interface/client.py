"""Typer-based CLI for the dynamic-cbom"""

from __future__ import annotations
from typing import List

import typer
import sys
from pathlib import Path

from interface.options.attachByPid import AttachByPID
from interface.options.globalTrace import GlobalTrace
from interface.options.runNewTarget import RunNewTarget
from interface.options.runPythonTest import RunPythonTest
from interface.logPostProcessor import LogPostProcessor
from interface.chartGenerator import ChartGenerator

from interface.dependencyInstaller import DependencyInstaller
from interface.config import settings


app = typer.Typer(
    no_args_is_help=True,        # optional: running `mytool` alone also shows help
	add_completion=False    # disable `mytool --show-completion` command
)
installer = DependencyInstaller()

@app.command()
def banner() -> None:
    try:
        art_text = Path("./docs/neoBanner.txt").read_text(encoding="utf-8")
    except OSError:
        art_text = ""

    if art_text:
        # Always preserve colors exactly as encoded in the file.
        # If the file has no ANSI codes, it will render with the terminal's default color.
        sys.stdout.write(art_text)
        if not art_text.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()


@app.command()
def install_dependencies() -> None:
	"""Install required dependencies using the DependencyInstaller."""
	installer.install()
 
@app.command()
def uninstall_dependencies() -> None:
	"""Uninstall previously installed dependencies using the DependencyInstaller."""
	installer.uninstall()

@app.command()
def parse_log(
	log_file: str = typer.Argument(..., help="path to the bpftrace log file to parse"),
	output_path: str = typer.Option(settings.default_output_path, help="path to save the generated CBOM JSON file"),
	verbose: bool = typer.Option(False, help="Enable verbose output")
) -> None:
	"""Parse a bpftrace log file and process it with Postprocessor."""
	try:
		logPostProcessor = LogPostProcessor(
			yaml_path=settings.default_rules_path,
			verbose=verbose
		)
		logPostProcessor.process_log(log_file, output_path=output_path)
		fig_path = Path(output_path).with_suffix('.png')
		logPostProcessor.generate_wordCloud(log_file, output_path=fig_path)
	except Exception as e:
		typer.echo(f"Error parsing log file: {e}", err=True)
		raise typer.Exit(code=2)

@app.command()
def generate_chart(
	dyn_cbom_path: str = typer.Argument(..., help="Path to the dynamic CBOM JSON file"),
	ibm_cbom_path: str = typer.Option(None, help="Path to the IBM CBOM JSON file"),
	gt_cbom_path: str = typer.Argument(..., help="Path to the ground truth CBOM JSON file"),
	output_path: str = typer.Option(..., help="Path to save the generated chart"),
	verbose: bool = typer.Option(False, help="Enable verbose output")
) -> None:
	"""Generate comparison charts from CBOM JSON files."""
	try:
		chartGen = ChartGenerator(verbose=verbose)
		
		if ibm_cbom_path is not None:
			chartGen.generate_comparisons(
				dyn_path=dyn_cbom_path,
				ibm_path=ibm_cbom_path,
				gt_path=gt_cbom_path,
				output_path=output_path
			)
		else:
			chartGen.generate_singular(
				dyn_path=dyn_cbom_path,
				gt_path=gt_cbom_path,
				output_path=output_path
			)
	except Exception as e:
		typer.echo(f"Error generating chart: {e}", err=True)
		raise typer.Exit(code=2)


@app.command()
def attach_pid(
	pid: int = typer.Argument(..., help="Process ID to attach the bpftrace script to."),
	bpftrace_binary: str = typer.Option(settings.default_bpftrace_binary_path, help="Path to the bpftrace executable"),
	script: str = typer.Option(settings.default_bpftrace_script_path, help="Path to the bpftrace script to run."),
	log_file: str = typer.Option(settings.default_log_path, help="Path where the trace log will be written."),
) -> None:
	"""Attach bpftrace to an existing process by PID and collect a trace."""
	try:
		obj = AttachByPID(bpftrace_binary=bpftrace_binary)
		obj.run(
			pid=pid,
			script=script,
			log_file=log_file
		)
	except Exception as e:
		typer.echo(f"Error attaching to PID {pid}: {e}", err=True)
		raise typer.Exit(code=2)


@app.command()
def global_trace(
	bpftrace_binary: str = typer.Option(settings.default_bpftrace_binary_path, help="Path to the bpftrace executable"),
	script: str = typer.Option(settings.default_bpftrace_script_path, help="Path to the bpftrace script to run."),
	log_file: str = typer.Option(settings.default_log_path, help="Path where the trace log will be written."),
) -> None:
	"""Start a global bpftrace collection across the system."""
	try:
		obj = GlobalTrace(bpftrace_binary=bpftrace_binary)
		obj.run(
			script=script,
			log_file=log_file
		)
	except Exception as e:
		typer.echo(f"Error starting global trace: {e}", err=True)
		raise typer.Exit(code=2)


@app.command()
def run_new_target(
	cmd: List[str] = typer.Argument(..., help="command to run (provide as: -- cmd arg1 arg2 ...) as the traced target"),
	bpftrace_binary: str = typer.Option(settings.default_bpftrace_binary_path, help="Path to the bpftrace executable"),
	script: str = typer.Option(settings.default_bpftrace_script_path, help="Path to the bpftrace script to run."),
	log_file: str = typer.Option(settings.default_log_path, help="Path where the trace log will be written."),
) -> None:
	"""Run a new target command under bpftrace and collect its trace."""
	if not cmd:
		typer.echo("error: no command provided for run-new-target", err=True)
		raise typer.Exit(code=2)
	try:
		obj = RunNewTarget(bpftrace_binary=bpftrace_binary)
		obj.run(
			script=script,
			log_file=log_file,
			target_cmd=list(cmd)
		)
	except Exception as e:
		typer.echo(f"Error running new target {' '.join(cmd)}: {e}", err=True)
		raise typer.Exit(code=2)

@app.command()
def run_python_test(
	test_program: str = typer.Argument(..., help="path to the python test program"),
	bpftrace_binary: str = typer.Option(settings.default_bpftrace_binary_path, help="Path to the bpftrace executable"),
	script: str = typer.Option(settings.default_bpftrace_script_path, help="Path to the bpftrace script to run."),
	log_file: str = typer.Option(settings.default_log_path, help="Path where the trace log will be written."),
) -> None:
	"""Run a Python test program under bpftrace and collect its trace."""
	try:
		obj = RunPythonTest(bpftrace_binary=bpftrace_binary)
		obj.run(
			script=script,
			log_file=log_file,
			test_program=test_program
		)
		
	except Exception as e:
		typer.echo(f"Error running python test {test_program}: {e}", err=True)
		raise typer.Exit(code=2)


if __name__ == "__main__":
	app()
