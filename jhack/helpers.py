import contextlib
import json as jsn
import os
import subprocess
from functools import partial
from pathlib import Path
from subprocess import PIPE
from typing import List

from juju.model import Model


@contextlib.asynccontextmanager
async def get_current_model() -> Model:
    model = Model()
    try:
        # connect to the current model with the current user, per the Juju CLI
        await model.connect()
        yield model

    finally:
        if model.is_connected():
            print("Disconnecting from model")
            await model.disconnect()


def get_local_charm() -> Path:
    cwd = Path(os.getcwd())
    try:
        return next(cwd.glob("*.charm"))
    except StopIteration:
        raise FileNotFoundError(f"could not find a .charm file in {cwd}")


# Env-passing-down Popen
JPopen = partial(subprocess.Popen, env=os.environ)


def juju_status(app_name, model: str = None, json: bool = False):
    cmd = f'juju status{" " + app_name if app_name else ""} --relations'
    if model:
        cmd += f" -m {model}"
    if json:
        cmd += " --format json"
    proc = JPopen(cmd.split(), stdout=PIPE, stderr=PIPE)
    raw = proc.stdout.read().decode("utf-8")
    if json:
        return jsn.loads(raw)
    return raw


def juju_models() -> str:
    proc = JPopen(f"juju models".split(), stdout=PIPE)
    return proc.stdout.read().decode("utf-8")


def list_models(strip_star=False) -> List[str]:
    raw = juju_models()
    lines = raw.split("\n")[3:]
    models = filter(None, (line.split(" ")[0] for line in lines))
    if strip_star:
        return [name.strip("*") for name in models]
    return models


def current_model() -> str:
    all_models = list_models()
    key = lambda name: name.endswith("*")
    return next(filter(key, all_models)).strip("*")
