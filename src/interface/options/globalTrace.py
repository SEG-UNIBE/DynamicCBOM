"""
Wrapper option to run a global bpftrace script.

Provides a small convenience class that configures and starts a BpftraceWrapper
instance using application-wide default paths from the settings module.
"""

from typing import Optional

from interface.bpftraceWrapper import BpftraceWrapper
from interface.config import settings


class GlobalTrace(BpftraceWrapper):
    """
    Convenience wrapper for running a global bpftrace script.

    Inherits from BpftraceWrapper and uses defaults from the application's
    settings module so callers can start tracing with minimal arguments.
    """

    def __init__(
        self,
        bpftrace_binary: str = settings.default_bpftrace_binary_path,
    ):
        """
        Initialize the GlobalTrace wrapper.

        :param bpftrace_binary: Path to the bpftrace binary. Defaults to the
                                application-configured binary path.
        """
        # Initialize parent wrapper with the configured binary path
        super().__init__(
            bpftrace_binary=bpftrace_binary,
        )

    def run(
        self,
        script: str = settings.default_bpftrace_script_path,
        log_file: Optional[str] = settings.default_log_path,
    ):
        """
        Start the bpftrace script.

        :param script: Path to the bpftrace script to run. Defaults to the
                       application-configured script path.
        :param log_file: Optional path to a log file where output should be
                         written. If None, behavior falls back to the base wrapper.
        """
        # Delegate to the wrapper's start method which handles launching and logging
        self.start(script=script, log_file=log_file)
