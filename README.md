# Undervolt detect project
Simulte undervolt attack on working payload. Train a model, and detect it.
## Project Environment
### CPU and Operation System
- CPU: *Intel® Gen 9th* or below where MSR `0x150` (Known as the mailbox interface) has not been abandoned.
- OS: Linux 5.15.0-138-generic #148~20.04.1-Ubuntu or other compatible OS.
### Setup
In order to allow userspace-level control of CPU voltage, we need for steps of operation:
#### In BIOS:
1. Hardware P-States should be disabled
    - Disable `Hardware P-States` if exist.
    - Disable `TurboBoost` relavant options.
2. Enable frequency and voltage control
    - Enable `SpeedStep` technology
#### In bash:
3. Edit grub startup commands
    - Run
        ```bash
        sudo vim /etc/default/grub
        ```
    - Find `GRUB_CMDLINE_LINUX_DEFAULT="..."`
    - Add `intel_pstate=disable acpi=force` into this option.
    - Applicate and reboot
        ```bash
        sudo update-grub
        sudo reboot
        ```
4. Change governors to `userspace` and fix CPU frequence to a certain value like `2500000`
    - `sudo apt install cpufrequtils` for tool kits
    - Run `./scripts/setup.sh` in the directory
### Programme Preparation
#### Spec CPU® 2017
- Download cpu2017-1.1.8.iso from [SPEC](https://www.spec.org/cpu2017) or other sources.
- Mount and install
    ```bash
    mkdir cpu2017
    mkdir spec2017
    sudo mount -t iso9660 -o ro,exec,loop ./cpu2017-1.1.8.iso ./cpu2017
    cd cpu2017
    bash ./install.sh # Enter path to target, referring its absolute path as <spec2017> below, e.g. {pwd}/spec2017
    ```
- Use default config `gcc`
    ```bash
    cd <spec2017>
    cd config
    cp Example-gcc-linux-x86.cfg gcc.cfg
    vim gcc.cfg # Follow instruction inside to enter path to gcc
    ```
- Source `shrc`
    ```bash
    cd <spec2017>
    source shrc
    ```
    Notice that if `<spc2017>/shrc` is not added to `~/.bashrc`, you need to `source` it every time after reboot.
- Build `intrate`suite for this project
    ```
    runcpu --config=gcc --action=build intrate
    ```
#### OpenSSL
- `sudo apt install openssl` is not installed.




