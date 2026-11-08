#!/usr/bin/env python3
"""Save a personal Go key from a hidden local terminal prompt; never accepts CLI secrets."""
import getpass
import os
from pathlib import Path
import sys
import tempfile

KEY_PATH=Path.home()/'.local/share/ism-ai-review/opencode-go.key'

def save_key(key,path=KEY_PATH):
    if len(key)<20 or any(c.isspace() for c in key):
        raise ValueError('That does not look like a complete API key. Copy the key itself and try again.')
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(path.parent,0o700)
    fd,temp=tempfile.mkstemp(prefix='.go-key-',dir=path.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w') as out:
            out.write(key+'\n');out.flush();os.fsync(out.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def main():
    if len(sys.argv)!=1:raise SystemExit('Run this command without arguments. Paste the key only at the hidden prompt.')
    if not sys.stdin.isatty():raise SystemExit('Run this in your own terminal so the API key stays hidden.')
    print('OpenCode Console → Account → Personal API keys → Add API key.')
    print('Choose the workspace with Go. If permissions are shown, choose Restricted → Models: Request.')
    print('Copy the new key. Paste it below and press Enter. Nothing will appear while pasting.')
    try:
        key=getpass.getpass('Paste your Go personal API key: ').strip()
        if not key:raise ValueError('No key entered; nothing saved.')
        save_key(key)
    except (KeyboardInterrupt,EOFError):raise SystemExit('\nCancelled; no new key saved.')
    except (ValueError,OSError) as exc:raise SystemExit(str(exc))
    print('Key saved privately on this computer. It was not printed or sent to chat.')
    print('No model request was made. Return to the chat and say: done')

if __name__=='__main__':main()
