"""
Wrapper to run a Python test program under bpftrace.

Provides RunPythonTest which extends BpftraceWrapper and invokes bpftrace
with the -c option to run a given Python test program while tracing.
"""

import os
from typing import Optional

from interface.bpftraceWrapper import BpftraceWrapper
from interface.config import settings


class RunPythonTest(BpftraceWrapper):
    """
    Helper to launch a Python test program under bpftrace.

    Parameters:
    - bpftrace_binary: path to the bpftrace executable (defaults from settings)
    """

    def __init__(
        self,
        bpftrace_binary: str = settings.default_bpftrace_binary_path,
    ):
        # Initialize parent wrapper with the bpftrace binary path
        super().__init__(
            bpftrace_binary=bpftrace_binary,
        )

    def run(
        self,
        test_program: str,
        script: str = settings.default_bpftrace_script_path,
        log_file: Optional[str] = settings.default_log_path,
    ):
        """
        Run the given Python test program under bpftrace.

        Args:
        - test_program: path to the Python test program to execute.
        - script: bpftrace script path to use for tracing.
        - log_file: optional path to write trace/log output.

        Raises:
        - FileNotFoundError: if the test_program path does not exist.
        """
        # Ensure the test program exists before invoking bpftrace
        if not os.path.exists(test_program):
            raise FileNotFoundError(f"Test program not found: {test_program}")

        # Start bpftrace with the provided script and log file.
        # Pass "-c /usr/bin/python3 <test_program>" so bpftrace runs the test under the Python interpreter.
        self.start(
            script=script, log_file=log_file, extra_args=["-c", f"/usr/bin/python3 {test_program}"]
        )
