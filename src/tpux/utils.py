import os

def get_config_path() -> str:
    return os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')

def get_podips_config_file() -> str:
    config_path = get_config_path()
    return os.path.join(config_path, 'tpux', 'podips.txt')
