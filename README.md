# Clipsync

A simple Linux tool for synchronising all X11 clipboards. Clipsync runs in the 
background and watches all of the clipboards for any change.

Any of the following actions should be noticed for the purpose of copying text:

- CTRL-C in a desktop app (like Firefox)
- Highlighting text in a terminal (like urxvt or xterm)
- Putting text to the system clipboard (eg., with `:"*y` in vim)

Any of the following should work for pasting from any of the methods above:

- CTRL-V in a desktop app
- Middle mouse button in a terminal
- `"*p` in vim.

Basically anything that touches X11's CLIPBOARD, PRIMARY, or SECONDARY
selection buffers.

It's best to run this as a cron task, probably. If you try to start clipsync
with another process running already for that user, it will simply check to
make sure that the old process is running OK and exit. If the old PID is
defunct, clipsync will clean up the pidfile and start up again.

## Installation and usage:
```bash
$ git clone https://github.com/petronius/clipsync/
$ python clipsync/clipsync.py
```

I run it as a cron every minute. Copypasta:
```
*/1 *   *   *   *   python path/to/clipsync.py
```

## Optional arguments

For the sake of not having to modify the code on every box you want to run this
on, there are a couple of arguments you can pass in:

* `-f` -  Force Clipsync to run in the foreground (ie, it won't call `os.fork()`
  when started from a terminal). Good for debugging problems.
* `-p /pidfile/path` - Specify a PID file path. The default is
  `/tmp/clipsync.yourusername.pid`
* `-x /path/to/xsel` - If for some weird reason `xsel` isn't being found, you
  can pass in the path to run it from.

## Requirements

This should work fine with Python 2 or Python 3. Note that it requires `xsel` 
(which is part of X11) and assumes it can read `/proc/`.

## License

I hereby release this program into the public domain. Do with it what you will,
I take no responsibility for whatever happens.
