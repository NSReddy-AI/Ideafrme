import copy
import os
from pathlib import Path
import unittest
import uuid
from studio_manual_ui.service import UIError
from visual_poster_studio.service import VisualStudio

class ServiceCase(unittest.TestCase):
    def setUp(self):
        self.root=Path(os.environ['VISUAL_TEST_ROOT'])/('case-'+uuid.uuid4().hex)
        self.s=VisualStudio(self.root)
        self.addCleanup(self.s.close)
        self.p=self.s.create({'name':'Synthetic acceptance','text':'తెలుగు శ్రీ\nEnglish é','language':'te'})
    def action(self,kind,**extras):
        self.p=self.s.action({'project_id':self.p['project_id'],'expected_revision':self.p['revision'],'action':kind,**extras});return self.p
    def test_create_schema(self):
        d=self.s.manual.document(self.p['project_id']);self.assertEqual(d['format'],'ai-reel-studio/creative@1');self.assertEqual(d['assets'],[])
    def test_edit_undo_redo(self):
        identity=self.p['elements'][0]['id'];before=self.p['content'][0]['text']
        self.action('edit_text',element_id=identity,text='శ్రీ విద్య é');self.action('undo');self.assertEqual(self.p['content'][0]['text'],before)
        self.action('redo');self.assertEqual(self.p['content'][0]['text'],'శ్రీ విద్య é');self.assertEqual(self.p['approval_count'],0)
    def test_save_reopen(self):
        expected=self.p['content'][0]['text'];self.action('save');p=self.s.reopen(self.p['project_id'],self.p['revision']);self.assertEqual(p['content'][0]['text'],expected)
    def test_stale_action(self):
        self.action('move',element_id=self.p['elements'][0]['id'],x=90,y=120)
        with self.assertRaises(UIError):self.s.action({'project_id':self.p['project_id'],'expected_revision':0,'action':'undo'})
    def test_bad_path(self):
        with self.assertRaises(UIError):self.s.view('../outside')
    def test_analysis_off(self):self.assertFalse(self.s.analysis()['enabled'])
    def test_line_budget(self):
        before=self.s.manual.document(self.p['project_id'])
        with self.assertRaises(UIError):self.action('edit_text',element_id=self.p['elements'][0]['id'],text='x\n'*64)
        self.assertEqual(before,self.s.manual.document(self.p['project_id']))
    def test_active_text_budget(self):
        ids=[self.p['elements'][0]['id']]
        for i in range(2):self.action('add_text',language='en');ids.append(self.p['elements'][-1]['id'])
        for identity in ids[:2]:self.action('edit_text',element_id=identity,text='a'*9990)
        with self.assertRaises(UIError):self.action('edit_text',element_id=ids[2],text='a'*100)
    def test_export_stale(self):
        begin=self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
        self.action('move',element_id=self.p['elements'][0]['id'],x=90,y=120)
        with self.assertRaises(UIError):self.s.finish({'token':begin['token'],'revision':0,'png':None,'qa':{'fonts_loaded':True,'overflow':[],'parity':False,'embedded_fonts':False}})
        self.assertEqual(list(self.s.exports.root.iterdir()),[])
    def test_export_busy(self):
        self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
        with self.assertRaises(UIError):self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
    def test_export_svg_and_duplicate(self):
        begin=self.s.begin({'project_id':self.p['project_id'],'expected_revision':0});r={'token':begin['token'],'revision':0,'png':None,'qa':{'fonts_loaded':True,'overflow':[],'parity':False,'embedded_fonts':False}}
        result=self.s.finish(r);self.assertEqual((Path(result['directory'])/'poster.draft.svg').read_text(),begin['scene']['svg']);self.assertTrue(result['manifest']['draft'])
        with self.assertRaises(UIError):self.s.finish(r)
    def test_export_expiry(self):
        b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':0});self.s.exports.pending['started']-=16
        with self.assertRaises(UIError):self.s.finish({'token':b['token'],'revision':0,'png':None,'qa':{}})
    def test_export_overflow_refused(self):
        b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
        with self.assertRaises(UIError):self.s.finish({'token':b['token'],'revision':0,'png':None,'qa':{'fonts_loaded':True,'overflow':['title'],'parity':False,'embedded_fonts':False}})
    def test_export_count(self):
        for i in range(20):(self.s.exports.root/str(i)).mkdir()
        with self.assertRaises(UIError):self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
    def test_export_png_reject(self):
        b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
        with self.assertRaises(UIError):self.s.finish({'token':b['token'],'revision':0,'png':'bad','qa':{'fonts_loaded':True,'overflow':[],'parity':True,'embedded_fonts':True}})

    def test_export_storage_budget(self):
        from unittest.mock import patch
        b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
        with patch('visual_poster_studio.exports.MAX_STORAGE',1):
            with self.assertRaises(UIError):self.s.finish({'token':b['token'],'revision':0,'png':None,'qa':{'fonts_loaded':True,'overflow':[],'parity':False,'embedded_fonts':False}})
        self.assertEqual(list(self.s.exports.root.iterdir()),[])
    def test_export_bad_revision_type(self):
        b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
        with self.assertRaises(UIError):self.s.finish({'token':b['token'],'revision':False,'png':None,'qa':{}})
    def test_export_symlink(self):
        from studio_manual_ui.service import safe
        target=self.root/'legitimate';target.mkdir();alias=self.s.exports.root/'alias';alias.symlink_to(target)
        b=self.s.begin({'project_id':self.p['project_id'],'expected_revision':0})
        with self.assertRaises(UIError):self.s.finish({'token':b['token'],'revision':0,'png':None,'qa':{'fonts_loaded':True,'overflow':[],'parity':False,'embedded_fonts':False}})
        self.assertEqual(list(target.iterdir()),[])
    def test_snapshot_alias_refused(self):
        self.action('save');path=self.s.manual._directory(self.p['project_id'])/'creative.json'
        os.link(path,path.with_name('alias.json'))
        with self.assertRaises(UIError):self.s.reopen(self.p['project_id'],self.p['revision'])
    def test_no_approval_resurrection(self):
        self.action('move',element_id=self.p['elements'][0]['id'],x=100,y=100)
        self.action('undo');self.action('redo');self.assertEqual(self.p['approval_count'],0)
