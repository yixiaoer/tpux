import argparse
from argparse import Namespace
import glob
from ipaddress import AddressValueError, IPv4Address
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
from typing import Callable, List, Literal, Optional, Union

import psutil

from .utils import get_podips, get_podips_config_file, run_command_on_all_hosts, run_command_on_localhost, run_commands_on_all_hosts, run_commands_on_localhost

YELLOW_START = '\033[93m'
COLOR_RESET = '\033[0m'

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

def parse_args() -> Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument('--is_tpu_pod', '-p', type=str, choices=['y', 'n'], help='Run on a tpu Pod or not(which means run on a tpu VM)')
    parser.add_argument('--install_zsh', '-z', type=str, choices=['y', 'n'], help='Install oh-my-zsh or not')
    parser.add_argument('--add_path_to_shell_config', '-s', type=str, choices=['y', 'n'], help='Add path to shell config or not')

    parser.add_argument('--priv_ipv4_addrs', '-i', type=str, help='The internal ipv4 addresses of other hosts')

    parser.add_argument('--clear', '-c', action='store_true', help='Clear configuration settings')

    args = parser.parse_args()
    return args

args = parse_args()

def input_bool(prompt: str, *, arg_value: Optional[str] = None, default: Optional[Union[Literal['y'], Literal['n']]] = None) -> bool:
    if arg_value is not None:
        if arg_value == 'y':
            return True
        elif arg_value == 'n':
            return False
        else:
            raise ValueError('Invalid arg value. Please use "y" or "n".')

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

def convert_str_addrs(s: str) -> List[IPv4Address]:
    parts = s.split(',')
    ip_addrs = []
    for part in parts:
        part = part.strip()
        ip_addr = IPv4Address(part)
        ip_addrs.append(ip_addr)
    return ip_addrs

def input_priv_ipv4_addrs(prompt: str, note: Optional[str] = None, *, arg_value: Optional[str] = None, default: Optional[List[IPv4Address]] = None) -> List[IPv4Address]:
    if arg_value is not None:
        try:
            return convert_str_addrs(arg_value)
        except AddressValueError as e:
            raise ValueError(f'Invalid arg value. Please use a list of valid private IPv4 addresses (comma-separated).') from e

    if default is None:
        default_str = ': '
    else:
        ip_str = ','.join(str(ip_addr) for ip_addr in default)
        default_str = f' (default: {ip_str}): '
    actual_prompt = f'{prompt}{default_str}' if note is None else f'''{prompt}{default_str}
{note}'''

    while True:
        s = input(actual_prompt)
        if not s and default is not None:
            return default
        try:
            ip_addrs = convert_str_addrs(s)
            return ip_addrs
        except AddressValueError:
            pass
        print(f'Please input a list of valid private IPv4 addresses (comma-separated).')

def get_priv_ipv4_addr(*, interface_prefix: str = 'ens') -> IPv4Address:
    addrs = psutil.net_if_addrs()
    for interface_name, interface_addrs in addrs.items():
        if interface_name.startswith(interface_prefix):
            for addr in interface_addrs:
                if addr.family == socket.AF_INET:  # get IPv4 addr
                    return IPv4Address(addr.address)
    raise RuntimeError('Cannot detect the private IPv4 address.')

ssh_config_file = os.path.expanduser('~/.ssh/config')
block_start = '# BEGIN tpux configuration'
block_end = '# END tpux configuration'
block_pattern = re.compile(r'\n*' + re.escape(block_start) + r'.*?' + re.escape(block_end) + r'\n*', re.DOTALL)

def clear_config_with_block(config_file: str, *, newline_format: str = '\n') -> None:
    if not os.path.exists(config_file):
        return

    content = Path(config_file).read_text()

    new_content = block_pattern.sub(f'\n{newline_format}', content).rstrip() + '\n'

    with open(config_file, 'w') as f:
        f.write(new_content)

def insert_ssh_config(ip_host_others: List[IPv4Address]) -> None:
    os.makedirs(os.path.expanduser('~/.ssh'), exist_ok=True)
    ips_str = '127.0.0.1 ' + ' '.join(str(ip) for ip in ip_host_others)
    config = f'''{block_start}
Host {ips_str}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
    IdentityFile ~/.ssh/id_ed25519_tpux
{block_end}
'''

    if not os.path.exists(ssh_config_file):
        with open(ssh_config_file, 'w') as f:
            pass
        os.chmod(ssh_config_file, 0o600)
        content = ''
    else:
        content = Path(ssh_config_file).read_text().rstrip()

    if not block_pattern.search(content):
        if not content:
            new_content = f'{content}{config}'
        else:
            new_content = f'{content}\n\n{config}'
    else:
        new_content = block_pattern.sub(config, content)

    with open(ssh_config_file, 'w') as f:
        f.write(new_content)

