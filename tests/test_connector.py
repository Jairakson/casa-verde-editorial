import io,json,os,tempfile,time,unittest
from unittest.mock import patch
import app,connector_backend as bridge
from domain import connect,migrate,save_version,current,review,approve
from connector import oauth,runtime
from connector.security import Store,ConnectorError
class Backend(unittest.TestCase):
 def setUp(self):
  self.d=connect(':memory:');migrate(self.d)
  self.seed()
 def seed(self):
  self.d.execute("INSERT INTO users VALUES(1,'admin',?,'admin')",(app.password('a-strong-password'),))
  self.d.execute("INSERT INTO opportunities(id,title,kind,keyword,sources) VALUES(1,'Horta','Tutorial','horta','https://example.org/source')")
  self.d.execute("INSERT INTO contents(id,opportunity_id,title,slug,brief) VALUES(1,1,'Horta','horta','Brief aprovado')")
  self.pair=bridge.start_pairing(self.d);bridge.approve_pairing(self.d,self.pair['user_code'],1)
  self.creds=bridge.poll_pairing(self.d,self.pair['device_code']);self.device=bridge.authenticate(self.d,self.creds['device_token'])
 def tearDown(self):self.d.close()
 def result(self):return {'entrega':{'titulo':'Texto gerado','corpo':'Um rascunho com referências.'},'afirmacoes_pendentes':[],'fontes_usadas':['https://example.org/source'],'limitacoes':['Fontes não acessadas.']}
 def test_pair_token_is_hashed_and_one_use(self):
  self.assertNotEqual(self.device['token_hash'],self.creds['device_token'])
  with self.assertRaises(ValueError):bridge.poll_pairing(self.d,self.pair['device_code'])
  self.assertIsNone(bridge.authenticate(self.d,'wrong'))
 def test_pair_requires_approval(self):
  pending=bridge.start_pairing(self.d)
  self.assertEqual(bridge.poll_pairing(self.d,pending['device_code'])['status'],'pending')
 def test_pair_expiry(self):
  pending=bridge.start_pairing(self.d);self.d.execute('UPDATE connector_pairings SET expires=0 WHERE user_code=?',(pending['user_code'],))
  with self.assertRaises(ValueError):bridge.approve_pairing(self.d,pending['user_code'],1)
 def test_queue_and_completion_idempotent(self):
  first=bridge.enqueue(self.d,1,'redacao',1);self.assertEqual(first,bridge.enqueue(self.d,1,'redacao',1))
  job=bridge.claim(self.d,self.device)['job'];self.assertEqual(job['id'],first)
  self.assertIsNone(bridge.claim(self.d,self.device)['job'])
  out=bridge.complete(self.d,self.device,first,job['lease'],self.result(),'model-test',{'total_tokens':10})
  self.assertEqual(out['status'],'completed')
  self.assertEqual(bridge.complete(self.d,self.device,first,job['lease'],self.result(),'model-test')['status'],'already_completed')
  self.assertEqual(current(self.d,1)[0]['current_version'],1)
  self.assertEqual(self.d.execute('SELECT count(*) FROM runs').fetchone()[0],1)
  self.assertIsNone(self.d.execute('SELECT cost FROM runs').fetchone()[0])
  self.assertIn('Revisão humana',current(self.d,1)[1]['claims'])
  with self.assertRaises(ValueError):approve(self.d,1,1)
 def test_stale_version_not_applied(self):
  jid=bridge.enqueue(self.d,1,'redacao',1);job=bridge.claim(self.d,self.device)['job']
  save_version(self.d,1,1,'Alterado','Texto humano')
  self.assertEqual(bridge.complete(self.d,self.device,jid,job['lease'],self.result(),'model')['status'],'stale')
  self.assertEqual(current(self.d,1)[1]['body'],'Texto humano')
 def test_stale_brief_not_applied(self):
  jid=bridge.enqueue(self.d,1,'estrategia',1);job=bridge.claim(self.d,self.device)['job']
  self.d.execute("UPDATE contents SET brief='Outro brief' WHERE id=1")
  self.assertEqual(bridge.complete(self.d,self.device,jid,job['lease'],self.result(),'model')['status'],'stale')
 def test_cancel_and_lease_expiry(self):
  jid=bridge.enqueue(self.d,1,'estrategia',1);job=bridge.claim(self.d,self.device)['job']
  self.d.execute('UPDATE connector_jobs SET lease_expires=0 WHERE id=?',(jid,))
  self.assertTrue(bridge.status(self.d,self.device,jid,job['lease'])['cancelled'])
  new=bridge.claim(self.d,self.device)['job'];self.assertNotEqual(job['lease'],new['lease'])
  with self.assertRaises(ValueError):bridge.complete(self.d,self.device,jid,job['lease'],self.result(),'model')
  self.d.execute("UPDATE connector_jobs SET state='cancelled' WHERE id=?",(jid,))
  with self.assertRaises(ValueError):bridge.complete(self.d,self.device,jid,new['lease'],self.result(),'model')
 def test_device_revocation(self):
  self.d.execute('UPDATE connector_devices SET revoked=1')
  self.assertIsNone(bridge.authenticate(self.d,self.creds['device_token']))
 def test_review_cannot_approve(self):
  save_version(self.d,1,1,'Texto','Corpo')
  jid=bridge.enqueue(self.d,1,'revisao',1);job=bridge.claim(self.d,self.device)['job']
  bridge.complete(self.d,self.device,jid,job['lease'],self.result(),'model')
  self.assertEqual(self.d.execute('SELECT count(*) FROM approvals').fetchone()[0],0)
  self.assertEqual(self.d.execute('SELECT count(*) FROM reviews').fetchone()[0],0)
 def test_video_needs_approved_version(self):
  save_version(self.d,1,1,'Texto','Corpo')
  with self.assertRaises(ValueError):bridge.enqueue(self.d,1,'video',1)
 def test_invalid_output_or_unknown_source(self):
  jid=bridge.enqueue(self.d,1,'estrategia',1);job=bridge.claim(self.d,self.device)['job']
  result=self.result();result['fontes_usadas']=['https://inventada.example/']
  with self.assertRaises(ValueError):bridge.complete(self.d,self.device,jid,job['lease'],result,'model')
  with self.assertRaises(ValueError):bridge.validate_result({'entrega':{}})
