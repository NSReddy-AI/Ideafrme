import json,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from qualify_ai_editorial import editorial_checks
class EditorialTests(unittest.TestCase):
 def raw(self,reasons):return json.dumps({'concepts':[{'direction':f'Direction {i}','rationale':r} for i,r in enumerate(reasons)]}).encode()
 def test_complete_sentences_pass_without_rewriting(self):
  reasons=['Calm spacing invites families to read together.','Clear hierarchy supports shared reading and discovery.','Open space makes the reading invitation welcoming.'];raw=self.raw(reasons);v=editorial_checks(raw);self.assertTrue(v['screen_pass']);self.assertEqual([x['rationale'] for x in v['checks']],reasons)
 def test_original_failures_rejected(self):
  reasons=['Guides the eye from a child’s curious gaze to a parent’s gentle smile, creatinga','Focuses on the connection between parent and child, with soft spacing that feels','Clear hierarchy supports shared reading and discovery.'];self.assertFalse(editorial_checks(self.raw(reasons))['screen_pass'])
 def test_period_does_not_hide_dangling_clause(self):
  self.assertFalse(editorial_checks(self.raw(['Calm spacing creates a.']*3))['screen_pass']);self.assertFalse(editorial_checks(self.raw(['Calm spacing feels.']*3))['screen_pass'])
 def test_no_silent_shortening_or_unsupported_imagery(self):
  self.assertFalse(editorial_checks(self.raw(['A'*81+'.']*3))['screen_pass']);self.assertFalse(editorial_checks(self.raw(['Photos invite families to read together.']*3))['screen_pass'])
 def test_exact_three_and_known_transport_marker(self):
  self.assertFalse(editorial_checks(self.raw(['Complete thought.']))['screen_pass']);v=editorial_checks(self.raw(['Calm spacing invites families to read together.']*3)+b' [end of text]\n');self.assertTrue(v['screen_pass'])
