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

After SSH into one of the hosts of your TPU VM or TPU Pod, you can perform the setup using the following method:

```sh
pip install tpux
export PATH="$HOME/.local/bin:$PATH"
tpux
```

Simply follow the on-screen prompts to complete the setup of your TPU VM or TPU Pod.

If the PATH has been added to your shell configuration file (`~/.bashrc` or `~/.zshrc`) by default, you can run the `tpux` or `podrun` commands directly. Otherwise, add the following line before running the commands:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

### Executing Commands Across All Hosts with the `podrun` Command

After setting up with the `tpux` command, you can use the `podrun` command to execute specified commands across all TPU hosts.

`podrun` reads the command to be executed from stdin, for example:

```sh
echo echo meow | podrun -i
```

This command outputs "meow" on all hosts.

Using the `-i` parameter executes the command on all machines, while omitting `-i` executes on all hosts except the local one:

```sh
echo echo meow | podrun
```

This command outputs "meow" on all hosts except the local machine.

For more information on how to use the `podrun` command, type:

```sh
podrun -h
```

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
