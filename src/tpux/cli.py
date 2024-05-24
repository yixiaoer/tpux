import glob
import ipaddress
import json
import os
import subprocess
from typing import Callable, Literal, Optional, Union

env = os.environ.copy()
env['DEBIAN_FRONTEND'] = 'noninteractive'

config_dir = os.path.expanduser('~/.config/tpux')
os.makedirs(config_dir, exist_ok=True)
config_file = os.path.join(config_dir, 'config.json')

def write_config_file(obj) -> None:
    with open(config_file, 'w') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

if not os.path.exists(config_file):
    write_config_file({})

def is_valid_private_ipv4_addr(s: str) -> bool:
    try:
        ip = ipaddress.ip_address(s)
    except ValueError:
        return False
    return ip.is_private and isinstance(ip, ipaddress.IPv4Address)

def is_valid_private_ipv4_addrs(ips: str) -> bool:
    parts = ips.split(',')
    parts = [part.strip() for part in parts]
    return all(is_valid_private_ipv4_addr(part) for part in parts)

def expect_user_input_bool(prompt: str, *, default: Optional[Union[Literal['y'], Literal['n']]] = None) -> bool:
    if default == 'y':
        options = '[Y/n]'
    elif default == 'n':
        options = '[y/N]'
    elif default == None:
        options = '[y/n]'
    else:
        raise ValueError(f'Invalid default value {default}')

    while True:
        res: Union[str, None] = input(f'{prompt} {options} ')
        res = default if res == '' else res

        if res == 'y':
            return True
        elif res == 'n':
            return False
        else:
            print('Please answer "y" or "n"')

def expect_user_input_str(prompt: str, *, default: Optional[str] = None, is_valid: Optional[Callable[[str], bool]] = None) -> str:
    default_text = '' if default is None else f'[default: {repr(default)}] '

    while True:
        res = input(f'{prompt} {default_text}')
        if is_valid is None or is_valid(res):
            return res
        print('Invalid input, please try again.')

def check_is_not_root() -> None:
    is_root = os.geteuid() == 0
    if is_root:
        print('Please run this script as a normal user, not root.')
        exit(-1)

def check_tpu_chip_exists() -> None:
    tpu_chip_exists = len(glob.glob('/dev/accel*')) > 0
    if not tpu_chip_exists:
        print('TPU chips not detected, exiting...')
        exit(-1)

def install_packages():
    commands = [
        'sudo apt-get update -y -qq',
        'sudo apt-get upgrade -y -qq',
        'sudo apt-get install -y -qq golang neofetch zsh byobu',
        'sudo apt-get install -y -qq software-properties-common',
        'sudo add-apt-repository -y ppa:deadsnakes/ppa',
        'sudo apt-get install -y -qq python3.12-full python3.12-dev',
    ]

    for command in commands:
        result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        if result.returncode != 0:
            print(f'Command failed: {command}')
            print(f'Error: {result.stderr.decode()}')
            exit(-1)

def install_oh_my_zsh():
    install_zsh = expect_user_input_bool('Do you want to install oh my zsh?', default='y')
    if install_zsh:
        commands = [
            'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended',
            'sudo chsh $USER -s /usr/bin/zsh',
        ]

        for command in commands:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                print(f'Command failed: {command}')
                print(f'Error: {result.stderr}')
                exit(-1)

def get_ips_of_pods():
    ip_host0 = expect_user_input_str('Input the private (internal) IPv4 address of the current host.', default=None, is_valid=is_valid_private_ipv4_addr)
    ip_host_others = expect_user_input_str('Input the private (internal) IPv4 address of the other hosts, comma separated.', is_valid=is_valid_private_ipv4_addrs)

def setup_single_host():
    check_is_not_root()
    check_tpu_chip_exists()
    install_packages()
    install_oh_my_zsh()
    raise NotImplementedError

def setup_tpu_pod():
    raise NotImplementedError

def main():
    print(
        'Welcome to tpux setup script!\n'
        'This script will guide you to setup environment on a new Cloud TPU.\n'
    )

    is_tpu_pod = expect_user_input_bool('Are you running on a TPU Pod (instead of a single TPU host)?')
    if is_tpu_pod:
        setup_tpu_pod()
    else:
        setup_single_host()
