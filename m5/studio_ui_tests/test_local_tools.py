import hashlib,json,os,sys,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import studio_local as local

class LocalToolsTests(unittest.TestCase):
    def test_inventory_no_optional_engine_dependency(self):
        r=local.inventory();self.assertTrue(r['ready_for_local_start']);self.assertEqual(r['runtime']['third_party_python_packages_required'],[]);self.assertEqual(len(r['fonts']),2);self.assertFalse(r['independence']['clean_offline_install_verified'])
    def test_source_allowlist_excludes_protected_and_runtime(self):
        names=local.source_paths()
        self.assertTrue(all(not any(v in n for v in ['style_recipes','r1_tests','.runtime','media_analysis_agent']) for n in names));self.assertIn('visual_poster_tests/browser_acceptance.js',names)
    def test_font_mismatch_refuses_readiness(self):
        original=local.regular
        def bad(p):return b'changed' if p.name=='Inter-Bold.otf' else original(p)
        with patch.object(local,'regular',side_effect=bad):self.assertFalse(local.inventory()['ready_for_local_start'])
    def test_bad_names_and_outside_output(self):
        for name in ['../bad','/bad','a/b','', 'a'*65]:
            with self.assertRaises(ValueError):local.build_kit(name)
        with self.assertRaises(ValueError):local.build_kit('outside',parent=ROOT)
    def test_deterministic_kit_and_notices(self):
        parent=Path(os.environ['LOCAL_TEST_ROOT'])/'kits'
        a=local.build_kit('one',parent=parent);b=local.build_kit('two',parent=parent);self.assertEqual(a['sha256'],b['sha256'])
        with zipfile.ZipFile(Path(a['directory'])/'manual-studio-source.zip') as z:
            manifest=json.loads(z.read('LOCAL_KIT_MANIFEST.json'));self.assertFalse(manifest['release_approved'])
            for name,record in manifest['files'].items():self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),record['sha256'])
            for name in ['Inter-Bold.otf','NotoSansTelugu-Black.ttf']:self.assertIn(b'Copyright',z.read('examples/posters/assets/fonts/'+name+'.LICENSE.txt'))
        with self.assertRaises(FileExistsError):local.build_kit('one',parent=parent)
    def test_symlink_write_refused(self):
        parent=Path(os.environ['LOCAL_TEST_ROOT']);link=parent/'alias';link.symlink_to(parent,target_is_directory=True)
        with self.assertRaises(ValueError):local.build_kit('symlink',parent=link)
    def test_source_symlink_refused(self):
        parent=Path(os.environ['LOCAL_TEST_ROOT']);source=parent/'source';source.write_text('x');link=parent/'source-alias';link.symlink_to(source)
        with self.assertRaises(ValueError):local.regular(link)
