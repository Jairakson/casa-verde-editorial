import unittest,tempfile,threading,urllib.request,urllib.error,urllib.parse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
class HTTP(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();app.DB=cls.tmp.name+'/test.db'
  with app.connect(app.DB) as d:
   app.migrate(d)
   for role in ['admin','editor','reviewer']:d.execute('INSERT INTO users(email,password,role) VALUES(?,?,?)',(role,app.password('test-password-123'),role))
  cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.base='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.tmp.cleanup()
 def request(self,path,data=None,cookie=None):
  r=urllib.request.Request(self.base+path,data=urllib.parse.urlencode(data).encode() if data else None,headers={'Cookie':cookie} if cookie else {})
  try:
   with urllib.request.urlopen(r) as res:return res.status,res.read().decode()
  except urllib.error.HTTPError as e:return e.code,e.read().decode()
 def identity(self,role):
  with app.connect(app.DB) as d:
   uid=d.execute('SELECT id FROM users WHERE role=?',(role,)).fetchone()[0];d.execute('INSERT OR REPLACE INTO sessions VALUES(?,?,?,?)',(role,uid,'csrf',app.time.time()+60))
  return 'session='+role
 def test_anonymous(self):self.assertIn('Entrar',self.request('/editorial')[1]);self.assertEqual(self.request('/action',{'action':'publish'})[0],401)
 def test_csrf(self):self.assertEqual(self.request('/action',{'action':'settings'},self.identity('admin'))[0],403)
 def test_permissions(self):self.assertEqual(self.request('/action',{'action':'publish','csrf':'csrf'},self.identity('editor'))[0],403)
 def test_pages(self):
  cookie=self.identity('admin')
  for path in ['/','/editorial','/oportunidades','/midia','/calendario','/analytics','/agentes','/configuracoes','/portal','/sitemap.xml']:
   self.assertEqual(self.request(path,cookie=cookie)[0],200,path)
if __name__=='__main__':unittest.main()

class EndToEnd(HTTP):
 def test_editorial_flow(self):
  import json
  admin=self.identity('admin');editor=self.identity('editor');reviewer=self.identity('reviewer')
  def post(cookie,**data):return self.request('/action',dict(csrf='csrf',**data),cookie)
  self.assertEqual(post(editor,action='opportunity',title='[TESTE] Horta pequena',category='Hortas em vasos',kind='Tutorial',keyword='horta',sources='https://www.embrapa.br/',context='Fonte a conferir')[0],200)
  with app.connect(app.DB) as d:oid=d.execute("SELECT id FROM opportunities WHERE title='[TESTE] Horta pequena' ORDER BY id DESC").fetchone()[0]
  self.assertEqual(post(editor,action='op_decision',id=oid,status='aprovada',reason='Aderente ao público')[0],200)
  with app.connect(app.DB) as d:cid=d.execute('SELECT id FROM contents WHERE opportunity_id=?',(oid,)).fetchone()[0]
  self.assertEqual(post(editor,action='brief',id=cid,brief='Objetivo e estrutura com fontes',responsible='Editor')[0],200)
  self.assertEqual(post(editor,action='version',id=cid,title='Horta pequena',body='Orientações com contexto. Referência: https://www.embrapa.br/')[0],200)
  self.assertEqual(post(admin,action='publish',id=cid)[0],400)
  self.assertEqual(post(reviewer,action='review',id=cid,result='aprovado',issues='',limitations='Fonte conferida manualmente pelo teste; dados fictícios.')[0],200)
  self.assertEqual(post(admin,action='approve',id=cid)[0],200)
  self.assertEqual(post(admin,action='publish',id=cid)[0],200)
  self.assertEqual(post(admin,action='publish',id=cid)[0],200)
  text=f'content_id,source,start,end,name,value,kind\n{cid},TESTE,2026-10-01,2026-10-31,cliques,10,confirmado\n'
  self.assertEqual(post(editor,action='metrics',csv=text)[0],200);self.assertEqual(post(editor,action='metrics',csv=text)[0],200)
  with app.connect(app.DB) as d:
   self.assertEqual(d.execute('SELECT count(*) FROM publications WHERE content_id=?',(cid,)).fetchone()[0],1)
   self.assertEqual(d.execute('SELECT count(*) FROM metrics WHERE content_id=?',(cid,)).fetchone()[0],1)
  self.assertEqual(post(editor,action='version',id=cid,title='Nova versão',body='Texto alterado')[0],200)
  self.assertEqual(post(admin,action='publish',id=cid)[0],400)
  self.assertIn('Horta pequena',self.request('/portal/pauta-'+str(oid))[1])
  self.assertNotIn('Nova versão',self.request('/portal/pauta-'+str(oid))[1])
