#!/usr/bin/env python

"""
USAGE:

    python clipsync.py [-p pidfile] [-f] [-x xsel_path]

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
import pwd
import shlex
import sys
import subprocess
import time

FLAGS = ('p', 's', 'b')
XSEL_PATH='xsel'

current_clipboard = None
last_values = [None, None, None]

def run_command(command, inp = ''):
    p = subprocess.Popen(shlex.split(command), 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(inp)
    if p.returncode == 127:
        # xsel doesn't exist or it isn't in the path.
        sys.exit(os.EX_CONFIG)    
    elif p.returncode:
        raise OSError('`'+command+'` failed: '+stderr)
    else:
        return stdout

def sync_clipboards():
    
    global current_clipboard, last_values, FLAGS

    for idx, flag in enumerate(FLAGS):
        result = run_command(XSEL_PATH+' -o'+flag)
        if result != last_values[idx] and result != current_clipboard:
            
            current_clipboard = result
            last_values[idx] = result
            
            for sflag in FLAGS:
                # If you re-set the value we just read, you end up screwing up
                # the UX when terminal text unhighlights and junk like that.
                # (It's also an unnecessary subprocess.)
                if sflag != flag:
                    run_command(XSEL_PATH+' -i'+sflag, current_clipboard)

            break

if __name__ == "__main__":
    
    import sys

    args = sys.argv[1:]
    isatty = sys.stdin.isatty()
    pidfile = None

    def q(doc):
        sys.stderr.write(doc+'\n')
        sys.exit(os.EX_USAGE)

    # Quick and dirtry argument parsing
    skipnext = False
    for idx, arg in enumerate(args):
        if skipnext:
            skipnext = False
            continue
        if arg == '-f':
            isatty = False
        elif arg == '-x':
            try:
                XSEL_PATH = args[idx + 1]
                skipnext = True
            except IndexError:
                q(__doc__)
        elif arg == '-p':
            try:
                pidfile = args[idx + 1]
                skipnext = True
            except IndexError:
                q(__doc__)
        else:
            q(__doc__)

    # Daemonize yourself if you're being run from a terminal. Otherwise it's
    # probably a cron task or something like that, and we will want to exit with
    # a proper exit code if anything goes wrong.
    if isatty:
        fork = os.fork()
        if fork:
            sys.exit(0)

    pid = os.getpid()
    user = pwd.getpwuid(os.getuid())[0]
    if not pidfile:
        pidfile = '/tmp/clipsync.'+user+'.pid'

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


