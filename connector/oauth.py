import base64,hashlib,hmac,json,secrets,time,uuid,webbrowser,urllib.parse
from http.server import BaseHTTPRequestHandler,HTTPServer
from .security import ConnectorError
from .transport import get_json
AUTHORIZE='https://auth.openai.com/api/accounts/authorize'
TOKEN='https://auth.openai.com/api/accounts/oauth/token'
DISCOVERY='https://auth.openai.com/.well-known/openid-configuration'
RESOURCE='https://api.openai.com/v1'
SCOPES='openid profile email offline_access resource.invoke chatgpt.tokens.use.direct'
def validate_identity(id_token,client_id,nonce):
 import jwt
 metadata=get_json(DISCOVERY)
 uri=metadata.get('jwks_uri','')
 if metadata.get('issuer')!='https://auth.openai.com' or urllib.parse.urlsplit(uri).scheme!='https' or urllib.parse.urlsplit(uri).hostname!='auth.openai.com':raise ConnectorError('Metadados de identidade não reconhecidos.')
 try:
  key=jwt.PyJWKClient(uri,timeout=15).get_signing_key_from_jwt(id_token)
  claims=jwt.decode(id_token,key.key,algorithms=['RS256','ES256'],audience=client_id,issuer='https://auth.openai.com',leeway=30,options={'require':['exp','iat','iss','aud','sub','nonce']})
  if not hmac.compare_digest(str(claims['nonce']),nonce):raise ValueError()
  return claims
 except Exception:raise ConnectorError('Não foi possível validar a identidade retornada pelo ChatGPT.') from None
