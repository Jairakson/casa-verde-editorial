import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from domain import *
class Workflow(unittest.TestCase):
 def setUp(self):
  self.d=connect(':memory:');migrate(self.d)
  self.d.execute("INSERT INTO users VALUES(1,'test','hash','admin')")
  self.d.execute("INSERT INTO opportunities(id,title) VALUES(1,'Plantas')")
  self.d.execute("INSERT INTO contents(id,opportunity_id,title,slug,brief) VALUES(1,1,'Plantas','plantas','brief')")
 def tearDown(self):self.d.close()
 def test_missing_data(self):
  r=ranking([None,80,None,60,100],[25,25,20,20,10]);self.assertEqual(r['coverage'],55);self.assertTrue(r['provisional']);self.assertIsNone(r['contributions'][0]);self.assertGreater(r['score'],60)
 def test_critical_blocks(self):
  save_version(self.d,1,1,'Título','Texto');review(self.d,1,1,'bloqueado','Crítico: sem fonte','não verificado')
  with self.assertRaises(ValueError):approve(self.d,1,1)
  with self.assertRaises(ValueError):publish(self.d,1,1)
 def test_exact_version_and_idempotency(self):
  save_version(self.d,1,1,'Título','Texto');review(self.d,1,1,'aprovado','','Fonte conferida');approve(self.d,1,1);publish(self.d,1,1);publish(self.d,1,1)
  self.assertEqual(self.d.execute('SELECT count(*) FROM publications').fetchone()[0],1)
  old=self.d.execute('SELECT version_id FROM publications').fetchone()[0]
  save_version(self.d,1,1,'Título novo','Texto alterado')
  with self.assertRaises(ValueError):publish(self.d,1,1)
  self.assertEqual(self.d.execute('SELECT version_id FROM publications').fetchone()[0],old)
  self.assertEqual(self.d.execute('SELECT count(*) FROM versions').fetchone()[0],2)
 def test_new_review_revokes_approval(self):
  save_version(self.d,1,1,'Título','Texto');review(self.d,1,1,'aprovado','','Fontes verificadas');approve(self.d,1,1);review(self.d,1,1,'ajustes','Reavaliar fonte','')
  self.assertEqual(self.d.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
 def test_claims_block(self):
  save_version(self.d,1,1,'Título','Texto','Fato pendente')
  with self.assertRaises(ValueError):review(self.d,1,1,'aprovado','','Fontes')
 def test_required_assets(self):
  save_version(self.d,1,1,'Título','Texto');review(self.d,1,1,'aprovado','','Fontes')
  self.d.execute("INSERT INTO assets(content_id,kind,status,required) VALUES(1,'Capa','pendente',1)")
  with self.assertRaises(ValueError):approve(self.d,1,1)
 def test_url(self):
  for url in ['javascript:alert(1)','https://user:secret@example.com','file:///tmp/test']:
   with self.assertRaises(ValueError):valid_url(url)
 def test_bad_weights(self):
  with self.assertRaises(ValueError):ranking([None]*5,[10]*5)
if __name__=='__main__':unittest.main()

class Assistants(unittest.TestCase):
 def test_idempotent_structured_execution(self):
  from agents import execute
  d=connect(':memory:');migrate(d)
  d.execute("INSERT INTO opportunities(id,title,kind,keyword,sources) VALUES(1,'DEMONSTRAÇÃO','Tutorial','plantas','https://example.org')")
  d.execute("INSERT INTO contents(id,opportunity_id,title,slug) VALUES(1,1,'DEMONSTRAÇÃO','demo')")
  first=execute(d,1,'estrategia');second=execute(d,1,'estrategia');self.assertEqual(first,second)
  run=d.execute('SELECT * FROM runs').fetchone();self.assertEqual(run['provider'],'local-deterministico');self.assertEqual(run['cost'],0);self.assertIn('objetivo',json.loads(run['output']));d.close()
