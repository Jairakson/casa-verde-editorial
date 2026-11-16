"""Execute com python -m connector.desktop. Nunca registra tokens em stdout."""
import sys,webbrowser,json
from .security import Store,ConnectorError
from . import oauth,panel,runtime

def account_login(store):
 data=store.read();items=list(data.get('accounts',{}).items())
 print('\n0 · Usar outra conta / registrar o conector')
 for i,(key,account) in enumerate(items,1):print(i,'·',account.get('email','Conta ChatGPT'),'· registro',key[-8:])
 raw=input('Conta [0]: ').strip() or '0'
 if not raw.isdigit() or not 0<=int(raw)<=len(items):raise ConnectorError('Escolha um número da lista.')
 selected=items[int(raw)-1][0] if int(raw) else None
 oauth.login(store,selected)
 data=store.read();data.pop('model',None);store.write(data)
def choose_model(store):
 choices=runtime.models(store)
 for i,item in enumerate(choices,1):print(i,'·',item.get('display_name',item['slug']))
 raw=input('Número do modelo: ').strip()
 if not raw.isdigit() or not 1<=int(raw)<=len(choices):raise ConnectorError('Escolha um número da lista.')
 data=store.read();data['model']=choices[int(raw)-1]['slug'];store.write(data)
 print('Modelo selecionado.')
def main():
 if sys.version_info<(3,11):raise SystemExit('Instale Python 3.11 ou superior.')
 try:sys.stdout.reconfigure(encoding='utf-8')
 except (AttributeError,OSError):pass
 from filelock import FileLock,Timeout
 store=Store()
 try:
  with FileLock(str(store.directory/'connector.lock'),timeout=0):
   print('CASA & VERDE · Conector pessoal ChatGPT Plus\nTokens ficam neste computador. Resultados são enviados ao seu painel.\n')
   while True:
    data=store.read();account=data.get('accounts',{}).get(data.get('active'),{})
    print('\nPainel:', 'conectado' if data.get('panel') else 'não conectado','| ChatGPT:',account.get('email','não conectado'))
    print('1 · Conectar computador ao painel\n2 · Entrar ou trocar conta ChatGPT\n3 · Escolher modelo\n4 · Iniciar processamento\n5 · Desconectar ChatGPT\n6 · Abrir limites de uso do ChatGPT\n7 · Ver último resultado não enviado\n0 · Sair')
    choice=input('Escolha: ').strip()
    try:
     if choice=='0':break
     elif choice=='1':panel.pair(store)
     elif choice=='2':account_login(store)
     elif choice=='3':choose_model(store)
     elif choice=='4':runtime.run(store)
     elif choice=='5':oauth.logout(store)
     elif choice=='6':webbrowser.open('https://chatgpt.com/settings/usage')
     elif choice=='7':print(json.dumps(store.read().get('last_unsent_result',{'aviso':'Nenhum resultado pendente.'}),ensure_ascii=False,indent=2))
     else:print('Escolha uma opção da lista.')
    except KeyboardInterrupt:print('\nProcessamento interrompido. Resultados já gerados serão retomados no próximo início; confira a fila no painel.')
    except ConnectorError as error:print('\nNão foi possível concluir:',error)
    except Exception:print('\nFalha inesperada. Nenhuma credencial foi exibida. Feche o conector, atualize o projeto e tente novamente.')
 except Timeout:print('O conector já está aberto neste computador. Use a janela existente.')
if __name__=='__main__':main()