def clear_ssh_config() -> None:
    clear_config_with_block(ssh_config_file)

public_key_path = os.path.expanduser('~/.ssh/id_ed25519_tpux.pub')
private_key_path = os.path.expanduser('~/.ssh/id_ed25519_tpux')
authorized_key_path = os.path.expanduser('~/.ssh/authorized_keys')

def generate_ssh_key() -> None:
    command = ['ssh-keygen', '-t', 'ed25519', '-f', private_key_path, '-N', '']
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

    public_key = Path(public_key_path).read_text().strip()

    print(f'''Generated public key for tpux:
{public_key}
{YELLOW_START}Please open https://console.cloud.google.com/compute/metadata?resourceTab=sshkeys add this public key. This key will be automatically propagated to all hosts.{COLOR_RESET}''')
    input('Please press enter to continue...')

    while True:
        authorized_key_file = Path(authorized_key_path)
        authorized_key_data = '' if not authorized_key_file.exists() else authorized_key_file.read_text()
        if public_key in authorized_key_data:
            break
        input('The key has not been propagated to host machines. Please wait for a while, and then press enter to continue...')

def clear_ssh_key() -> None:
    public_key_file = Path(public_key_path)
    public_key_file.unlink(missing_ok=True)

    private_key_file = Path(private_key_path)
    private_key_file.unlink(missing_ok=True)

def write_podips_config(ip_host_others: List[IPv4Address]) -> None:
    podips_config_file = get_podips_config_file()
    with open(podips_config_file, 'w') as f:
        for ip in ip_host_others:
            print(ip, file=f)

def check_is_not_root() -> None:
    is_root = os.geteuid() == 0
    if is_root:
        print('Please run this script as a normal user, not root.')
        exit(-1)

def check_tpu_chip_exists() -> None:
    tpu_chip_exists = len(glob.glob('/dev/accel*')) > 0
    if not tpu_chip_exists:
        print('TPU chips not detected. Please check your TPU setup, create a new TPU VM or turn to the Cloud TPU documentation for further assistance.')
        print('Exiting...')

        exit(-1)

update_apt_commands = [
    'sudo apt-get update -y -qq',
    'sudo apt-get upgrade -y -qq',
]

install_packages_commands = [
    'sudo apt-get install -y -qq golang neofetch zsh byobu',
    'sudo apt-get install -y -qq software-properties-common',
    'sudo add-apt-repository -y ppa:deadsnakes/ppa',
    'sudo apt-get install -y -qq python3.12-full python3.12-dev',
]

install_oh_my_zsh_commands = [
    'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended',
    'sudo chsh $USER -s /usr/bin/zsh',
]

def update_apt() -> None:
    run_commands_on_localhost(update_apt_commands)

def update_apt_on_hosts() -> None:
    run_commands_on_all_hosts(update_apt_commands, include_local=True)

def install_packages() -> None:
    run_commands_on_localhost(install_packages_commands)

def install_packages_on_hosts() -> None:
    run_commands_on_all_hosts(install_packages_commands, include_local=True)

def install_oh_my_zsh() -> None:
    install_zsh = input_bool('Do you want to install oh my zsh?', arg_value=args.install_zsh, default='y')
    if install_zsh:
        run_commands_on_localhost(install_oh_my_zsh_commands, shell=True)

def install_oh_my_zsh_on_hosts() -> None:
    install_zsh = input_bool('Do you want to install oh my zsh?', arg_value=args.install_zsh, default='y')
    if install_zsh:
        run_commands_on_all_hosts(install_oh_my_zsh_commands, include_local=True)

def config_podips() -> None:
    ip_host0 = get_priv_ipv4_addr()
    note = f'''{YELLOW_START}To find the IPv4 addresses,
1. Open https://console.cloud.google.com/compute/tpus
2. Click on the node name of the TPU pod you're using in the current project
3. In the details, find the Internal IP addresses
4. Do NOT include the IP address of the current host: {ip_host0}{COLOR_RESET}
'''
    ip_host_others = input_priv_ipv4_addrs('Input the private (internal) IPv4 address of the other hosts, comma separated', note, arg_value=args.priv_ipv4_addrs)
    insert_ssh_config(ip_host_others=ip_host_others)
    write_podips_config(ip_host_others=ip_host_others)  # TODO: do we need to add host0 ip here?

def install_nfs_on_hosts() -> None:
    run_command_on_all_hosts('sudo apt-get install -y -qq nfs-common', include_local=False)
    run_commands_on_localhost([
        'sudo apt-get install -y -qq nfs-kernel-server',
        'sudo mkdir -p /nfs_share',
        'sudo chown -R nobody:nogroup /nfs_share',
        'sudo chmod 777 /nfs_share',
    ])