class LocalAuth(unittest.TestCase):
 def test_secure_store_and_host_id(self):
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder);store.write({'accounts':{},'active':None,'secret':'FAKE-TEST-TOKEN'})
   self.assertEqual(store.read()['secret'],'FAKE-TEST-TOKEN')
   if os.name!='nt':self.assertEqual(store.path.stat().st_mode&0o777,0o600)
 def test_official_oauth_parameters(self):
  params=oauth.authorization_parameters('urn:uuid:test','http://127.0.0.1:1234/auth/callback','state','nonce','verifier')
  self.assertEqual(params['client_id'],'dynamic_agent_client');self.assertEqual(params['code_challenge_method'],'S256')
  self.assertIn('chatgpt.tokens.use.direct',params['scope']);self.assertNotIn('client_secret',params)
  saved=oauth.authorization_parameters('urn:uuid:test','http://127.0.0.1:1234/auth/callback','state','nonce','verifier',{'client_id':'issued','id_token':'FAKE','email':'example'})
  self.assertEqual(saved['client_id'],'issued');self.assertNotIn('agent_name_hint',saved)
 def test_identity_validates_signature_nonce_and_audience(self):
  import jwt
  from cryptography.hazmat.primitives.asymmetric import rsa
  key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
  claims={'iss':'https://auth.openai.com','sub':'subject','aud':'issued','iat':time.time(),'exp':time.time()+60,'nonce':'nonce'}
  token=jwt.encode(claims,key,algorithm='RS256')
  with patch('connector.oauth.get_json',return_value={'issuer':'https://auth.openai.com','jwks_uri':'https://auth.openai.com/jwks'}),patch('jwt.PyJWKClient') as jwks:
   jwks.return_value.get_signing_key_from_jwt.return_value.key=key.public_key()
   self.assertEqual(oauth.validate_identity(token,'issued','nonce')['sub'],'subject')
   with self.assertRaises(ConnectorError):oauth.validate_identity(token,'issued','wrong-nonce')
   with self.assertRaises(ConnectorError):oauth.validate_identity(token,'wrong-audience','nonce')
 def test_refresh_rotates_tokens(self):
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder);store.write({'active':'issued','accounts':{'issued':{'client_id':'issued','access_token':'OLD-FAKE','refresh_token':'OLD-REFRESH','scopes':['chatgpt.tokens.use.direct'],'saved_at':0,'expires_in':3600}}})
   with patch('connector.oauth.get_json',return_value={'access_token':'NEW-FAKE','refresh_token':'NEW-REFRESH','expires_in':3600,'scope':'chatgpt.tokens.use.direct'}) as call:
    self.assertEqual(oauth.access_token(store),'NEW-FAKE');self.assertEqual(store.read()['accounts']['issued']['refresh_token'],'NEW-REFRESH')
    self.assertEqual(call.call_args.args[1]['client_id'],'issued');self.assertNotIn('scope',call.call_args.args[1])
 def test_no_api_key_fallback(self):
  with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'OPENAI_API_KEY':'FAKE-DO-NOT-USE'}):
   with self.assertRaises(ConnectorError):oauth.access_token(Store(folder))
