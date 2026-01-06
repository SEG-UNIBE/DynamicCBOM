"""
Wrapper to run a new target command under a bpftrace script.

Provides a small helper class around BpftraceWrapper to start bpftrace
with a target command (using -c "command args...") and sensible defaults
from the project's settings.
"""

from interface.bpftraceWrapper import BpftraceWrapper
from typing import Sequence, Optional
from interface.config import settings


class RunNewTarget(BpftraceWrapper):
    """Run a new process under bpftrace using a supplied command sequence.

    This class delegates to BpftraceWrapper.start(...) and constructs the
    appropriate extra_args for running a command (i.e. -c "cmd ...").
    """

    def __init__(
        self,
        bpftrace_binary: str = settings.default_bpftrace_binary_path,
    ):
        # Initialize the parent wrapper with the chosen bpftrace binary.
        super().__init__(
            bpftrace_binary=bpftrace_binary,
        )

    def run(
        self,
        target_cmd: Sequence[str],
        script: str = settings.default_bpftrace_script_path,
        log_file: Optional[str] = settings.default_log_path,
    ):
        """Start bpftrace with the given script and run target_cmd under it.

        Args:
            target_cmd: Sequence of command and arguments to run under bpftrace.
                        e.g. ["ls", "-l", "/tmp"]
            script: Path to the bpftrace script to execute.
            log_file: Optional path to a file where bpftrace logs should be written.

        The command sequence is joined into a single string because bpftrace's
        -c option expects a single shell command string.
        """
        # Use the inherited start() method. Pass the target command as a single
        # quoted command string to bpftrace via the -c argument.
        self.start(
            script=script,
            log_file=log_file,
            extra_args=["-c", " ".join(target_cmd)]
        )
