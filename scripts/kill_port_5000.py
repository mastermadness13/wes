#!/usr/bin/env python3
import subprocess
import re

def main():
    try:
        out = subprocess.check_output('netstat -ano', shell=True, text=True, stderr=subprocess.DEVNULL)
    except Exception as e:
        print('Failed to run netstat:', e)
        return

    pids = set()
    for line in out.splitlines():
        if ':5000' in line:
            m = re.search(r"\s+(\d+)$", line.strip())
            if m:
                pids.add(m.group(1))

    if not pids:
        print('No process found on port 5000')
        return

    for pid in pids:
        try:
            subprocess.run(['taskkill', '/PID', pid, '/F'], check=True)
            print('Killed', pid)
        except Exception as e:
            print('Failed to kill', pid, e)

if __name__ == '__main__':
    main()
