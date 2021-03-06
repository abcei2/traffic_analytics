from typing import Union
from dotenv import dotenv_values


PLACEHOLDER_FOR_SECRET = "set-this-value-in-secrets.env"

EnvSetting = Union[str, bool, int, float, list]
EnvSettingTypes = (str, bool, int, float, list)


def get_env_value(env: dict, key: str, default: EnvSetting = None):
    """get & cast a given value from a dictionary, or return the default"""
    if key in env:
        value = env[key]
    else:
        return default

    ExpectedType = type(default)
    assert (
        ExpectedType in EnvSettingTypes
    ), f"Tried to set unsupported environemnt variable {key} to {ExpectedType}"

    def raise_typerror():
        raise TypeError(
            f"Got bad environment variable {key}={value}" f" (expected {ExpectedType})"
        )

    if ExpectedType is str:
        return value
    elif ExpectedType is bool:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            raise_typerror()
    elif ExpectedType is int:
        if value.isdigit():
            return int(value)
        else:
            raise_typerror()
    elif ExpectedType is float:
        try:
            return float(value)
        except ValueError:
            raise_typerror()
    elif ExpectedType is list:
        return value.split(",")


def unique_env_settings(env: dict, defaults: dict) -> dict:
    """return all the new valid env settings in a dictionary of settings"""

    existing_settings = {
        setting_name: val
        for setting_name, val in (defaults or env).items()
        if not setting_name.startswith("_") and setting_name.isupper()
    }
    if not defaults:
        return existing_settings

    new_settings = {}
    for setting_name, default_val in existing_settings.items():
        loaded_val = get_env_value(env, setting_name, default_val)

        if loaded_val != default_val:
            new_settings[setting_name] = loaded_val

    return new_settings


def load_env_settings(
    dotenv_path: str = None, env: dict = None, defaults: dict = None
) -> dict:
    """load settings from a dotenv file or os.environ by default"""
    assert not (dotenv_path and env), "Only pass env or dotenv_path, not both"

    env_values = (env or {}).copy()
    defaults = (defaults or {}).copy()
    if dotenv_path:
        env_values = dotenv_values(dotenv_path=dotenv_path)

    return unique_env_settings(env_values, defaults)
