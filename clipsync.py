#!/usr/bin/env python

"""
USAGE:

    python clipsync.py

This should work fine with Python 2 or Python 3. Note that it requires xsel and
assumes it can read /proc/.

A simple Linux tool for synchronising all X11 clipboards. Any of the following
actions should be noticed for the purpose of copying text:

    - CTRL-C in a desktop app (like Firefox)
    - Highlighting text in a terminal (like urxvt or xterm)
    - Putting text to the system clipboard (eg., with `:"*y` in vim)

Any of the following should work for pasting from any of the methods above:

    - CTRL-V in a desktop app
    - Middle mouse button in a terminal
    - `"*p` in vim.

Basically anything that touches CLIPBOARD, PRIMARY, or SECONDARY in terms of
xsel buffers.

It's best to run this as a cron task, probably. If you try to start clipsync
with another process running already for that user, it will simply check to
make sure that the old process is running OK and exit. If the old PID is
defunct, clipsync will clean up the pidfile and start up again.
"""

import atexit
import os
import shlex
import sys
import subprocess
import time

current_clipboard = None
last_values = [None, None, None]

FLAGS = ('p', 's', 'b')

def run_command(command, inp = ''):
    p = subprocess.Popen(shlex.split(command), 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(inp)
    # xsel doesn't exist.
    if p.returncode == 127:
        sys.exit(os.EX_CONFIG)    
    elif p.returncode:
        raise OSError('Failed: '+command)
    else:
        return stdout

def sync_clipboards():
    
    global current_clipboard, last_values, FLAGS

    for idx, flag in enumerate(FLAGS):
        result = run_command('xsel -o'+flag)
        if result != last_values[idx] and result != current_clipboard:
            
            current_clipboard = result
            last_values[idx] = result
            
            for sflag in FLAGS:
                # If you re-set the value we just read, you end up screwing up
                # the UX when terminal text unhighlights and junk like that.
                # (It's also an unnecessary subprocess.)
                if sflag != flag:
                    run_command('xsel -i'+sflag, current_clipboard)

            break


if __name__ == "__main__":


    fork = os.fork()
    if fork:
        sys.exit(0)
    
    import sys
    args = sys.argv[1:]

    pid = os.getpid()
    pidfile = '/tmp/clipsync.pid'

    # If the process isn't actually running (determined by checking proc),
    # restart it. Not 100% reliable, but good enough.
    if os.path.exists(pidfile):
        with open(pidfile) as f:
            oldpid = f.read()
            oldproc = '/proc/'+oldpid
            if os.path.exists(oldproc):
                sys.exit(0)
            else:
                os.remove(pidfile)
        
    with open(pidfile, 'w') as f:
        f.write(str(pid))
    
    atexit.register(os.remove, pidfile)

    while True:
        sync_clipboards()
        # Too high and it's a waste of processing power. Too low and the
        # reaction time is too slow. I figure 100ms is usually okay.
        time.sleep(.1)


