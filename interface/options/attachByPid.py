"""AttachByPID: helper to run bpftrace attached to a specific process ID.

This module provides a small wrapper around BpftraceWrapper that starts bpftrace
with the "-p <pid>" option so the script attaches to a running process.
"""
from interface.bpftraceWrapper import BpftraceWrapper
from typing import Optional
from interface.config import settings




class AttachByPID(BpftraceWrapper):
    """Wrapper to start bpftrace attached to a PID.

    Inherits BpftraceWrapper which handles process management and logging.
    """

    def __init__(
        self, 
        bpftrace_binary: str = settings.default_bpftrace_binary_path,
    ):
        # Pass the path to the bpftrace binary to the base wrapper.
        super().__init__(
            bpftrace_binary=bpftrace_binary,
        )

    def run(
        self, 
        pid: int,
        script: str = settings.default_bpftrace_script_path,
        log_file: Optional[str] = settings.default_log_path
    ):
        """Start bpftrace attaching to the given PID.

        Args:
            pid: Process ID to attach to.
            script: Path to the bpftrace script to run (defaults from settings).
            log_file: Optional path for logging bpftrace output (defaults from settings).
        """
        # Use the base class start() method and add the "-p <pid>" extra arg
        # so the bpftrace session attaches to the target process.
        self.start(
            script=script,
            log_file=log_file,
            extra_args=["-p", str(pid)]
        )