"""Assistentes locais determinísticos. Não representam chamadas a modelos de IA.
Fontes são dados não confiáveis; nunca executadas ou usadas como instruções.
"""
import json,hashlib
from domain import *
INSTRUCTIONS={
 'pesquisa':{'version':'1','instruction':'Organizar fontes fornecidas. Nunca inferir demanda ou tendências sem dados.'},
 'estrategia':{'version':'1','instruction':'Gerar estrutura de brief a partir da pauta aprovada; marcar lacunas e verificar duplicação.'},
 'redacao':{'version':'1','instruction':'Preparar estrutura de artigo; nunca preencher fatos sem evidência.'},
 'imagens':{'version':'1','instruction':'Entregar brief e prompt como pendentes; IA não é fotografia de projeto real.'},
 'video':{'version':'1','instruction':'Derivar storyboard exclusivamente da versão aprovada. Sem renderização, manter pendente.'},
 'revisao':{'version':'1','instruction':'Aplicar bloqueios objetivos e registrar limitações; revisão factual exige conferência humana.'},
 'desempenho':{'version':'1','instruction':'Preservar fonte, período e unidade; ausência não significa zero.'}}
def execute(d,c,agent):
 if agent not in INSTRUCTIONS:raise ValueError('Agente desconhecido.')
 x,v=current(d,c);o=d.execute('SELECT * FROM opportunities WHERE id=?',(x['opportunity_id'],)).fetchone()
 payload={'title':x['title'],'version':v['id'] if v else None,'brief':x['brief'],'sources':o['sources']}
 key=hashlib.sha256(json.dumps([c,agent,INSTRUCTIONS[agent]['version'],payload],sort_keys=True).encode()).hexdigest()
 old=d.execute('SELECT * FROM runs WHERE idempotency=?',(key,)).fetchone()
 if old:return old['id']
 output={};status='concluido';error=''
 if agent=='estrategia':
  duplicates=d.execute('SELECT id,title FROM contents WHERE id!=? AND (title=? OR opportunity_id=?)',(c,x['title'],x['opportunity_id'])).fetchall()
  output={'modo':'estrutura local, sem IA','objetivo':f'Responder à intenção de {o["keyword"] or x["title"]}.','tipo':o['kind'],'publico':'Iniciantes, moradores de apartamentos e imóveis alugados','estrutura':['Resposta inicial','Contexto e condições','Passo a passo','Cuidados e limites','Referências'],'perguntas':['Qual problema será resolvido?','Quais condições mudam a recomendação?','Quanto esforço é necessário?'],'fontes_obrigatorias':o['sources'],'diferencial':'Pendente de definição humana','imagens':'Opcionais, a definir','links_internos':[],'produtos':'Somente dados comprovados; nenhuma URL inventada','cta':'Aplicar a orientação às condições da própria casa','cuidados':'Cultivo depende de espécie, luz, clima e substrato. Não há frequência universal de rega.','possiveis_duplicatas':[dict(z) for z in duplicates],'acao':'Conferir intenção e considerar atualização antes de nova página'}
 elif agent=='revisao':
  issues=[]
  if not v:issues.append({'severidade':'critica','motivo':'Nenhuma versão disponível'})
  else:
   if v['claims'].strip():issues.append({'severidade':'critica','trecho':v['claims'],'motivo':'Afirmações sem validação','correcao':'Validar e salvar nova versão'})
   if not o['sources']:issues.append({'severidade':'critica','motivo':'Fontes ausentes'})
   if re.search(r'reg(?:ue|ar).{0,25}(todo dia|diariamente|sempre)',v['body'],re.I):issues.append({'severidade':'critica','motivo':'Possível recomendação universal de rega','correcao':'Contextualizar espécie, luz e substrato'})
  output={'problemas':issues,'resultado':'bloqueado' if issues else 'conferencia_humana_obrigatoria','limitacoes':['Assistente local não acessa fontes. Correção factual, atualidade e direitos devem ser conferidos por revisor humano.'],'versao':v['id'] if v else None}
 elif agent=='redacao':output={'estado':'estrutura_pendente_de_redacao','titulo':x['title'],'secoes':['Resposta principal baseada nas fontes','Orientações contextualizadas','Limitações','Referências associadas às afirmações'],'brief':x['brief'],'aviso':'Nenhum texto factual foi gerado. Preencha e valide no editor.'}
 elif agent=='imagens':output={'estado':'pendente_provedor','brief':f'Ilustração conceitual para {x["title"]}, identidade verde e tons naturais.','prompt':'Ilustração editorial de casa e jardim, composição simples, sem texto, sem pretensão de identificação botânica.','origem':'IA, se gerada','licenca':'Pendente de provedor','alt':'Definir após geração','finalidade':'Capa opcional'}
 elif agent=='video':
  if not v or not d.execute('SELECT 1 FROM approvals WHERE version_id=?',(v['id'],)).fetchone():raise ValueError('Vídeo exige versão aprovada.')
  sentences=[s.strip() for s in v['body'].split('\n') if s.strip()]
  output={'estado':'storyboard_pendente_renderizacao','versao_origem':v['id'],'formatos':['9:16','16:9'],'cenas':[{'texto':s,'legenda':s,'duracao_estimada_segundos':max(3,round(len(s.split())/2.5)),'ativo':'pendente_aprovacao'} for s in sentences],'voz':'não configurada','musica':'não configurada','direitos':'Verificar antes da renderização'}
 elif agent=='pesquisa':output={'modo':'importacao_manual','fontes':o['sources'],'volume':None,'tendencia':None,'confianca':'A avaliar pelo editor','limitacao':'Sem provedor de pesquisa conectado; nenhuma evidência nova descoberta.'}
 elif agent=='desempenho':
  metrics=[dict(z) for z in d.execute('SELECT source,start,end,name,value,kind FROM metrics WHERE content_id=?',(c,))]
  output={'metricas':metrics,'recomendacao':'Comparar períodos equivalentes antes de recomendar mudanças.' if metrics else 'Importar métricas reais antes de avaliar desempenho.','limitacao':'Não atribui receita nem soma métricas de fontes incompatíveis.'}
 row=d.execute('INSERT INTO runs(content_id,version_id,agent,instruction_version,provider,model,status,input,output,error,cost,cost_kind,units,idempotency,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(c,v['id'] if v else None,agent,'1','local-deterministico','sem-modelo',status,json.dumps(payload,ensure_ascii=False),json.dumps(output,ensure_ascii=False),error,0,'confirmado',0,key,now()))
 return row.lastrowid
