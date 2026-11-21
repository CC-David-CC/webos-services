"""Read local GPU counters and write an owner-only snapshot for the WebOS gateway."""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def output(argv):
    return subprocess.check_output(argv, text=True, timeout=5, stderr=subprocess.DEVNULL).strip()


def number(value):
    return int(value) if str(value).strip().isdigit() else None


def process_model(pid):
    # Inspect only model flags on compute processes. Never export their argv, environment or paths.
    try:
        args = Path(f'/proc/{int(pid)}/cmdline').read_bytes().decode(errors='replace').split('\0')
    except (OSError, ValueError):
        return None
    flags = ('-m', '--model', '--model-path')
    for i, arg in enumerate(args):
        name, sep, value = arg.partition('=')
        if name not in flags:
            continue
        value = value if sep else (args[i+1] if i+1 < len(args) else '')
        leaf = Path(value).name
        if not re.fullmatch(r'[\w.-]{1,180}', leaf):
            continue
        quant = re.search(r'(?:^|[-._])((?:I?Q\d+(?:_[A-Z0-9]+)*)|BF16|FP16|F16|FP8)(?=[-.]|$)',leaf,re.I)
        return {'model':leaf,'precision':quant.group(1) if quant else None}
    return None


def snapshot():
    cards = []
    if shutil.which('nvidia-smi'):
        rows = output(['nvidia-smi', '--query-gpu=index,uuid,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'])
        processes = output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'])
        active = {}
        for uuid, pid in csv.reader(processes.splitlines(),skipinitialspace=True):
            active.setdefault(uuid,[]).append(process_model(pid))
        for index, uuid, name, used, total, busy in csv.reader(rows.splitlines(),skipinitialspace=True):
            cards.append(dict(id='nvidia:'+index,name=name,usedMiB=number(used),totalMiB=number(total),
                              utilization=number(busy), workloads=active.get(uuid,[])))
    for device in sorted(Path('/sys/class/drm').glob('card[0-9]*/device')):
        if not (device/'mem_info_vram_total').is_file() or (device/'vendor').read_text().strip()!='0x1002':
            continue
        pci=device.resolve().name
        name='AMD '+(device/'device').read_text().strip()
        if shutil.which('lspci'):
            names = next(csv.reader([output(['lspci','-mm','-s',pci])],delimiter=' ',quotechar='"',skipinitialspace=True),[])
            if len(names)>=4:name=names[3]
        cards.append(dict(id=device.parent.name,name=name,usedMiB=int((device/'mem_info_vram_used').read_text())//1048576,
                          totalMiB=int((device/'mem_info_vram_total').read_text())//1048576,
                          utilization=number((device/'gpu_busy_percent').read_text().strip()), workloads=None))
    return {'version':1,'sampledAt':int(time.time()),'devices':cards}


def main():
    os.umask(0o077)
    dest=Path(os.environ['XDG_RUNTIME_DIR'])/'webos-gpu-monitor.json'
    if sys.argv[1:] == ['read']:
        value=json.loads(dest.read_bytes())
        if not 0 <= time.time()-value['sampledAt'] < 45:
            raise SystemExit('GPU snapshot expired')
        print(json.dumps(value))
        return
    if sys.argv[1:] != ['serve']:
        raise SystemExit('Expected serve or read')
    while True:
        data=snapshot()
        temp=dest.with_suffix('.tmp')
        temp.write_text(json.dumps(data));temp.replace(dest)
        time.sleep(10)


if __name__=='__main__':
    main()
