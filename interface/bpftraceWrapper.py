from __future__ import annotations
import subprocess
import threading
import typer
import sys
from typing import List, Optional
from interface.dependencyInstaller import DependencyInstaller
from interface.config import settings


class BpftraceError(RuntimeError):
    pass

class BpftraceWrapper:
    """
    Thread-safe wrapper for running bpftrace via sudo.

    Verifies dependencies on init. 
    Use start(script, log_file, extra_args) to run a bpftrace script (blocking call).
    """
    def __init__(
        self, 
        bpftrace_binary: str = settings.default_bpftrace_binary_path,
    ):
        installer = DependencyInstaller()
        if not installer.is_installed():
            typer.secho("⚠️  Warning: 'bpftrace' or its scripts are not installed, use 'dynamic-cbom install-dependencies' to install them.", fg=typer.colors.YELLOW)
            raise BpftraceError("'bpftrace' or its scripts are not installed")
        self._binary = bpftrace_binary
        self._lock = threading.Lock()
        self._cmd = []

    
    
    def start(
        self, 
        script: str = settings.default_bpftrace_script_path, 
        log_file: Optional[str] = settings.default_log_path,
        extra_args: Optional[List[str]] = None
    ):
        with self._lock:
            self._cmd = ["sudo", self._binary, script]
            
            if extra_args:
                self._cmd += extra_args

            if log_file:
                self._cmd += ["-o", log_file]

            
            typer.secho("Started bpftrace, stop it with Ctrl+C", fg=typer.colors.GREEN)

            try:
                # every time rewrite the log file
                with open("subprocess.log", "a") as logf:
                    subprocess.run(self._cmd, stdout=logf, stderr=sys.stderr, stdin=sys.stdin)
            except Exception as e:
                typer.secho(f"Error running bpftrace: {e}", fg=typer.colors.RED)
                raise BpftraceError(f"Error running bpftrace: {e}")


    
