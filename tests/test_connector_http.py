import json,urllib.request,urllib.error
from test_http import HTTP as _HTTP
class ConnectorAPI(_HTTP):
 def api(self,path,payload,token=None,origin=None):
  headers={'Content-Type':'application/json'}
  if token:headers['Authorization']='Bearer '+token
  if origin:headers['Origin']=origin
  req=urllib.request.Request(self.base+'/api/connector/'+path,data=json.dumps(payload).encode(),headers=headers)
  try:
   with urllib.request.urlopen(req) as response:return response.status,json.loads(response.read())
  except urllib.error.HTTPError as error:return error.code,json.loads(error.read())
 def test_pair_approval_authentication_revocation(self):
  code,pair=self.api('pair/start',{});self.assertEqual(code,200)
  self.assertEqual(self.api('pair/poll',{'device_code':pair['device_code']})[1]['status'],'pending')
  data={'action':'pair_approve','csrf':'csrf','code':pair['user_code']}
  self.assertEqual(self.request('/action',data,self.identity('editor'))[0],403)
  self.assertEqual(self.request('/action',data,self.identity('admin'))[0],200)
  status,credentials=self.api('pair/poll',{'device_code':pair['device_code']});self.assertEqual(status,200)
  token=credentials['device_token']
  self.assertEqual(self.api('next',{},token)[0],200)
  self.assertEqual(self.api('pair/poll',{'device_code':pair['device_code']})[0],400)
  self.assertEqual(self.request('/action',{'action':'device_revoke','csrf':'csrf','device_id':credentials['device_id']},self.identity('admin'))[0],200)
  self.assertEqual(self.api('next',{},token)[0],401)
 def test_cookie_does_not_authorize_connector_api(self):
  self.assertEqual(self.api('next',{})[0],401)
  self.assertEqual(self.api('next',{},origin='https://evil.example')[0],403)
 def test_pair_approval_requires_csrf(self):
  self.assertEqual(self.request('/action',{'action':'pair_approve','code':'1234'},self.identity('admin'))[0],403)
 def test_local_connector_delivers_draft_over_http(self):
  import app,io,tempfile
  from connector.security import Store
  from connector import runtime,panel
  from unittest.mock import patch
  admin=self.identity('admin');editor=self.identity('editor')
  with app.connect(app.DB) as d:
   oid=d.execute("INSERT INTO opportunities(title,sources,scores,category,kind) VALUES('Conector E2E','https://example.org/source','[null,null,null,null,null]','Hortas em vasos','Tutorial') RETURNING id").fetchone()[0]
   cid=d.execute("INSERT INTO contents(opportunity_id,title,slug,brief) VALUES(?,?,?,'Brief aprovado') RETURNING id",(oid,'Conector E2E','conector-e2e')).fetchone()[0]
  self.assertEqual(self.request('/action',{'action':'plus_enqueue','csrf':'csrf','id':cid,'agent':'redacao'},editor)[0],200)
  _,pair=self.api('pair/start',{})
  self.request('/action',{'action':'pair_approve','csrf':'csrf','code':pair['user_code']},admin)
  _,credentials=self.api('pair/poll',{'device_code':pair['device_code']})
  result={'entrega':{'titulo':'Rascunho pelo Plus','corpo':'Texto para revisão humana.'},'afirmacoes_pendentes':[],'fontes_usadas':['https://example.org/source'],'limitacoes':['Teste sintético, sem uso de uma conta real.']}
  events=[{'type':'response.output_text.delta','delta':json.dumps(result)},{'type':'response.completed','response':{'status':'completed','usage':{'total_tokens':15}}}]
  stream=b''.join(b'data: '+json.dumps(event).encode()+b'\n\n' for event in events)
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder);store.write({'accounts':{},'panel':{'base':self.base,'device_token':credentials['device_token']}})
   job=panel.call(store,'next')['job']
   with patch('connector.runtime.access_token',return_value='FAKE-OAUTH'),patch('connector.runtime.request',return_value=io.BytesIO(stream)):
    runtime.process_one(store,job,'fake-model')
   self.assertNotIn('outbox',store.read())
  with app.connect(app.DB) as d:
   version=d.execute('SELECT body,claims FROM versions WHERE content_id=?',(cid,)).fetchone()
   self.assertEqual(version['body'],'Texto para revisão humana.');self.assertIn('Revisão humana',version['claims'])
   self.assertEqual(d.execute("SELECT count(*) FROM runs WHERE provider='chatgpt-plus-local' AND content_id=?",(cid,)).fetchone()[0],1)
   self.assertEqual(d.execute('SELECT count(*) FROM publications WHERE content_id=?',(cid,)).fetchone()[0],0)
del _HTTP
