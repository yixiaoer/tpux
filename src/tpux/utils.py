import os
import subprocess
from typing import List

import fabric

env = os.environ.copy()
env['DEBIAN_FRONTEND'] = 'noninteractive'

def get_config_path() -> str:
    return os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')

def get_podips_config_file() -> str:
    config_path = get_config_path()
    return os.path.join(config_path, 'tpux', 'podips.txt')

def get_podips() -> List[str]:
    podips_config_file = get_podips_config_file()
    with open(podips_config_file, 'r') as f:
        return [line.rstrip('\n') for line in f]

def run_command_on_localhost(command: str, **kwargs) -> None:
    if kwargs.get('shell'):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, **kwargs)
    else:
        result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, **kwargs)

    if result.returncode != 0:
        print(f'Command failed: {command}')
        print(f'Error: {result.stderr.decode()}')
        exit(-1)

def run_commands_on_localhost(commands: List[str], **kwargs) -> None:
    for command in commands:
        run_command_on_localhost(command, **kwargs)

def run_command_on_all_hosts(command: str, *, include_local: bool) -> None:
    hosts = get_podips()

    if include_local:
        hosts.append('127.0.0.1')

    with fabric.ThreadingGroup(*hosts) as group:
        group.run(command)

def run_commands_on_all_hosts(commands: List[str], *, include_local: bool) -> None:
    for command in commands:
        run_command_on_all_hosts(command, include_local=include_local)