def authorization_parameters(host,redirect,state,nonce,verifier,saved=None):
 params={'client_id':saved['client_id'] if saved else 'dynamic_agent_client','ext_agent_host_id':host,'response_type':'code','redirect_uri':redirect,'scope':SCOPES,'resource':RESOURCE,'state':state,'nonce':nonce,'code_challenge_method':'S256','code_challenge':base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')}
 if saved:
  if saved.get('id_token'):params['id_token_hint']=saved['id_token']
  if saved.get('email'):params['login_hint']=saved['email']
 else:params['agent_name_hint']='Casa & Verde Connector'
 return params
def login(store,selected=None):
 data=store.read();saved=data.get('accounts',{}).get(selected) if selected else None
 if 'host_id' not in data:data['host_id']='urn:uuid:'+str(uuid.uuid4());store.write(data)
 state=secrets.token_urlsafe(32);nonce=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(64);callback={}
 class Callback(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   parsed=urllib.parse.urlsplit(self.path)
   if parsed.path!='/auth/callback':self.send_response(404);self.end_headers();return
   query=urllib.parse.parse_qs(parsed.query)
   if len(query.get('state',[]))!=1 or not hmac.compare_digest(query['state'][0],state):self.send_response(400);self.end_headers();return
   for key in ['code','client_id','error']:
    if len(query.get(key,[]))>1:self.send_response(400);self.end_headers();return
   callback.update({k:v[0] for k,v in query.items()})
   self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'none'; frame-ancestors 'none'");self.end_headers()
   self.wfile.write('Autorização recebida. Volte à janela do conector para confirmar o resultado.'.encode())
 server=HTTPServer(('127.0.0.1',0),Callback);server.timeout=1
 redirect=f'http://127.0.0.1:{server.server_port}/auth/callback'
 params=authorization_parameters(data['host_id'],redirect,state,nonce,verifier,saved)
 print('Abrindo a página oficial do ChatGPT. Entre na sua conta Plus e confira as permissões.\nNão feche esta janela. O login será aguardado por dez minutos.')
 try:
  if not webbrowser.open(AUTHORIZE+'?'+urllib.parse.urlencode(params)):raise ConnectorError('Não foi possível abrir o navegador padrão. Configure-o e tente novamente.')
  until=time.monotonic()+600
  while not callback and time.monotonic()<until:server.handle_request()
 finally:server.server_close()
 if not callback:raise ConnectorError('Tempo de login esgotado. Inicie novamente.')
 if callback.get('error'):raise ConnectorError('Autorização não concluída. Nenhuma tarefa será executada.')
 issued=callback.get('client_id') or (saved['client_id'] if saved else None)
 if not issued or issued=='dynamic_agent_client' or (saved and issued!=saved['client_id']) or not callback.get('code'):raise ConnectorError('Registro de conta incompleto ou incompatível.')
 tokens=get_json(TOKEN,{'grant_type':'authorization_code','client_id':issued,'code':callback['code'],'code_verifier':verifier,'redirect_uri':redirect,'resource':RESOURCE},form=True)
 claims=validate_identity(tokens.get('id_token',''),issued,nonce)
 if saved and claims['sub']!=saved['subject']:raise ConnectorError('A conta retornada é diferente da conta selecionada.')
 account={'client_id':issued,'subject':claims['sub'],'email':claims.get('email','Conta ChatGPT'),'issuer':'https://auth.openai.com',**tokens,'scopes':tokens.get('scope','').split(),'saved_at':time.time()}
 data=store.read();data.setdefault('accounts',{})[issued]=account
 if 'chatgpt.tokens.use.direct' in account['scopes']:data['active']=issued
 store.write(data)
 if 'chatgpt.tokens.use.direct' not in account['scopes']:raise ConnectorError('Login realizado, mas o uso do plano não foi autorizado. Conecte novamente essa conta e confira a autorização.')
 print('Conta autorizada:',account['email'])
 return issued
def access_token(store):
 data=store.read();key=data.get('active');account=data.get('accounts',{}).get(key)
 if not account or 'chatgpt.tokens.use.direct' not in account.get('scopes',[]):raise ConnectorError('Conecte uma conta ChatGPT e autorize o uso do plano antes de executar tarefas.')
 if time.time()>=account.get('saved_at',0)+account.get('expires_in',0)-90:
  if not account.get('refresh_token'):raise ConnectorError('A conexão expirou. Entre novamente no ChatGPT.')
  if time.time()<account.get('earliest_refresh_at',0):raise ConnectorError('Aguarde o prazo de renovação da conexão e tente novamente.')
  tokens=get_json(TOKEN,{'grant_type':'refresh_token','client_id':account['client_id'],'refresh_token':account['refresh_token'],'resource':RESOURCE},form=True)
  scopes=tokens.get('scope',' '.join(account['scopes'])).split()
  if 'chatgpt.tokens.use.direct' not in scopes or not tokens.get('access_token') or not tokens.get('refresh_token'):raise ConnectorError('Permissão de uso do plano não está disponível. Conecte novamente.')
  account.update(tokens);account.update(scopes=scopes,saved_at=time.time());data['accounts'][key]=account;store.write(data)
 return account['access_token']
def logout(store):
 data=store.read();key=data.get('active');account=data.get('accounts',{}).get(key)
 if not account:return
 confirmed=True
 try:
  if account.get('refresh_token'):
   metadata=get_json(DISCOVERY);endpoint=metadata.get('revocation_endpoint','')
   if urllib.parse.urlsplit(endpoint).scheme!='https' or urllib.parse.urlsplit(endpoint).hostname!='auth.openai.com':raise ConnectorError('Endpoint de revogação inválido.')
   from .transport import request
   with request(endpoint,{'token':account['refresh_token'],'token_type_hint':'refresh_token','client_id':key},form=True):pass
 except ConnectorError:confirmed=False
 for field in ['access_token','refresh_token','id_token','scope','scopes','expires_in','earliest_refresh_at']:account.pop(field,None)
 data['active']=None;data['accounts'][key]=account;store.write(data)
 print('Conta desconectada.' if confirmed else 'Dados locais removidos. A revogação remota não foi confirmada; desconecte o aplicativo nas configurações do ChatGPT.')
