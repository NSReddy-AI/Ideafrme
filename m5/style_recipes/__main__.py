"""Manual CLI. No server, rendering, media decoder, network, or creative.json writer."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
from .canonical import StyleError, loads, ref, require
from .schema import validate, ID, match
from .store import Store, WORKSPACE
from .manual import finding,recipe,edited,review,availability,association


def local_json(filename):
    path=Path(filename).absolute()
    require(path.is_relative_to(WORKSPACE) and '..' not in path.parts,'storage','$','input must be inside AI Studio')
    require(not any(p.is_symlink() for p in (path,*path.parents)),'storage','$','symlink input refused')
    # Open through handles so a replaced path cannot escape the read boundary.
    import os,stat
    fd=os.open(WORKSPACE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        parts=path.relative_to(WORKSPACE).parts
        for i,name in enumerate(parts):
            new=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|(os.O_DIRECTORY if i<len(parts)-1 else 0),dir_fd=fd)
            os.close(fd);fd=new
        st=os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=1048576,'storage','$','bounded regular JSON input required')
        raw=os.read(fd,1048577)
        return loads(raw)
    finally:os.close(fd)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',required=True,help='new/existing directory under AI Studio/r1_data')
    parser.add_argument('--actor',help='stable local reviewer UUID; plain files are not authenticated signatures')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('init');sub.add_parser('list');sub.add_parser('qualify')
    p=sub.add_parser('show');p.add_argument('hash')
    p=sub.add_parser('new');p.add_argument('--name',required=True);p.add_argument('--property');p.add_argument('--value-json')
    p=sub.add_parser('edit');p.add_argument('hash');p.add_argument('--name');p.add_argument('--property');p.add_argument('--value-json');p.add_argument('--reason')
    p=sub.add_parser('write');p.add_argument('file');p.add_argument('--action',default='save',choices=['save','rights-decision']);p.add_argument('--confirm',action='store_true');p.add_argument('--brand-classification',choices=['benign','adverse'])
    p=sub.add_parser('review');p.add_argument('hash');p.add_argument('--decision',required=True,choices=['approve','exclude','reject','revoke']);p.add_argument('--authority',required=True,choices=['A','B','C']);p.add_argument('--reason',required=True);p.add_argument('--verified-evidence');p.add_argument('--confirm',action='store_true')
    p=sub.add_parser('availability');p.add_argument('hash');p.add_argument('--state',required=True);p.add_argument('--reason',required=True);p.add_argument('--confirm',action='store_true')
    p=sub.add_parser('eligibility');p.add_argument('hash');p.add_argument('--project-id')
    sub.add_parser('recovery-status')
    p=sub.add_parser('recover');p.add_argument('--generation-json',required=True);p.add_argument('--confirm',action='store_true')
    p=sub.add_parser('associate');p.add_argument('hash');p.add_argument('--project-id',required=True);p.add_argument('--synthetic-creative-json',required=True)
    args=parser.parse_args(argv);now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    try:
        store=Store(args.store)
        if args.command=='init':
            Store.create(args.store);print('Created qualified local R1 store. No project modified.');return 0
        if args.command=='qualify':
            print(json.dumps(store.qualify()));return 0
        if args.command=='recovery-status':
            print(json.dumps(store.recovery_generation(),sort_keys=True));return 0
        if args.command=='recover':
            match(args.actor,ID)
            result=store.recover(loads(args.generation_json.encode()),args.actor,now,confirmed=args.confirm)
            print(json.dumps(result));return 0
        snap=store.read()
        def get_hash(h):
            from .schema import HASH
            match(h,HASH)
            require(h in snap.visible,'reference','$','hash not committed')
            return snap.visible[h]
        if args.command=='list':
            print(json.dumps({'head':snap.head,'roots':snap.roots},indent=2));return 0
        if args.command=='show':
            print(json.dumps(get_hash(args.hash),ensure_ascii=False,indent=2));return 0
        if args.command=='eligibility':
            result=snap.eligible(ref(get_hash(args.hash)),now,args.project_id)
            print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['eligible'] else 2
        match(args.actor,ID);extra={};action='save'
        if args.command=='new':
            fs=[]
            require((args.property is None)==(args.value_json is None),'schema','$','property and typed value together')
            if args.property:fs=[finding(args.actor,now,args.property,loads(args.value_json.encode()))]
            p=recipe(args.actor,now,args.name,fs);additions=fs+[p]
        elif args.command=='edit':
            require(args.name is not None or args.property is not None,'schema','$','edit needs a change')
            require((args.property is None)==(args.value_json is None),'schema','$','property and typed value together')
            additions,p=edited(snap,get_hash(args.hash),args.actor,now,args.name,args.property,
                               loads(args.value_json.encode()) if args.value_json else None,args.reason)
        elif args.command=='write':
            data=local_json(args.file);additions=data if type(data) is list else [data]
            for p in additions:validate(p)
            action=args.action;extra=dict(confirmed=args.confirm,brand_classification=args.brand_classification)
        elif args.command=='review':
            additions=[review(snap,ref(get_hash(args.hash)),args.actor,now,args.decision,args.authority,args.reason)]
            action='review';extra=dict(confirmed=args.confirm,verified_evidence=args.verified_evidence)
        elif args.command=='availability':
            additions=[availability(snap,ref(get_hash(args.hash)),args.actor,now,args.state,args.reason)]
            action='dependency-event';extra=dict(confirmed=args.confirm)
        elif args.command=='associate':
            # Validate a synthetic creative@1 input using its unchanged existing validator.
            from creative_core.validation import validate as validate_creative
            from creative_core.document import fingerprint
            creative=local_json(args.synthetic_creative_json)
            require(creative['id'].startswith('synthetic-'),'schema','$','R1 associations are synthetic-only')
            validate_creative(creative,WORKSPACE)
            additions=[association(snap,ref(get_hash(args.hash)),args.actor,now,args.project_id,
                dict(format=creative['format'],id=creative['id'],fingerprint=fingerprint(creative)))]
            action='associate'
        result=store.commit(additions,snap.head,args.actor,now,action=action,**extra)
        print(json.dumps({'head':result,'records':[ref(p) for p in additions]},ensure_ascii=False,indent=2));return 0
    except (StyleError,OSError,KeyError) as e:
        print(str(e),file=sys.stderr);return 2


if __name__=='__main__':
    raise SystemExit(main())
