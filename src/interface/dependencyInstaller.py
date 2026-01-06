"""Dependency installer for bpftrace and build scripts.

Provides a singleton class to check, download, install, and remove the bpftrace
binary and its associated scripts. Uses settings from interface.config and
subprocess/requests for operations.
"""

import os
import platform
import subprocess

import requests
from rich.progress import Progress, SpinnerColumn, TextColumn

from interface.config import settings
from interface.utils.singleton import SingletonMeta


class DependencyInstallerError(Exception):
    """Exception raised for errors in DependencyInstaller operations."""

    pass


class DependencyInstaller(metaclass=SingletonMeta):
    """Manages installation and uninstallation of bpftrace and build scripts.

    Singleton class responsible for checking, downloading, installing, and
    removing bpftrace binary and associated build scripts. Provides both
    individual operations and high-level orchestration methods.

    Operations:
        - Check presence of bpftrace binary and scripts
        - Download bpftrace binary from configured source
        - Set execute permissions on binaries
        - Build scripts via make
        - Clean build artifacts via make
    """

    def __init__(self):
        """Initialize the dependency installer.

        No per-instance state is required due to singleton pattern.
        """
        pass

    def is_bpftrace_installed(self) -> bool:
        """Check if bpftrace binary is installed and executable.

        Returns:
            True if the binary exists and is executable, False otherwise.
        """
        if os.path.isfile(settings.default_bpftrace_binary_path) and os.access(
            settings.default_bpftrace_binary_path, os.X_OK
        ):
            return True
        return False

    def install_bpftrace(self) -> bool:
        """Download and install the bpftrace binary.

        Downloads the bpftrace binary from the configured URL and sets
        appropriate execute permissions. Automatically detects the OS
        and provides platform-specific guidance.

        Returns:
            True if installation succeeded, False otherwise.
        """
        if self.is_bpftrace_installed():
            print("bpftrace is already installed.")
            return True

        system = platform.system()
        if system == "Windows":
            print("bpftrace is not supported on Windows by this installer. Use WSL2.")
            return False

        # Download the binary from GitHub releases
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Downloading bpftrace...", total=None)
                response = requests.get(settings.bpftrace_download_url)
                response.raise_for_status()
                with open(settings.default_bpftrace_binary_path, "wb") as f:
                    f.write(response.content)
            print("Downloaded bpftrace")
        except requests.RequestException as e:
            print(f"Error downloading bpftrace: {e}")
            return False

        # Make the binary executable
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(
                    description="Setting executable permissions for bpftrace...", total=None
                )
                os.chmod(settings.default_bpftrace_binary_path, 0o755)
            print("Set executable permissions for bpftrace")
        except Exception as e:
            print(f"Error setting permissions for bpftrace: {e}")
            return False

        # Final check
        if self.is_bpftrace_installed():
            print("bpftrace is available after installation.")
            return True

        print("Failed to install bpftrace. Please install it manually.")
        return False

    def uninstall_bpftrace(self) -> bool:
        """Remove the installed bpftrace binary.

        Returns:
            True if removal succeeded, False if binary not found.
        """
        if not self.is_bpftrace_installed():
            print("cannot find the installed bpftrace.")
            return False

        local_path = os.path.join(os.getcwd(), settings.default_bpftrace_binary_path)
        os.remove(local_path)
        print(f"Removed bpftrace at {local_path}")
        return True

    def is_bpftrace_scripts_installed(self) -> bool:
        """Check if bpftrace build scripts are installed.

        Returns:
            True if the default script path exists and is readable, False otherwise.
        """
        return os.path.isfile(settings.default_bpftrace_script_path) and os.access(
            settings.default_bpftrace_script_path, os.R_OK
        )

    def install_bpftrace_scripts(self) -> None:
        """Build bpftrace scripts by running make.

        Runs 'make all' in the scripts directory to build necessary artifacts.

        Raises:
            DependencyInstallerError: If the build fails.
        """
        scripts_dir = settings.default_bpftrace_script_folder_path
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Building bpftrace scripts...", total=None)
                result = subprocess.run(
                    ["make", "all"], cwd=scripts_dir, check=True, text=True, capture_output=True
                )
            print("Build succeeded:\n", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Error during build:\n", e.stderr)
            raise DependencyInstallerError("Failed to build bpftrace scripts") from e

    def uninstall_bpftrace_scripts(self) -> None:
        """Clean bpftrace build artifacts by running make clean.

        Runs 'make clean' in the scripts directory to remove build artifacts.

        Raises:
            DependencyInstallerError: If the clean operation fails.
        """
        scripts_dir = settings.default_bpftrace_script_folder_path
        try:
            result = subprocess.run(
                ["make", "clean"], cwd=scripts_dir, check=True, text=True, capture_output=True
            )
            print("Clean succeeded:\n", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Error during clean:\n", e.stderr)
            raise DependencyInstallerError("Failed to clean bpftrace scripts") from e

    def is_installed(self) -> bool:
        """Check if all dependencies are installed.

        Returns:
            True if both bpftrace binary and scripts are installed, False otherwise.
        """
        return self.is_bpftrace_installed() and self.is_bpftrace_scripts_installed()

    def install(self):
        """High-level installation orchestration.

        Installs both the bpftrace binary and builds the necessary scripts.
        """
        self.install_bpftrace()
        self.install_bpftrace_scripts()

    def uninstall(self):
        """High-level uninstallation orchestration.

        Removes the bpftrace binary and cleans up build artifacts.
        """
        self.uninstall_bpftrace()
        self.uninstall_bpftrace_scripts()
