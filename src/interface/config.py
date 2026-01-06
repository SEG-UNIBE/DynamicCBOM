"""Configuration management for the DynamicCBOM interface.

This module loads configuration settings from TOML files and environment variables
using Dynaconf. It provides a centralized settings object that can be imported
across the application.
"""

from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["./interface/settings.toml", "./interface/.secrets.toml"],
    envvar_prefix="DYNACONF",
)

# Environment variables with the DYNACONF prefix (e.g., DYNACONF_FOO=bar) override
# TOML settings. Configuration files are loaded in the specified order, with later
# files taking precedence over earlier ones.