class OAuthLoopback(unittest.TestCase):
 def test_loopback_ignores_wrong_state_and_exchanges_valid_code(self):
  import threading,urllib.request,urllib.error,urllib.parse,contextlib
  threads=[];rejected=[]
  def browser(url):
   self.assertTrue(url.startswith(oauth.AUTHORIZE+'?'))
   params=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
   def callback():
    base=params['redirect_uri'][0]
    for state in ['incorrect',params['state'][0]]:
     target=base+'?'+urllib.parse.urlencode({'state':state,'code':'FAKE-CODE','client_id':'issued'})
     try:
      with urllib.request.urlopen(target,timeout=5) as response:response.read()
     except urllib.error.HTTPError as error:rejected.append(error.code)
   thread=threading.Thread(target=callback);thread.start();threads.append(thread);return True
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder)
   with patch('connector.oauth.webbrowser.open',side_effect=browser),patch('connector.oauth.validate_identity',return_value={'sub':'subject','email':'user@example.com'}),patch('connector.oauth.get_json',return_value={'id_token':'FAKE-ID','access_token':'FAKE-ACCESS','refresh_token':'FAKE-REFRESH','expires_in':3600,'scope':'openid chatgpt.tokens.use.direct'}) as exchange,contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(oauth.login(store),'issued')
   for thread in threads:thread.join(timeout=5)
   self.assertEqual(rejected,[400]);self.assertEqual(exchange.call_count,1)
   self.assertEqual(exchange.call_args.args[0],oauth.TOKEN)
   self.assertEqual(exchange.call_args.args[1]['client_id'],'issued')
   self.assertEqual(store.read()['active'],'issued');self.assertTrue(store.read()['host_id'].startswith('urn:uuid:'))

class Streaming(unittest.TestCase):
 def job(self):return {'id':1,'lease':'test-lease','instructions':'Editorial','payload':{'title':'Horta'},'timeout_seconds':180}
 def output(self):return {'entrega':{'brief':'Teste'},'afirmacoes_pendentes':[],'fontes_usadas':[],'limitacoes':['Teste']}
 def event(self,kind,**data):return b'data: '+json.dumps({'type':kind,**data}).encode()+b'\n\n'
 def test_request_has_no_unsupported_fields(self):
  body=runtime.inference_body(self.job(),'model')
  self.assertFalse(body['store']);self.assertTrue(body['stream']);self.assertNotIn('max_output_tokens',body);self.assertNotIn('tools',body)
 def test_completed_stream(self):
  stream=io.BytesIO(self.event('response.output_text.delta',delta=json.dumps(self.output()))+self.event('response.completed',response={'status':'completed','usage':{'total_tokens':12}}))
  result,usage=runtime.consume_stream(None,self.job(),stream);self.assertEqual(result,self.output());self.assertEqual(usage['total_tokens'],12)
 def test_partial_stream_rejected(self):
  with self.assertRaises(ConnectorError):runtime.consume_stream(None,self.job(),io.BytesIO(self.event('response.output_text.delta',delta='partial')))
 def test_failed_stream_rejected(self):
  with self.assertRaises(ConnectorError):runtime.consume_stream(None,self.job(),io.BytesIO(self.event('response.failed',response={'error':{'code':'subscription_sharing_usage_limit_exceeded'}})))
 def test_outbox_retry_does_not_regenerate(self):
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder);store.write({'accounts':{},'outbox':{'stage':'ready','job':self.job(),'model':'m','result':self.output()}})
   with patch('connector.runtime.panel.call',side_effect=[{'state':'leased','cancelled':False},{'status':'already_completed'}]) as remote,patch('connector.runtime.generate') as generate:
    runtime.send_outbox(store);generate.assert_not_called();self.assertNotIn('outbox',store.read());self.assertEqual(remote.call_count,2)
