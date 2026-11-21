#!/usr/bin/python3
"""Install new user units, preserving unrelated existing files and running model services."""
from pathlib import Path
import os
import subprocess

os.umask(0o077)
repo=Path(__file__).resolve().parent
home=Path.home()
unitdir=home/'.config/systemd/user'
installed=home/'.local/share/webos-services'
unitdir.mkdir(parents=True,exist_ok=True)
if installed.exists() or installed.is_symlink():
    if installed.resolve()!=repo:raise SystemExit(f'Existing installation at {installed}')
else:
    installed.parent.mkdir(parents=True,exist_ok=True)
    installed.symlink_to(repo,target_is_directory=True)
for unit in (repo/'units').glob('*.service'):
    target=unitdir/unit.name
    old=home/'.local/share/webos-gpu-monitor/webos-gpu-monitor.service'
    if target.is_symlink() and target.resolve()==unit.resolve():continue
    if target.exists() or target.is_symlink():
        if unit.name!='webos-gpu-monitor.service' or not target.is_symlink() or target.resolve()!=old or old.read_text()!=unit.read_text().replace('%h/.local/share/webos-services/bin/gpu-probe','%h/.local/share/webos-gpu-monitor/probe.py'):
            raise SystemExit(f'Unrecognized installed unit at {target}')
    temp=unitdir/(unit.name+'.webos-install')
    temp.symlink_to(unit);temp.replace(target)
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