export_file_name = '/etc/exports'
def insert_exports_config() -> None:
    hosts = get_podips()
    export_file_path = Path(export_file_name)

    export_file = '' if not export_file_path.exists() else export_file_path.read_text()

    new_entries = '\n'.join(f'/nfs_share {ip}(rw,sync,no_subtree_check)' for ip in hosts)
    export_new_entries = f'''
{block_start}
{new_entries}
{block_end}
'''

    if not block_pattern.search(export_file):
        if not export_file or export_file.endswith('\n\n'):
            export_file_new = f'{export_file}{export_new_entries}'
        else:
            export_file_new = f'{export_file}\n{export_new_entries}'
    else:
        export_file_new = block_pattern.sub(export_new_entries, export_file)

    with tempfile.TemporaryDirectory() as name:
        tmp_file = Path(name) / 'exports'
        tmp_file.write_text(export_file_new)

        subprocess.run(['sudo', 'cp', str(tmp_file), export_file_name], check=True)

def clear_exports_config() -> None:
    export_file_path = Path(export_file_name)
    export_file = '' if not export_file_path.exists() else export_file_path.read_text()

    with tempfile.TemporaryDirectory() as name:
        tmp_file = Path(name) / 'exports'
        tmp_file.write_text(export_file)

        clear_config_with_block(str(tmp_file))

        subprocess.run(['sudo', 'cp', str(tmp_file), export_file_name], check=True)

def config_nfs() -> None:
    ip_host0 = get_priv_ipv4_addr()

    run_command_on_localhost('sudo exportfs -ra', check=True)
    run_command_on_localhost('sudo systemctl restart nfs-kernel-server', check=True)

    run_command_on_all_hosts('sudo mkdir -p /nfs_share', include_local=False)
    run_command_on_all_hosts(f'sudo mount {ip_host0}:/nfs_share /nfs_share', include_local=False)
    run_command_on_all_hosts('ln -sf /nfs_share ~/nfs_share', include_local=True)

def get_shell_path() -> str:
    bashrc_path = os.path.expanduser('~/.bashrc')
    zshrc_path = os.path.expanduser('~/.zshrc')

    if not os.path.exists(bashrc_path) and not os.path.exists(zshrc_path):
        raise ValueError("Neither `.bashrc` nor `.zshrc` configuration files were found in the user's home directory.")

    return zshrc_path if os.path.exists(zshrc_path) else bashrc_path

def add_path_to_env() -> None:
    shell_config_file = get_shell_path()
    add_path_to_shell_config = input_bool(f'Do you want to add the `export PATH="$HOME/.local/bin:$PATH"` to {shell_config_file}?', arg_value=args.add_path_to_shell_config, default='y')

    if add_path_to_shell_config:
        shell_config = Path(shell_config_file).read_text().rstrip()
        config = f'''{shell_config}

{block_start}
export PATH="$HOME/.local/bin:$PATH"
{block_end}
'''

        with tempfile.TemporaryDirectory() as name:
            tmp_file = Path(name) / 'shell_config'
            tmp_file.write_text(config)

            subprocess.run(['sudo', 'cp', str(tmp_file), shell_config_file], check=True)

def clear_path_to_env() -> None:
    shell_config_file = get_shell_path()
    clear_config_with_block(shell_config_file)

def setup_single_host() -> None:
    check_is_not_root()
    check_tpu_chip_exists()

    update_apt()
    install_packages()
    install_oh_my_zsh()

    add_path_to_env()

def setup_tpu_pod() -> None:
    check_is_not_root()
    check_tpu_chip_exists()

    config_podips()
    generate_ssh_key()

    update_apt_on_hosts()
    install_packages_on_hosts()
    install_oh_my_zsh_on_hosts()
    install_nfs_on_hosts()
    insert_exports_config()
    config_nfs()

    add_path_to_env()

def clear_setup_single_host() -> None:
    clear_path_to_env()

def clear_setup_tpu_pod() -> None:
    clear_ssh_config()
    clear_ssh_key()
    clear_exports_config()
    clear_path_to_env()

def setup_or_clear(setup_fn: Callable[[], None], clear_fn: Callable[[], None], is_clear: bool) -> None:
    if is_clear:
        clear_fn()
    else:
        setup_fn()

def main() -> None:
    print(
        'Welcome to tpux setup script!\n'
        'This script will guide you to setup environment on a new Cloud TPU.\n'
    )

    is_tpu_pod = input_bool('Are you running on a TPU Pod (instead of a single TPU host)?', arg_value=args.is_tpu_pod)

    if is_tpu_pod:
        setup_or_clear(setup_tpu_pod, clear_setup_tpu_pod, args.clear)
    else:
        setup_or_clear(setup_single_host, clear_setup_single_host, args.clear)
