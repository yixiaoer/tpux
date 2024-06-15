# tpux

export PATH="$HOME/.local/bin:$PATH"

Use `podrun` to make all hosts purr like a kitty:
```sh
echo echo meow | podrun -i
```

## TODO

- [ ] `env['DEBIAN_FRONTEND'] = 'noninteractive'` for pod
- [ ] Create venv

## Example

```sh
touch ~/nfs_share/meow
echo ls ~/nfs_share/meow
echo ls -l ~/nfs_share/meow | podrun -i
```

