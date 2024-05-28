import glob
from ipaddress import AddressValueError, IPv4Address
import json
import os
import socket
import subprocess
from typing import Callable, List, Literal, Optional, Union

import psutil

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

def input_bool(prompt: str, *, default: Optional[Union[Literal['y'], Literal['n']]] = None) -> bool:
    if default == 'y':
        options = '[Y/n]'
    elif default == 'n':
        options = '[y/N]'
    elif default == None:
        options = '[y/n]'
    else:
        raise ValueError(f'Invalid default value {default}.')

    while True:
        res: Union[str, None] = input(f'{prompt} {options} ')
        res = default if res == '' else res

        if res == 'y':
            return True
        elif res == 'n':
            return False
        else:
            print('Please answer "y" or "n".')

def input_priv_ipv4_addr(prompt: str, default: Optional[IPv4Address] = None) -> IPv4Address:
    default_str = ': ' if default is None else f' (default: {default}): '
    actual_prompt = f'{prompt}{default_str}'
    while True:
        s = input(actual_prompt)
        if not s and default is not None:
            return default
        try:
            return IPv4Address(s)
        except AddressValueError:
            pass
        print('Please input a valid private IPv4 address.')

def input_priv_ipv4_addrs(prompt: str, default: Optional[List[IPv4Address]] = None) -> List[IPv4Address]:
    if default is None:
        default_str = ': '
    else:
        ip_str = ','.join(str(ip_addr) for ip_addr in default)
        default_str = f' (default: {ip_str}): '
    actual_prompt = f'{prompt}{default_str}'

    while True:
        s = input(actual_prompt)
        if not s and default is not None:
            return default
        try:
            parts = s.split(',')
            ip_addrs = []
            for part in parts:
                part = part.strip()
                ip_addr = IPv4Address(part)
                ip_addrs.append(ip_addr)
            return ip_addrs
        except AddressValueError:
            pass
        print('Please input a list of valid private IPv4 addresses (comma-separated).')

# def input_str(prompt: str, *, default: Optional[str] = None, is_valid: Optional[Callable[[str], bool]] = None) -> str:
#     default_text = '' if default is None else f'[default: {repr(default)}] '

#     while True:
#         res = input(f'{prompt} {default_text}')
#         if is_valid is None or is_valid(res):
#             return res
#         print('Invalid input, please try again.')

def get_priv_ipv4_addr(*, interface_prefix: str = 'ens') -> IPv4Address:
    addrs = psutil.net_if_addrs()
    for interface_name, interface_addrs in addrs.items():
        if interface_name.startswith(interface_prefix):
            for addr in interface_addrs:
                if addr.family == socket.AF_INET:  # get IPv4 addr
                    return IPv4Address(addr.address)
    raise RuntimeError('Cannot detect the private IPv4 address.')

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
    install_zsh = input_bool('Do you want to install oh my zsh?', default='y')
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
    ip_host0 = input_priv_ipv4_addr('Input the private (internal) IPv4 address of the current host', default=get_priv_ipv4_addr())
    ip_host_others = input_priv_ipv4_addrs('Input the private (internal) IPv4 address of the other hosts, comma separated')

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

    is_tpu_pod = input_bool('Are you running on a TPU Pod (instead of a single TPU host)?')
    if is_tpu_pod:
        setup_tpu_pod()
    else:
        setup_single_host()
