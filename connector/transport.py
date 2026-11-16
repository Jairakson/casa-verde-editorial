import json,urllib.request,urllib.error,urllib.parse
from .security import ConnectorError
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
OPENER=urllib.request.build_opener(NoRedirect)
def request(url,payload=None,headers=None,form=False,timeout=25):
 data=None
 headers=dict(headers or {})
 if payload is not None:
  data=(urllib.parse.urlencode(payload) if form else json.dumps(payload,ensure_ascii=False)).encode()
  headers['Content-Type']='application/x-www-form-urlencoded' if form else 'application/json'
 req=urllib.request.Request(url,data=data,headers=headers)
 try:return OPENER.open(req,timeout=timeout)
 except urllib.error.HTTPError as error:
  error.close()
  if error.code==401:raise ConnectorError('Autorização recusada. Conecte novamente a conta ou o painel.',status=401) from None
  if error.code==429:raise ConnectorError('Limite de uso atingido. Verifique os limites do Plus ou aguarde antes de tentar novamente.',status=429) from None
  raise ConnectorError('Solicitação recusada pelo serviço (HTTP '+str(error.code)+'). Nenhuma credencial foi exibida.',status=error.code) from None
 except (OSError,urllib.error.URLError):raise ConnectorError('Falha de conexão. Verifique a internet e tente novamente.') from None
def get_json(url,payload=None,headers=None,form=False,timeout=25):
 with request(url,payload,headers,form,timeout) as response:
  raw=response.read(2_000_001)
  if len(raw)>2_000_000:raise ConnectorError('Resposta excedeu o limite permitido.')
  try:return json.loads(raw)
  except (ValueError,UnicodeError):raise ConnectorError('O serviço retornou uma resposta inválida.') from None
