= Title

Determine the Linux kernel version.

```sh
uname -a
```

Output
```console
rdonnell@MT-504479:~/repos/hpsc/lab/tools/runbook/examples$  uname -a
```

Determine the distribution version.

```sh
lsb_release -a
```

Output
```console
rdonnell@MT-504479:~/repos/hpsc/lab/tools/runbook/examples$  lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 24.04.4 LTS
Release:        24.04
Codename:       noble
```

Run multiple commands in one block.

```sh
key=value
echo $key
```

Output
```console
rdonnell@MT-504479:~/repos/hpsc/lab/tools/runbook/examples$  key=value
rdonnell@MT-504479:~/repos/hpsc/lab/tools/runbook/examples$  echo $key
value
```

Some trailing text.

