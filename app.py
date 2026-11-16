"""Central editorial: stdlib Python 3.11+, sem dependências."""
import os,json,secrets,time,hashlib,hmac,csv,io,html,urllib.parse,sqlite3,re
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from zoneinfo import ZoneInfo
from domain import *
from agents import execute,INSTRUCTIONS
DB=os.environ.get('DATABASE_PATH',str(ROOT/'editorial.db'))
def esc(x):
 if isinstance(x,str) and re.match(r'^\d{4}-\d\d-\d\dT.*\+00:00$',x):
  try:x=datetime.datetime.fromisoformat(x).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M %Z')
  except ValueError:pass
 return html.escape(str(x if x is not None else ''))
def password(p,salt=None):
 salt=salt or secrets.token_hex(16)
 return salt+':'+hashlib.scrypt(p.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()
def field(name,label,kind='text',value=''):
 return f'<label>{label}<'+('textarea' if kind=='textarea' else 'input')+f' name="{name}" '+('>'+esc(value)+'</textarea>' if kind=='textarea' else f'type="{kind}" value="{esc(value)}">')+'</label>'
def select(name,label,options):return '<label>'+label+f'<select name="{name}">'+''.join(f'<option value="{esc(k)}">{esc(v)}</option>' for k,v in options)+'</select></label>'
def card(title,body):return '<section class="card"><h2>'+esc(title)+'</h2>'+body+'</section>'
CSS='''*{box-sizing:border-box}body{margin:0;background:#f5f5ef;color:#243d32;font:15px system-ui}a{color:inherit}aside{position:fixed;inset:0 auto 0 0;width:230px;background:#173e32;color:#edf4e6;padding:30px 23px}aside h1{font:30px Georgia;margin:0 0 8px}aside small{color:#acc4b5}nav{margin-top:40px}nav a{display:block;padding:13px;border-radius:8px;text-decoration:none;margin:4px 0}nav a:hover,nav a.active{background:#315747}main{margin-left:230px;padding:38px 48px;max-width:1600px}h1{font:38px Georgia;margin:8px 0 14px}h2{font:24px Georgia;margin:0 0 20px}h3{font:21px Georgia}p{line-height:1.65}.eyebrow{text-transform:uppercase;letter-spacing:2px;font-size:11px;color:#687e66}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:35px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px}.card{padding:26px;background:white;border:1px solid #e1e6da;border-radius:12px;margin-bottom:22px}.stat{font:38px Georgia;color:#24533c}.muted,small{color:#6c7b70}.tag{display:inline-block;font-size:11px;background:#e9efdb;border-radius:20px;padding:6px 10px;margin:3px}.warn{background:#fff1cf;color:#775b20;padding:14px;border-radius:8px}button,.button{background:#27563e;color:white;padding:11px 17px;border:0;border-radius:7px;cursor:pointer;text-decoration:none;display:inline-block;font:inherit}button:hover{background:#173e32}label{display:block;font-size:13px;margin:14px 0}input,textarea,select{display:block;width:100%;border:1px solid #ccd6c9;background:#fafcf7;padding:11px;border-radius:6px;font:inherit;margin-top:7px;color:#243d32}textarea{min-height:130px;resize:vertical}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:14px 10px;border-bottom:1px solid #edf0e7;vertical-align:top}th{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#6c7b70}.actions{display:flex;gap:10px;flex-wrap:wrap}details{margin:15px 0}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;word-break:break-word;font:14px system-ui;line-height:1.7}article{max-width:850px;margin:auto}footer{margin:30px 0;color:#6c7b70;font-size:12px}.hero{background:#e8eddd;padding:32px;border-radius:12px;margin-bottom:25px}.error{padding:15px;background:#ffe5dd;border-radius:8px}@media(max-width:800px){aside{position:relative;width:auto;padding:20px}nav{display:flex;overflow:auto;margin-top:16px}nav a{white-space:nowrap;padding:8px}main{margin:0;padding:23px}table{display:block;overflow:auto}.top{display:block}}'''
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,body,status=200,ctype='text/html; charset=utf-8',cookie=None):
  self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','same-origin');self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers();self.wfile.write(body.encode())
 def redirect(self,url,cookie=None):
  self.send_response(303);self.send_header('Location',url)
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers()
 def session(self,d):
  c=SimpleCookie()
  try:c.load(self.headers.get('Cookie',''))
  except:return None
  return d.execute('SELECT s.*,u.role,u.email FROM sessions s JOIN users u ON u.id=s.user_id WHERE token=? AND expires>?',(c['session'].value if 'session'in c else '',time.time())).fetchone()
 def form(self,action,body,label='Salvar'):
  return f'<form method="post" action="/action"><input type="hidden" name="action" value="{action}"><input type="hidden" name="csrf" value="{self.s["csrf"]}">'+body+f'<button>{label}</button></form>'
 def hidden(self,c):return f'<input type="hidden" name="id" value="{c}">'
 def page(self,title,body,tab=''):
  nav=[('/','Visão geral'),('/oportunidades','Oportunidades'),('/editorial','Central editorial'),('/midia','Biblioteca de mídia'),('/calendario','Calendário'),('/analytics','Analytics'),('/agentes','Agentes e execuções'),('/configuracoes','Configurações'),('/portal','Ver portal')]
  return '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+esc(title)+' · Casa & Verde</title><style>'+CSS+'</style><aside><h1>casa & verde<span style="color:#b5cb85">.</span></h1><small>CENTRAL EDITORIAL</small><nav>'+''.join(f'<a class="{"active" if tab==u else ""}" href="{u}">{l}</a>' for u,l in nav)+'</nav></aside><main><div class="top"><span class="eyebrow">Seu próximo conteúdo começa aqui</span><span class="muted">'+esc(self.s['email'] if getattr(self,'s',None) else 'Portal de casa e jardim')+'</span></div><h1>'+esc(title)+'</h1>'+body+'<footer>Casa bonita e verde · Horários: America/Sao_Paulo · Integrações externas não configuradas</footer></main></html>'
 def do_GET(self):
  with connect(DB) as d:
   self.s=self.session(d);path=urllib.parse.urlsplit(self.path).path
   if path.startswith('/portal') or path=='/sitemap.xml':return self.public(d,path)
   if not self.s:return self.send(self.page('Entre na sua central',card('Bem-vindo de volta','<p>Planeje, escreva e publique com cuidado editorial.</p><form action="/login" method="post">'+field('email','E-mail','email')+field('password','Senha','password')+'<button>Entrar</button></form>')))
   try:body,title=self.admin(d,path);self.send(self.page(title,body,path))
   except (ValueError,TypeError) as e:self.send(self.page('Não foi possível abrir',card('Verifique o endereço',esc(e))),400)
 def admin(self,d,path):
  if path=='/':
   n=lambda sql:d.execute(sql).fetchone()[0]
   body='<div class="hero"><span class="eyebrow">Uma casa de boas ideias</span><h2>Conteúdo útil. Fontes claras. Publicação consciente.</h2><p>Decoração acessível e plantas para espaços pequenos.</p><a class="button" href="/oportunidades">Explorar oportunidades ↗</a></div><div class="grid">'
   for label,val in [('Oportunidades',n('SELECT count(*) FROM opportunities')),('Em produção',n("SELECT count(*) FROM contents WHERE state!='publicado'")),('Publicações',n('SELECT count(*) FROM publications')),('Custo confirmado · USD',n("SELECT coalesce(sum(cost),0) FROM runs WHERE cost_kind='confirmado'"))]:body+=card(label,f'<div class="stat">{val}</div>')
   body+='</div>'+card('Fluxo de produção',self.content_table(d))+card('Pendências e falhas',self.run_table(d,True))
   return body,'Visão geral'
  if path=='/oportunidades':
   weights=json.loads(d.execute("SELECT value FROM settings WHERE key='weights'").fetchone()[0]);rows=[]
   for o in d.execute('SELECT * FROM opportunities ORDER BY id DESC'):
    r=ranking(json.loads(o['scores']),weights);rows.append((o,r))
   rows.sort(key=lambda z:z[1]['score'] if z[1]['score'] is not None else -1,reverse=True)
   body=card('Prioridades editoriais','<p class="muted">Notas são avaliações editoriais informadas manualmente. Volume de busca não é inferido. A cobertura mede critérios preenchidos, não confiança estatística.</p><table><tr><th>Pauta</th><th>Classificação</th><th>Evidências e contribuição</th><th>Decisão</th></tr>'+''.join('<tr><td><b>'+esc(o['title'])+'</b><br><span class="tag">'+esc(o['kind'])+'</span><br>'+esc(o['category'])+'</td><td>'+esc(r['score'] if r['score'] is not None else 'Indisponível')+f'<br>{r["coverage"]}% de cobertura<br>'+('Provisório' if r['provisional'] else 'Priorização editorial')+'</td><td><details><summary>Ver fundamentos</summary><pre>'+esc(o['sources'])+'</pre>'+''.join('<p>'+esc(k)+': '+esc(v if v is not None else 'indisponível')+'</p>' for k,v in zip(CRITERIA,r['contributions']))+'<p>'+esc(o['priority'])+'</p></details></td><td>'+esc(o['status'])+self.form('op_decision',self.hidden(o['id'])+select('status','Decisão',[('aprovada','Aprovar pauta'),('adiada','Adiar'),('rejeitada','Rejeitar')])+field('reason','Justificativa'))+'</td></tr>' for o,r in rows)+'</table>')
   body+=card('Nova oportunidade',self.form('opportunity',field('title','Título provisório')+select('category','Grupo editorial',[(s,s) for s in ['Plantas para apartamentos','Decoração de salas pequenas','Varandas e jardins pequenos','Cuidados com plantas','Hortas em vasos','Organização de ambientes','Guias de compra','Projetos reais e faça você mesmo']])+select('kind','Tipo',[(s,s) for s in ['Artigo permanente','Tutorial','Comparativo','Notícia']])+field('keyword','Palavra-chave')+field('sources','Fontes — uma URL por linha (a consulta será registrada)','textarea')+field('context','Evidências, intenção, público, local/período, confiança e esforço','textarea')+''.join(field('score'+str(i),k+' · nota editorial 0–100 (vazio = indisponível)','number') for i,k in enumerate(CRITERIA))))
   return body,'Oportunidades'
  if path=='/editorial':return card('Sua linha de produção',self.content_table(d)),'Central editorial'
  if path.startswith('/conteudo/'):
   c=int(path.rsplit('/',1)[1]);x,v=current(d,c);h=self.hidden(c)
   body='<p><span class="tag">'+esc(x['state'])+'</span> Versão atual: '+str(x['current_version'])+'</p>'
   body+=card('Brief editorial',self.form('brief',h+field('brief','Objetivo, público, intenção, estrutura, fontes obrigatórias, diferencial, links, CTA e cuidados','textarea',x['brief'])+field('responsible','Responsável',value=x['responsible'])+field('planned','Data planejada','datetime-local',x['planned'] or '')))
   body+=card('Texto e versões',self.form('version',h+field('title','Título',value=x['title'])+field('body','Texto em linguagem simples · inclua referências junto às afirmações','textarea',v['body'] if v else '')+field('claims','Afirmações pendentes de validação','textarea',v['claims'] if v else ''),'Salvar nova versão'))
   body+=card('Assistentes locais',self.form('agent',h+select('agent','Módulo',[(k,k.title()) for k in INSTRUCTIONS]),'Executar assistente')+'<p>Saídas estruturadas disponíveis em Agentes e execuções. Não substituem pesquisa ou revisão factual.</p>')
   body+=card('Revisão obrigatória',self.form('review',h+select('result','Parecer',[('ajustes','Ajustes necessários'),('bloqueado','Bloqueado por problema crítico'),('aprovado','Aprovado para avaliação humana')])+field('issues','Problemas: severidade, trecho, motivo, evidência, correção e especialista','textarea')+field('limitations','Fontes verificadas e limitações de acesso (obrigatório ao aprovar)','textarea')))
   body+=card('Aprovação e publicação', '<p>A aprovação vale apenas para a versão atual. Alterações exigem nova revisão e nova aprovação. Publicação manual no portal interno.</p><div class="actions">'+self.form('approve',h,'Aprovar versão exata')+self.form('publish',h,'Publicar no portal')+'</div>')
   history=d.execute('SELECT v.*,u.email FROM versions v JOIN users u ON u.id=v.author WHERE content_id=? ORDER BY number DESC',(c,)).fetchall()
   body+=card('Histórico imutável',''.join('<details><summary>Versão '+str(z['number'])+' · '+esc(z['created'])+' · '+esc(z['email'])+'</summary><pre>'+esc(z['body'])+'</pre>'+''.join('<p>'+esc(dict(r))+'</p>' for r in d.execute('SELECT result,issues,limitations,created FROM reviews WHERE version_id=?',(z['id'],)))+'</details>' for z in history))
   return body,x['title']
  if path=='/midia':
   body='<p class="warn">Sem provedor de imagens ou renderização. Cadastre briefs e prompts como pendentes. Nenhum vídeo é simulado como concluído.</p>'
   body+=card('Ativos e procedência',self.table(d,'SELECT a.id,c.title,a.kind,a.origin,a.license,a.reference,a.alt,a.status,a.version_id FROM assets a JOIN contents c ON c.id=a.content_id'))
   body+=card('Registrar ativo ou brief',self.form('asset',field('id','ID do conteúdo','number')+select('kind','Formato',[(s,s) for s in ['Capa','Ilustração','Vídeo 9:16','Vídeo 16:9','Áudio']])+field('origin','Origem / provedor (indicar IA quando gerada)')+field('license','Licença e direitos')+field('reference','Referência, brief visual, prompt ou storyboard','textarea')+field('alt','Texto alternativo / legenda')+select('required','Obrigatório',[('0','Não'),('1','Sim')])));return body,'Biblioteca de mídia'
  if path=='/calendario':return card('Agenda editorial · America/Sao_Paulo',self.table(d,'SELECT id,title,planned,responsible,state FROM contents ORDER BY planned')),'Calendário'
  if path=='/analytics':
   body='<p class="warn">Dados ausentes são indisponíveis. Cada métrica mantém fonte e janela. Impressões, sessões e visualizações não são somadas.</p>'
   body+=card('Métricas importadas',self.table(d,'SELECT content_id,source,start,end,name,value,kind,created FROM metrics ORDER BY id DESC'))
   body+=card('Importar CSV', '<p>Cabeçalho: content_id,source,start,end,name,value,kind<br>Datas ISO (AAAA-MM-DD), kind: confirmado ou estimado. Uma linha por métrica e período. Reimportações idênticas são ignoradas.</p>'+self.form('metrics',field('csv','Cole o CSV','textarea')));return body,'Analytics'
  if path=='/agentes':
   body='<p class="warn">Modo manual estruturado. Não há chamadas de IA, pesquisa conectada ou execução externa habilitada. Custos reais só são registrados quando comprovados.</p>'
   body+=card('Módulos especializados',''.join('<span class="tag">'+a+' · instruções v1 · provedor pendente</span>' for a in ['Pesquisa','Estratégia','Redação','Imagens','Vídeo','Revisão','Desempenho']))
   body+=card('Execuções e falhas',self.run_table(d))
   body+=card('Entregas estruturadas',''.join('<details><summary>#'+str(r['id'])+' · '+esc(r['agent'])+' · conteúdo '+str(r['content_id'])+' · versão '+esc(r['version_id'])+'</summary><pre>'+esc(r['output'])+'</pre></details>' for r in d.execute('SELECT * FROM runs WHERE output IS NOT NULL ORDER BY id DESC LIMIT 50')))
   return body,'Agentes e execuções'
  if path=='/configuracoes':
   body=card('Política de operação','<p>Publicação automática desabilitada. Destino: portal interno. Fuso: America/Sao_Paulo. Provedores externos: não configurados. Nenhuma credencial é armazenada no navegador.</p>')
   if self.s['role']=='admin':
    body+=card('Pesos e limites',self.form('settings',field('weights','Pesos na ordem demanda, busca, monetização, originalidade, aderência',value=d.execute("SELECT value FROM settings WHERE key='weights'").fetchone()[0])+field('budget','Limite por período em USD','number',d.execute("SELECT value FROM settings WHERE key='budget'").fetchone()[0])))
    body+=card('Novo usuário',self.form('user',field('email','E-mail','email')+field('password','Senha (mínimo 12 caracteres)','password')+select('role','Permissão',[(s,s) for s in ['editor','reviewer','admin']])))
   body+=card('Auditoria',self.table(d,'SELECT user_id,action,entity,data,created FROM audit ORDER BY id DESC LIMIT 100'))
   return body,'Configurações'
  raise ValueError('Página não encontrada.')
 def content_table(self,d):return '<table><tr><th>Conteúdo</th><th>Etapa</th><th>Versão</th><th>Responsável</th></tr>'+''.join(f'<tr><td><a href="/conteudo/{r["id"]}">{esc(r["title"])}</a><br><small>#{r["id"]}</small></td><td><span class="tag">{esc(r["state"])}</span></td><td>{r["current_version"]}</td><td>{esc(r["responsible"])}</td></tr>' for r in d.execute('SELECT * FROM contents ORDER BY id DESC'))+'</table>'
 def table(self,d,sql):
  q=d.execute(sql);return '<table><tr>'+''.join('<th>'+esc(z[0])+'</th>' for z in q.description)+'</tr>'+''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in q)+'</table>'
 def run_table(self,d,failed=False):return self.table(d,'SELECT agent,status,instruction_version,provider,cost,cost_kind,error,created FROM runs '+("WHERE status='falha' " if failed else '')+'ORDER BY id DESC LIMIT 50')
 def public(self,d,path):
  if path=='/sitemap.xml':
   host='http://'+self.headers.get('Host','localhost:8000')
   return self.send('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+esc(host+'/portal/'+r[0])+'</loc></url>' for r in d.execute('SELECT c.slug FROM publications p JOIN contents c ON c.id=p.content_id'))+'</urlset>',ctype='application/xml')
  body='<p><a href="/portal">Início</a> · <a href="/portal/sobre">Sobre e política editorial</a></p>'
  if path=='/portal/sobre':body+=card('Nossa política','<p>Decoração acessível e plantas para espaços pequenos. Conteúdos passam por revisão e aprovação humana. Referências e autoria constam nos artigos. Relações comerciais devem ser declaradas no texto. Imagens de IA são ilustrações, nunca evidência de testes ou projetos reais.</p>')
  elif path=='/portal':
   query=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query);term=query.get('q',[''])[0];cat=query.get('categoria',[''])[0]
   body+='<form><input name="q" placeholder="Buscar no portal" value="'+esc(term)+'"><button>Buscar</button></form><p>'+''.join('<a class="tag" href="/portal?categoria='+urllib.parse.quote(r[0])+'">'+esc(r[0])+'</a>' for r in d.execute('SELECT DISTINCT o.category FROM publications p JOIN contents c ON c.id=p.content_id JOIN opportunities o ON o.id=c.opportunity_id'))+'</p><div class="grid">'
   rows=d.execute('SELECT v.title,v.body,c.slug,o.category FROM publications p JOIN versions v ON v.id=p.version_id JOIN contents c ON c.id=p.content_id JOIN opportunities o ON o.id=c.opportunity_id WHERE (v.title LIKE ? OR v.body LIKE ?) AND (?="" OR o.category=?)',('%'+term+'%','%'+term+'%',cat,cat)).fetchall()
   body+=''.join(card(r['title'],'<span class="tag">'+esc(r['category'])+'</span><p>'+esc(r['body'][:180])+'…</p><a href="/portal/'+esc(r['slug'])+'">Ler artigo →</a>') for r in rows)+'</div>'
   if not rows:body+='<p>Nenhum conteúdo publicado para esta busca.</p>'
  else:
   r=d.execute('SELECT v.*,p.created published,u.email,o.sources FROM publications p JOIN contents c ON c.id=p.content_id JOIN versions v ON v.id=p.version_id JOIN users u ON u.id=v.author JOIN opportunities o ON o.id=c.opportunity_id WHERE c.slug=?',(path.split('/')[-1],)).fetchone()
   if not r:return self.send(self.page('Artigo não encontrado',body),404)
   body+='<article><h2>'+esc(r['title'])+'</h2><small>Por '+esc(r['email'])+' · Atualizado '+esc(r['published'])+'</small><pre>'+esc(r['body'])+'</pre><h3>Referências</h3><pre>'+esc(r['sources'])+'</pre></article>'
  return self.send(self.page('Casa bonita e verde',body))
 def do_POST(self):
  if int(self.headers.get('Content-Length','0'))>1_000_000:return self.send('Entrada muito grande',413)
  data=urllib.parse.parse_qs(self.rfile.read(int(self.headers.get('Content-Length','0'))).decode(),keep_blank_values=True);f=lambda k,default='':data.get(k,[default])[0]
  with connect(DB) as d:
   if self.path=='/login':
    user=d.execute('SELECT * FROM users WHERE email=?',(f('email').strip().lower(),)).fetchone()
    # Rate limiting global por endereço, em memória, evita guardar senhas ou dados sensíveis.
    attempts=LOGIN_ATTEMPTS.get(self.client_address[0],[]);attempts=[t for t in attempts if t>time.time()-300]
    LOGIN_ATTEMPTS[self.client_address[0]]=attempts+[time.time()]
    if len(attempts)>=10:return self.send('Muitas tentativas. Aguarde cinco minutos.',429)
    if not user or not hmac.compare_digest(password(f('password'),user['password'].split(':')[0]),user['password']):return self.send('Credenciais inválidas. <a href="/">Voltar</a>',401)
    token=secrets.token_urlsafe(32);d.execute('INSERT INTO sessions VALUES(?,?,?,?)',(token,user['id'],secrets.token_urlsafe(32),time.time()+28800));d.commit();return self.redirect('/',f'session={token}; HttpOnly; SameSite=Strict; Path=/'+('; Secure' if os.environ.get('COOKIE_SECURE')=='1' else ''))
   self.s=self.session(d)
   if not self.s:return self.send('Autenticação necessária',401)
   if not hmac.compare_digest(f('csrf'),self.s['csrf']):return self.send('CSRF inválido',403)
   origin=self.headers.get('Origin')
   if origin and urllib.parse.urlsplit(origin).netloc!=self.headers.get('Host'):return self.send('Origem inválida',403)
   action=f('action');u=self.s['user_id'];c=int(f('id','0') or 0);dest='/'
   try:
    role=self.s['role'];allowed={'admin':None,'editor':{'opportunity','op_decision','brief','version','asset','metrics','agent'},'reviewer':{'review','agent'}}
    if allowed[role] is not None and action not in allowed[role]:return self.send('Permissão insuficiente',403)
    d.execute('BEGIN IMMEDIATE')
    if action=='opportunity':
     if not f('title').strip():raise ValueError('Informe um título.')
     sources=[valid_url(s.strip()) for s in f('sources').splitlines() if s.strip()]
     if not sources:raise ValueError('Cadastre ao menos uma fonte.')
     scores=[float(f('score'+str(i))) if f('score'+str(i)) else None for i in range(5)];ranking(scores,[25,25,20,20,10])
     d.execute('INSERT INTO opportunities(title,category,kind,keyword,sources,scores,priority,created) VALUES(?,?,?,?,?,?,?,?)',(f('title'),f('category'),f('kind'),f('keyword'),json.dumps({'urls':sources,'consulted':now(),'context':f('context')},ensure_ascii=False),json.dumps(scores),'',now()));dest='/oportunidades'
    elif action=='op_decision':
     if f('status') not in ('aprovada','adiada','rejeitada') or not f('reason').strip():raise ValueError('Decisão e justificativa são obrigatórias.')
     o=d.execute('SELECT * FROM opportunities WHERE id=?',(c,)).fetchone()
     if not o:raise ValueError('Oportunidade inexistente.')
     d.execute('UPDATE opportunities SET status=?,priority=? WHERE id=?',(f('status'),f('reason'),c))
     if f('status')=='aprovada':d.execute('INSERT OR IGNORE INTO contents(opportunity_id,title,slug) VALUES(?,?,?)',(c,o['title'],'pauta-'+str(c)))
     dest='/editorial'
    elif action=='brief':
     if not f('brief').strip():raise ValueError('Preencha o brief.')
     d.execute("UPDATE contents SET brief=?,responsible=?,planned=?,state=CASE WHEN current_version=0 THEN 'brief_aprovado' ELSE state END WHERE id=?",(f('brief'),f('responsible'),f('planned'),c));dest=f'/conteudo/{c}'
    elif action=='version':
     x,v=current(d,c)
     if not x['brief']:raise ValueError('Aprove o brief antes do texto.')
     save_version(d,c,u,f('title'),f('body'),f('claims'));dest=f'/conteudo/{c}'
    elif action=='review':
     run=execute(d,c,'revisao');out=json.loads(d.execute('SELECT output FROM runs WHERE id=?',(run,)).fetchone()[0])
     if f('result')=='aprovado' and out['problemas']:raise ValueError('Assistente revisor identificou bloqueios: '+json.dumps(out['problemas'],ensure_ascii=False))
     review(d,c,u,f('result'),f('issues'),f('limitations'));dest=f'/conteudo/{c}'
    elif action=='agent':execute(d,c,f('agent'));dest='/agentes'
    elif action=='approve':approve(d,c,u);dest=f'/conteudo/{c}'
    elif action=='publish':publish(d,c,u);dest='/portal'
    elif action=='asset':
     x,v=current(d,c);d.execute("INSERT INTO assets(content_id,version_id,kind,origin,license,reference,alt,status,required) VALUES(?,?,?,?,?,?,?,'pendente',?)",(c,v['id'] if v else None,f('kind'),f('origin'),f('license'),f('reference'),f('alt'),int(f('required'))));dest='/midia'
    elif action=='metrics':
     for r in csv.DictReader(io.StringIO(f('csv'))):
      cid=int(r['content_id']);current(d,cid)
      if not d.execute('SELECT 1 FROM publications WHERE content_id=?',(cid,)).fetchone():raise ValueError('Métricas exigem publicação associada.')
      start=datetime.date.fromisoformat(r['start']);end=datetime.date.fromisoformat(r['end']);value=float(r['value'])
      import math
      if end<start or not math.isfinite(value) or value<0 or r['kind'] not in ('estimado','confirmado') or not r['source'].strip():raise ValueError('Métrica inválida.')
      key=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
      d.execute('INSERT OR IGNORE INTO metrics(content_id,source,start,end,name,value,kind,import_key,created) VALUES(?,?,?,?,?,?,?,?,?)',(cid,r['source'],str(start),str(end),r['name'],value,r['kind'],key,now()))
     dest='/analytics'
    elif action=='settings':
     weights=json.loads(f('weights'));ranking([None]*5,weights)
     if float(f('budget'))<0:raise ValueError('Limite inválido.')
     d.execute("UPDATE settings SET value=? WHERE key='weights'",(json.dumps(weights),));d.execute("UPDATE settings SET value=? WHERE key='budget'",(f('budget'),));dest='/configuracoes'
    elif action=='user':
     if len(f('password'))<12:raise ValueError('Use pelo menos 12 caracteres.')
     if f('role') not in ('admin','reviewer','editor'):raise ValueError('Papel inválido.')
     d.execute('INSERT INTO users(email,password,role) VALUES(?,?,?)',(f('email').strip().lower(),password(f('password')),f('role')));dest='/configuracoes'
    else:raise ValueError('Operação desconhecida.')
    audit(d,u,action,c);d.commit();return self.redirect(dest)
   except (ValueError,KeyError,TypeError,sqlite3.IntegrityError) as e:
    d.rollback()
    d.execute('INSERT INTO runs(content_id,agent,instruction_version,provider,status,error,cost,cost_kind,created) VALUES(?,?,?,?,?,?,?,?,?)',(c if d.execute('SELECT 1 FROM contents WHERE id=?',(c,)).fetchone() else None,action,'v1','manual','falha',str(e),0,'confirmado',now()));d.commit()
    return self.send(self.page('Operação não concluída','<p class="error">'+esc(e)+'</p><a href="/editorial">Voltar à central</a>'),400)
LOGIN_ATTEMPTS={}
def main():
 import argparse,getpass
 p=argparse.ArgumentParser();p.add_argument('command',choices=['init','serve']);p.add_argument('--email',default='admin@local');p.add_argument('--port',type=int,default=8000);args=p.parse_args()
 with connect(DB) as d:
  migrate(d)
  if args.command=='init':
   pw=getpass.getpass('Senha inicial (12+ caracteres): ')
   if len(pw)<12:raise SystemExit('Senha curta.')
   d.execute('INSERT INTO users(email,password,role) VALUES(?,?,?)',(args.email.lower(),password(pw),'admin'));d.commit();print('Administrador criado.');return
 print(f'Abra http://127.0.0.1:{args.port}');ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
if __name__=='__main__':main()
