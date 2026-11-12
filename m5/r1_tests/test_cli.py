import json
import subprocess
import sys
import unittest
from uuid import uuid4
from style_recipes.store import WORKSPACE
from .helpers import ACTOR


class ManualCLITests(unittest.TestCase):
    def test_actual_manual_cli_create_edit_and_invalid_input(self):
        store=WORKSPACE/'.runtime/r1/tests'/str(uuid4())
        def run(*args):
            return subprocess.run([sys.executable,'-B','-m','style_recipes','--store',str(store),'--actor',ACTOR,*args],
                cwd=WORKSPACE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        self.assertEqual(run('init').returncode,0)
        p=run('new','--name','తెలుగు / English','--property','palette.primary',
              '--value-json','{"kind":"color","rgba":"#112233ff"}')
        self.assertEqual(p.returncode,0,p.stderr)
        record=json.loads(p.stdout)['records'][-1]['sha256']
        p=run('show',record);self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)['name'],'తెలుగు / English')
        p=run('edit',record,'--name','New immutable revision');self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(run('show',record).returncode,0)
        self.assertEqual(run('new','--name','invalid','--property','motion.duration','--value-json','{"kind":"text","value":"x"}').returncode,2)
        self.assertEqual(run('review',record,'--decision','approve','--authority','A','--reason','No confirmation').returncode,2)
