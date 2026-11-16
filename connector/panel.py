import time,urllib.parse,webbrowser
from .security import ConnectorError
from .transport import get_json
DEFAULT_PANEL='https://casa-verde-editorial.onrender.com'
def validate_base(base):
 parts=urllib.parse.urlsplit(base)
 if parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('','/') or not parts.hostname:raise ConnectorError('Endereço do painel inválido.')
 if parts.scheme!='https' and not (parts.scheme=='http' and parts.hostname=='127.0.0.1'):raise ConnectorError('O painel precisa de HTTPS.')
 return base.rstrip('/')
def pair(store,base=DEFAULT_PANEL):
 base=validate_base(base);answer=get_json(base+'/api/connector/pair/start',{})
 code=answer['user_code'];device=answer['device_code']
 print('\nCódigo de pareamento:',code,'\nConfirme esse mesmo código no painel como administrador. Ele expira em dez minutos.')
 webbrowser.open(base+'/conector?codigo='+urllib.parse.quote(code))
 until=time.monotonic()+min(int(answer.get('expires_in',600)),600)
 while time.monotonic()<until:
  time.sleep(max(3,int(answer.get('interval',3))))
  result=get_json(base+'/api/connector/pair/poll',{'device_code':device})
  if result.get('status')=='connected':
   data=store.read();data['panel']={'base':base,'device_token':result['device_token'],'device_id':result['device_id']};store.write(data)
   print('Computador conectado ao painel.');return
 raise ConnectorError('Pareamento expirado. Inicie novamente.')
def call(store,endpoint,payload=None):
 panel=store.read().get('panel')
 if not panel:raise ConnectorError('Conecte este computador ao painel primeiro.')
 base=validate_base(panel['base'])
 if endpoint not in ('next','status','complete','fail'):raise ConnectorError('Operação não permitida ao conector.')
 return get_json(base+'/api/connector/'+endpoint,payload or {},{'Authorization':'Bearer '+panel['device_token']},timeout=20)
