import os
from typing import List

import fabric

def get_config_path() -> str:
    return os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')

def get_podips_config_file() -> str:
    config_path = get_config_path()
    return os.path.join(config_path, 'tpux', 'podips.txt')

def get_podips() -> List[str]:
    podips_config_file = get_podips_config_file()
    with open(podips_config_file, 'r') as f:
        return [line.rstrip('\n') for line in f]

def run_command_on_all_hosts(command: str, *, append_localhost: bool) -> None:
    hosts = get_podips()

    if append_localhost:
        hosts.append('127.0.0.1')

    with fabric.ThreadingGroup(*hosts) as group:
        group.run(command)
