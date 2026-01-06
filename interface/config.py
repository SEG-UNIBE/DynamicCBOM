
from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["./interface/settings.toml", "./interface/.secrets.toml"],
    envvar_prefix="DYNACONF"
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
