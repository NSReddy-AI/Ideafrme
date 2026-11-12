"""Subprocess-only acceptance worker. No use by the manual application."""
import json
import os
import resource
import signal
import socket
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from style_recipes.canonical import StyleError,loads
from style_recipes.store import Store
from style_recipes.manual import recipe
from r1_tests.helpers import ACTOR,NOW

mode,path,configuration=sys.argv[1:]
config=json.loads(configuration)
s=Store(path)
try:
    s.qualify()
    if mode=='crash':
        seen=0
        def fault(stage):
            global seen
            if stage==config['stage']:
                seen+=1
                if seen==config.get('occurrence',1):os._exit(77)
        s.fault=fault
        snap=s.read();p=recipe(ACTOR,NOW,'Crash transaction')
        s.commit([p],snap.head,ACTOR,NOW)
    elif mode=='recovery-crash':
        def fault(stage):
            if stage==config['stage']:os._exit(77)
        s.fault=fault
        s.recover(config['generation'],ACTOR,NOW,confirmed=True)
    elif mode=='race':
        p=recipe(ACTOR,NOW,'Concurrent writer')
        s.commit([p],config['expected'],ACTOR,NOW)
    elif mode=='file-limit':
        resource.setrlimit(resource.RLIMIT_FSIZE,(128,128))
        snap=s.read();p=recipe(ACTOR,NOW,'Bounded real write failure')
        s.commit([p],snap.head,ACTOR,NOW)
    elif mode=='signal-kill':
        def ready(stage):
            if stage=='after:record:create':
                (s.path/'staging'/'kill-ready').write_bytes(b'ready')
                signal.pause()
        s.fault=ready
        snap=s.read();s.commit([recipe(ACTOR,NOW,'Killed writer')],snap.head,ACTOR,NOW)
    elif mode=='isolation':
        network_denied=False
        try:
            with socket.socket() as sock:sock.connect(('127.0.0.1',9))
        except OSError as e:
            network_denied=e.errno in (1,13)
        if not network_denied:raise StyleError('storage','$','network denial not established')
        outside=s.path.parents[3]/('r1-denied-'+str(os.getpid()))
        write_denied=False
        try:
            with outside.open('xb') as file:file.write(b'unexpected')
        except PermissionError:write_denied=True
        else:outside.unlink()
        if not write_denied:raise StyleError('storage','$','OS write boundary not established')
        print(json.dumps(dict(network_denied=True,write_outside_r1_denied=True)))
    else:raise ValueError('unknown worker mode')
except (StyleError,OSError) as e:
    print(str(e));raise SystemExit(2)
