"""
Dependency installer module.

Provides a Singleton class to check, download, install, and remove the bpftrace binary
and its associated scripts. Uses settings from interface.config and subprocess/requests
for operations.
"""
import os
import platform
import requests
import subprocess
from rich.progress import Progress, SpinnerColumn, TextColumn
from interface.config import settings
from interface.utils.singleton import SingletonMeta

class DependencyInstallerError(Exception):
    """Custom exception raised for errors in the DependencyInstaller operations."""
    pass

class DependencyInstaller(metaclass=SingletonMeta):
    """
    Singleton that manages installation and uninstallation of bpftrace and its scripts.

    Responsibilities:
    - Check presence of the bpftrace binary and scripts.
    - Download and make the bpftrace binary executable.
    - Build/clean bpftrace scripts via `make`.
    - Provide high-level install/uninstall orchestration.
    """
    def __init__(self):
        """Initialize the installer. Currently no per-instance state is required."""
        pass
    
    def is_bpftrace_installed(self) -> bool:
        """
        Check whether a bpftrace binary exists at the configured path and is executable.

        Returns:
            True if the binary exists and is executable, otherwise False (or None in current implementation).
        """
        # Check if there's a bpftrace binary in current directory
        if os.path.isfile(settings.default_bpftrace_binary_path) and os.access(settings.default_bpftrace_binary_path, os.X_OK):
            return True

    def install_bpftrace(self) -> bool:
        """
        Download the bpftrace binary from the configured URL and set execute permissions.

        Returns:
            True if the binary is available after the operation, False on failure.
        """
        if self.is_bpftrace_installed():
            print("bpftrace is already installed.")
            return True

        system = platform.system()
        if system == "Windows":
            # Installer does not support Windows natively; recommend WSL2
            print("bpftrace is not supported on Windows by this installer. The alternative is to use WSL2.")
            return False

        # Download the binary from GitHub releases (or configured URL)
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
            # Network or HTTP error while downloading
            print(f"Error downloading bpftrace: {e}")
            return False

        # Make the binary executable
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Setting executable permissions for bpftrace...", total=None)
                os.chmod(settings.default_bpftrace_binary_path, 0o755)
            print("Set executable permissions for bpftrace")
        except Exception as e:
            # Filesystem error while setting permissions
            print(f"Error setting permissions for bpftrace: {e}")
            return False
        

        # final check
        if self.is_bpftrace_installed():
            print("bpftrace is available after attempted installs.")
            return True

        print("Failed to install bpftrace. Please install it manually.")
        return False
    
    def uninstall_bpftrace(self) -> bool:
        """
        Remove the managed bpftrace binary from the current working directory.

        Returns:
            True if removal succeeded, False if the binary was not found or removal failed.
        """
        if not self.is_bpftrace_installed():
            print("cannot find the installed bpftrace.")
            return False

        # Prefer removing the local ./bpftrace we manage
        local_path = os.path.join(os.getcwd(), settings.default_bpftrace_binary_path)
        os.remove(local_path)
        print(f"Removed bpftrace at {local_path}")
        return True

    def is_bpftrace_scripts_installed(self) -> bool:
        """
        Check whether the bpftrace scripts (built artifacts) exist and are readable.

        Returns:
            True if the default script path exists and is readable, False otherwise.
        """
        return os.path.isfile(settings.default_bpftrace_script_path) and os.access(settings.default_bpftrace_script_path, os.R_OK)
    
    def install_bpftrace_scripts(self) -> None:
        """
        Build the bpftrace scripts by running `make all` in the scripts directory.

        Raises:
            DependencyInstallerError if the build fails.
        """
        scripts_dir = settings.default_bpftrace_script_folder_path
        try:
            # Run the make command
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Building bpftrace scripts...", total=None)
                result = subprocess.run(["make", "all"], cwd=scripts_dir, check=True, text=True, capture_output=True)
            print("make all result:\n", result.stdout)
        except subprocess.CalledProcessError as e:
            # Capture build error output and wrap it in a custom exception
            print("Error during make:\n", e.stderr)
            raise DependencyInstallerError("Failed to build bpftrace scripts") from e
    
    def uninstall_bpftrace_scripts(self) -> None:
        """
        Clean the bpftrace scripts by running `make clean` in the scripts directory.

        Raises:
            DependencyInstallerError if the clean step fails.
        """
        scripts_dir = settings.default_bpftrace_script_folder_path
        try:
            # Run the make command
            result = subprocess.run(["make", "clean"], cwd=scripts_dir, check=True, text=True, capture_output=True)
            print("make clean result:\n", result.stdout)
        except subprocess.CalledProcessError as e:
            # Capture error output and re-raise as a custom exception
            print("Error during make:\n", e.stderr)
            raise DependencyInstallerError("Failed to build bpftrace scripts") from e

    def is_installed(self) -> bool:
        """
        High-level check that both the bpftrace binary and scripts are installed.

        Returns:
            True if both components are present, False otherwise.
        """
        return self.is_bpftrace_installed() and self.is_bpftrace_scripts_installed()

    def install(self):
        """
        High-level installation orchestration: install binary and scripts.

        Note: errors raised by lower-level functions may propagate.
        """
        self.install_bpftrace()
        self.install_bpftrace_scripts()
        
    def uninstall(self):
        """
        High-level uninstallation orchestration: remove binary and clean scripts.

        Note: errors raised by lower-level functions may propagate.
        """
        self.uninstall_bpftrace()
        self.uninstall_bpftrace_scripts()


        