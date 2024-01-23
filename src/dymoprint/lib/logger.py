import logging
import os
import sys

_IS_VERBOSE = False
LOG = logging.getLogger("dymoprint")
VERBOSE_NOTICE = "Run with --verbose for more information"


def _is_env_var_true(env_var: str) -> bool:
    val = os.getenv(env_var)
    return val is not None and val.lower() in ("1", "true")


def _is_verbose_env_vars() -> bool:
    return _is_env_var_true("VERBOSE")


def _update_log_level():
    LOG.setLevel(logging.DEBUG if _IS_VERBOSE else logging.INFO)


def set_verbose():
    global _IS_VERBOSE
    _IS_VERBOSE = True
    _update_log_level()


def is_verbose():
    return _IS_VERBOSE


def configure_logging():
    global _IS_VERBOSE
    _IS_VERBOSE = _is_verbose_env_vars()

    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    _update_log_level()
    LOG.addHandler(handler)


def print_exception(e):
    if _IS_VERBOSE:
        LOG.exception(e)
    else:
        LOG.error(e)
        LOG.error(VERBOSE_NOTICE)
