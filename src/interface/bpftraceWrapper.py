"""Thread-safe wrapper for executing bpftrace scripts.

This module provides a wrapper class around the bpftrace binary, handling
process management, logging, and error handling.
"""

from __future__ import annotations
import subprocess
import threading
import typer
import sys
from typing import List, Optional
from interface.dependencyInstaller import DependencyInstaller
from interface.config import settings


class BpftraceError(RuntimeError):
    """Exception raised for bpftrace-related errors."""
    pass


class BpftraceWrapper:
    """Thread-safe wrapper for running bpftrace scripts.

    Verifies dependencies on initialization, manages process lifecycle,
    and handles logging of bpftrace output. Thread-safe for concurrent
    invocations through internal locking.

    Attributes:
        _binary: Path to the bpftrace executable.
        _lock: Thread lock for synchronization.
        _cmd: Current bpftrace command being executed.
    """

    def __init__(
        self,
        bpftrace_binary: str = settings.default_bpftrace_binary_path,
    ):
        """Initialize the bpftrace wrapper.

        Verifies that bpftrace and required scripts are installed. Raises
        an exception if dependencies are not available.

        Args:
            bpftrace_binary: Path to the bpftrace executable.

        Raises:
            BpftraceError: If bpftrace is not installed.
        """
        installer = DependencyInstaller()
        if not installer.is_installed():
            typer.secho(
                "⚠️  Warning: 'bpftrace' or its scripts are not installed. "
                "Use 'dynamic-cbom install-dependencies' to install them.",
                fg=typer.colors.YELLOW
            )
            raise BpftraceError("'bpftrace' or its scripts are not installed")
        self._binary = bpftrace_binary
        self._lock = threading.Lock()
        self._cmd = []

    def start(
        self,
        script: str = settings.default_bpftrace_script_path,
        log_file: Optional[str] = settings.default_log_path,
        extra_args: Optional[List[str]] = None
    ) -> None:
        """Start bpftrace with the given script and arguments.

        Constructs and executes the bpftrace command with the specified script.
        The command is executed using sudo to ensure appropriate privileges.
        Output is logged to the specified file.

        Args:
            script: Path to the bpftrace script to execute.
            log_file: Optional path for the output log file.
            extra_args: Optional list of additional arguments to pass to bpftrace.

        Raises:
            BpftraceError: If the bpftrace command fails.
        """
        with self._lock:
            self._cmd = ["sudo", self._binary, script]

            if extra_args:
                self._cmd += extra_args

            if log_file:
                self._cmd += ["-o", log_file]

            typer.secho("Started bpftrace, stop it with Ctrl+C", fg=typer.colors.GREEN)

            try:
                with open("subprocess.log", "a") as logf:
                    subprocess.run(self._cmd, stdout=logf, stderr=sys.stderr, stdin=sys.stdin)
            except Exception as e:
                typer.secho(f"Error running bpftrace: {e}", fg=typer.colors.RED)
                raise BpftraceError(f"Error running bpftrace: {e}")


    
