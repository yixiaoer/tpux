import glob
import os
import subprocess
from typing import Literal, Optional, Union

def expect_user_input(prompt: str, default: Optional[Union[Literal['y'], Literal['n']]] = None):
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

def check_is_not_root() -> None:
    is_root = os.geteuid() != 0
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
        'DEBIAN_FRONTEND=noninteractive sudo apt-get update -y -qq',
        'DEBIAN_FRONTEND=noninteractive sudo apt-get upgrade -y -qq',
        'DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -qq golang neofetch zsh byobu',
        'DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -qq software-properties-common',
        'DEBIAN_FRONTEND=noninteractive sudo add-apt-repository -y ppa:deadsnakes/ppa',
        'DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -qq python3.12-full python3.12-dev',
    ]

    for command in commands:
        result = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f'Command failed: {command}')
            print(f'Error: {result.stderr.decode()}')
            exit(-1)

def install_oh_my_zsh():
    install_zsh = expect_user_input('Do you want to install oh my zsh?', default='y')
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

    is_tpu_pod = expect_user_input('Are you running on a TPU Pod (instead of a single TPU host)?')
    if is_tpu_pod:
        setup_tpu_pod()
    else:
        setup_single_host()
