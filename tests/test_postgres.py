"""Integração real: TEST_POSTGRES_URL aponta exclusivamente para um banco descartável.
Os testes limpam as tabelas de aplicação desse banco. Nunca usar dados reais.
"""
import os,unittest,threading
import app
from test_domain import Workflow as _Workflow
from test_http import EndToEnd as _HTTP
from test_connector import Backend as _ConnectorBackend
from test_portal import PublicPortal as _PublicPortal
URL=os.environ.get('TEST_POSTGRES_URL')
def reset():
 with app.connect(URL) as d:
  app.migrate(d)
  d.execute('TRUNCATE users,sessions,opportunities,contents,versions,reviews,approvals,publications,metrics,runs,assets,audit RESTART IDENTITY CASCADE')
@unittest.skipUnless(URL,'TEST_POSTGRES_URL não configurada')
class PostgresDomain(_Workflow):
 def setUp(self):
  reset();self.d=app.connect(URL)
  self.d.execute("INSERT INTO users(id,email,password,role) VALUES(1,'test','hash','admin')")
  self.d.execute("INSERT INTO opportunities(id,title) VALUES(1,'Plantas')")
  self.d.execute("INSERT INTO contents(id,opportunity_id,title,slug,brief) VALUES(1,1,'Plantas','plantas','brief')")
 def test_migration_is_idempotent(self):
  self.d.commit();app.migrate(self.d);app.migrate(self.d)
  self.assertEqual(self.d.execute('SELECT count(*) FROM users').fetchone()[0],1)
@unittest.skipUnless(URL,'TEST_POSTGRES_URL não configurada')
class PostgresHTTP(_HTTP):
 @classmethod
 def setUpClass(cls):
  cls.old_db=app.DB;app.DB=URL;reset()
  with app.connect(URL) as d:
   for role in ['admin','editor','reviewer']:d.execute('INSERT INTO users(email,password,role) VALUES(?,?,?)',(role,app.password('test-password-123'),role))
  cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.base='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();app.DB=cls.old_db
# Evita que unittest colete novamente as classes importadas.
@unittest.skipUnless(URL,'TEST_POSTGRES_URL não configurada')
class PostgresConnector(_ConnectorBackend):
 def setUp(self):
  reset();self.d=app.connect(URL);self.seed()
@unittest.skipUnless(URL,'TEST_POSTGRES_URL não configurada')
class PostgresPortal(_PublicPortal):
 @classmethod
 def setUpClass(cls):PostgresHTTP.setUpClass.__func__(cls)
 @classmethod
 def tearDownClass(cls):PostgresHTTP.tearDownClass.__func__(cls)
del _Workflow,_HTTP,_ConnectorBackend,_PublicPortal
