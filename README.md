# tpux: Enhance Your Google Cloud TPU Experience

Welcome to tpux, your essential toolkit designed to revolutionize the way you use Google Cloud TPUs. This suite of tools is tailored to simplify and streamline your TPU setup and operation processes, ensuring you maximize your productivity with minimal effort.

## Pronunciation

To pronounce "tpux", first say "TPU" as you would in English, followed by "X" pronounced as /iks/ in French.

## Why You Need tpux

Setting up Google Cloud TPU instances traditionally involves initializing empty VM instances, a process that can be tedious and repetitive. With tpux, this setup is greatly simplified, allowing you to focus on what truly matters—your work.

## Features

- `tpux`: A user-friendly setup script that automates the configuration of your Google Cloud TPUs. This tool ensures that you are equipped with the latest practices and optimizations, keeping your operations cutting-edge.
- `podrun`: Seamlessly execute commands across all nodes in your TPU pods. Ideal for scaling applications and managing large-scale machine learning tasks, it enhances efficiency and effectiveness across your deployments.

Inspired by the comprehensive guide [ayaka14732/tpu-starter](https://github.com/ayaka14732/tpu-starter), tpux incorporates best practices for TPU usage in open-source environments.

## Setting Up Your TPU VM or TPU Pod with tpux

Watch our [quick setup guide on YouTube](https://www.youtube.com/watch?v=a42YnpzcEYM) to see how to configure your TPU v4-32 using tpux. This video serves as an example, and the procedures can be applied to any Google Cloud TPU devices.

[![Watch the tpux setup video](https://img.youtube.com/vi/a42YnpzcEYM/maxresdefault.jpg)](https://www.youtube.com/watch?v=a42YnpzcEYM)

### When Creating TPU VM or TPU Pod Instances

During the creation of a TPU VM instance, ensure to select the latest `tpu-ubuntu2204-base` software version to benefit from the most up-to-date system and software packages.

Besides using the web UI to create TPUs, you can also use the Google Cloud Shell. Here, your `--version` option should specify `tpu-ubuntu2204-base`. For example:

```sh
until gcloud alpha compute tpus tpu-vm create node-2 --zone us-central2-b --accelerator-type v4-32 --version tpu-ubuntu2204-base ; do : ; done
```

### Using the `tpux` Command to Execute the Setup Script

After SSH into one of the hosts of your TPU VM or TPU Pod, you can perform the setup using `tpux`. There are two ways to proceed: interactive setup or setup using command line options.

#### Interactive Setup

To quickly start the interactive setup, run:

```sh
pip install tpux
export PATH="$HOME/.local/bin:$PATH"
tpux
```

Simply follow the on-screen prompts to complete the setup of your TPU VM or TPU Pod.

#### Command Line Options for Setup

To perform the setup with specific configurations and less interaction, `tpux` supports several command line options. The provided options will bypass corresponding interactive prompts. Any unspecified configurations will be requested interactively. If all necessary options are provided, the setup will run without interaction.

* `--is_tpu_pod` (`-p`): Specify if the setup is for a TPU Pod or a TPU VM.

    * Usage: `--is_tpu_pod y` or `-p y` for TPU Pod, `--is_tpu_pod n` or `-p n` for TPU VM.

* `--install_zsh` (`-z`): Choose whether to install oh-my-zsh.

    * Usage: `--install_zsh y` or `-z y` to install oh-my-zsh, `--install_zsh n` or `-z n` to skip installation.

* `--add_path_to_shell_config` (`-s`): Add `tpux` path to the shell configuration file.

    * Usage: `--add_path_to_shell_config y` or `-s y` to add, `--add_path_to_shell_config n` or `-s n` to skip.

* `--priv_ipv4_addrs` (-i): Provide a comma-separated list of IPv4 addresses of other hosts (applicable only for TPU Pods).

    * Usage: `--priv_ipv4_addrs '<ip addresses of other hosts>'` or `-i '<ip addresses of other hosts>'`.

Examples for Setup:

* Non-Interactive Setup for TPU VM with Zsh Installation and Path Addition

    ```sh
    tpux --is_tpu_pod n --install_zsh y --add_path_to_shell_config y
    ```

* Non-Interactive Setup for TPU Pod with Specific Hosts

    ```sh
    tpux -p y -i '<ip addresses of other hosts>' -z y -s y
    ```

#### Adding tpux to PATH

If the PATH has been added to your shell configuration file (`~/.bashrc` or `~/.zshrc`) by default, you can run the `tpux` or `podrun` commands directly. Otherwise, add the following line before running the commands:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

#### Clearing Configuration

To clear all configuration information with files, `tpux` provides options to reset your setup.

Command line options for clearing configuration:

* `--is_tpu_pod` (`-p`): Specify if the setup to clear is for a TPU Pod or a TPU VM.

    * Usage: `--is_tpu_pod y` or `-p y` for TPU Pod, `--is_tpu_pod n` or `-p n` for TPU VM.

* `--clear` (`-c`): Clear all information in the configuration file.

    * Usage: `--clear` or `-c`.

Example for clearing configuration:

* Clearing Configuration for TPU VM

    ```sh
    tpux --is_tpu_pod n -c
    ```

* Clearing Configuration for TPU Pod

    ```sh
    tpux --is_tpu_pod y --clear
    ```

### Executing Commands Across All Hosts with the `podrun` Command

After setting up with the `tpux` command, you can use the `podrun` command to execute specified commands across all TPU hosts in a TPU Pod.

#### Command Options for Running Commands

Before running commands with `podrun`, familiarize the available options:

* `-i` (`--include-local`): Executes the command on all hosts, including the local one; while omitting `-i` executes on all hosts except the local one.

* `-w` (`--cwd`): Executes the command in the current working directory, assuming the directory exists on all hosts.

* `-h` (`--help`): For more information on how to use the `podrun` command, simply run:

    ```sh
    podrun -h
    ```

Adjust these options based on your needs. For example, use `podrun -ic` to include the local host and execute the command in the current working directory.

#### Running Commands Method 1: Pipe Method

With the Pipe Method, `podrun` reads the command to be executed from stdin with `echo` and `|`, for example, run the command on host0:

```sh
echo echo meow | podrun -i
```

The above command outputs "meow" on all hosts, using the `-i` parameter to include the local machine in the execution.

Without the `-i` parameter, the command runs only on other hosts:

```sh
echo echo meow | podrun
```

The above command outputs "meow" on all hosts except the local machine.

#### Running Commands Method 2: Live Command Method

In the Live Command Method, you can run podrun and input commands directly.

Enter the following command in the terminal:

```sh
podrun -iw
```

This command initiates `podrun` with the specified options (`-i` to include the local host, and `-w` for the current directory). 

After pressing Enter, `podrun` program will pause and wait for your input. You can then copy and paste the command(s) you wish to execute (supporting multiple lines) into the terminal, press Enter, and then press Ctrl+D to end the input. Afterward, `podrun` will execute the command across all hosts in the TPU Pod.

### Verifying Successful Configuration of Your TPU Pod

Given the complexity of configuring a TPU Pod, after executing the `tpux` setup command, you may want to ensure it was successful. You can verify this by:

```sh
echo echo meow | podrun -i
```

If the TPU Pod is configured correctly, the above command should output multiple lines of "meow," where the number of lines corresponds to the number of TPU Pod hosts.

```sh
touch ~/nfs_share/meow
echo ls -l ~/nfs_share/meow | podrun -i
```

If configured correctly, the above commands should display the results of `ls -l ~/nfs_share/meow` on multiple lines, with the number of lines equaling the number of TPU Pod hosts.

## Disclaimer

This is not an officially supported Google product.
