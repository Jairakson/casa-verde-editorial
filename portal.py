"""Portal público e configuração de anúncios. Renderiza somente versões publicadas."""
import datetime,html,json,os,re,urllib.parse
from zoneinfo import ZoneInfo
E=lambda value:html.escape(str(value if value is not None else ''))
CATEGORIES=['Plantas para apartamentos','Decoração de salas pequenas','Varandas e jardins pequenos','Cuidados com plantas','Hortas em vasos','Organização de ambientes','Guias de compra','Projetos reais e faça você mesmo']
SLOTS={'home_top':'Página inicial · faixa superior','home_middle':'Página inicial · entre publicações','sidebar':'Barra lateral · início e artigos','article_top':'Artigo · antes do texto','article_middle':'Artigo · dentro do texto','article_bottom':'Artigo · final da leitura'}
DEFAULT_SITE={'hero_title':'Uma casa mais leve. Uma vida mais verde.','hero_text':'Ideias possíveis para transformar pequenos espaços — com plantas, decoração acessível e um jeito mais simples de morar.','hero_label':'Seu cantinho, suas possibilidades','hero_cta':'Encontre sua próxima ideia','hero_image':'','hero_alt':'','adsense_client':''}
DEFAULT_AD={'mode':'placeholder','title':'','description':'','url':'','image':'','alt':'','button':'Conhecer o curso','google_slot':''}
def setting(d,key,default):
 row=d.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
 if not row:return dict(default)
 try:
  value=json.loads(row[0]);return {**default,**value} if isinstance(value,dict) else dict(default)
 except (ValueError,TypeError):return dict(default)
def site(d):return setting(d,'portal_site',DEFAULT_SITE)
def ad_config(d,slot):return setting(d,'portal_ad_'+slot,DEFAULT_AD)
def url(value):
 value=value.strip()
 if not value:return ''
 p=urllib.parse.urlsplit(value)
 if p.scheme!='https' or not p.hostname or p.username or p.password or any(ord(c)<32 for c in value) or len(value)>2000:raise ValueError('Use uma URL HTTPS válida, sem credenciais.')
 return value
def save_site(d,values):
 data={k:str(values.get(k,'' )).strip() for k in DEFAULT_SITE}
 for k in ['hero_title','hero_text','hero_label','hero_cta','hero_alt']:
  if len(data[k])>600:raise ValueError('Texto do banner muito longo.')
 if not data['hero_title'] or not data['hero_cta']:raise ValueError('Informe o título e o botão do banner.')
 data['hero_image']=url(data['hero_image'])
 if data['hero_image'] and not data['hero_alt']:raise ValueError('Informe o texto alternativo da imagem do banner.')
 if data['adsense_client'] and not re.fullmatch(r'ca-pub-\d{16}',data['adsense_client']):raise ValueError('ID AdSense inválido. Formato: ca-pub- seguido de 16 dígitos.')
 d.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',('portal_site',json.dumps(data,ensure_ascii=False)))
def save_ad(d,slot,values):
 if slot not in SLOTS:raise ValueError('Posição de anúncio inválida.')
 data={k:str(values.get(k,'')).strip() for k in DEFAULT_AD}
 if data['mode'] not in ('disabled','placeholder','google','course'):raise ValueError('Tipo de anúncio inválido.')
 for k in ['title','description','alt','button']:
  if len(data[k])>600:raise ValueError('Texto de anúncio muito longo.')
 data['url']=url(data['url']);data['image']=url(data['image'])
 if data['mode']=='course' and (not data['title'] or not data['url'] or not data['button']):raise ValueError('Campanhas próprias exigem título, link e texto do botão.')
 if data['image'] and not data['alt']:raise ValueError('Informe texto alternativo da imagem do anúncio.')
 if data['google_slot'] and not re.fullmatch(r'\d{10}',data['google_slot']):raise ValueError('Unidade AdSense deve conter 10 dígitos.')
 if data['mode']=='google' and (not site(d)['adsense_client'] or not data['google_slot']):raise ValueError('Configure o ID da conta AdSense e o ID desta unidade antes de ativar.')
 d.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',('portal_ad_'+slot,json.dumps(data,ensure_ascii=False)))
def ad(d,slot):
 config=ad_config(d,slot);kind=config['mode']
 if kind=='disabled':return ''
 body='';classes=''
 if kind=='course':
  classes=' course-ad'
  image=f'<img src="{E(config["image"])}" alt="{E(config["alt"])}" loading="lazy" referrerpolicy="no-referrer">' if config['image'] else '<span class="course-symbol" aria-hidden="true">✳</span>'
  body=f'<div class="course-content">{image}<div><span class="eyebrow">Aprenda com a Casa &amp; Verde</span><h3>{E(config["title"])}</h3><p>{E(config["description"])}</p><a class="button" href="{E(config["url"])}" rel="sponsored noopener">{E(config["button"])} <span aria-hidden="true">↗</span></a></div></div>'
 elif kind=='google' and re.fullmatch(r'ca-pub-\d{16}',site(d)['adsense_client']) and re.fullmatch(r'\d{10}',config['google_slot']):
  body=f'<ins class="adsbygoogle" style="display:block" data-ad-client="{E(site(d)["adsense_client"])}" data-ad-slot="{E(config["google_slot"])}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
 else:
  body='<div class="ad-placeholder"><span class="ad-leaf" aria-hidden="true">✳</span><span>Um espaço para boas conexões</span></div>'
 return f'<aside class="ad-slot{classes}" data-position="{slot}" aria-label="Publicidade"><div class="ad-label">Publicidade</div>{body}</aside>'
def google_enabled(d):return bool(re.fullmatch(r'ca-pub-\d{16}',site(d)['adsense_client'])) and any(ad_config(d,k)['mode']=='google' for k in SLOTS)
def origin():
 value=os.environ.get('PUBLIC_SITE_URL') or os.environ.get('RENDER_EXTERNAL_URL') or 'https://casa-verde-editorial.onrender.com'
 try:return url(value).rstrip('/')
 except ValueError:return 'https://casa-verde-editorial.onrender.com'
def date(value):
 try:return datetime.datetime.fromisoformat(value).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y')
 except (ValueError,TypeError):return ''
QUERY='''SELECT c.id content_id,c.slug,v.title,v.body,p.created published,o.category,o.kind,o.sources FROM publications p JOIN contents c ON c.id=p.content_id JOIN versions v ON v.id=p.version_id JOIN opportunities o ON o.id=c.opportunity_id'''
def excerpt(text,limit=160):return re.sub(r'\s+',' ',re.sub(r'[#*`\[\]]','',text or '')).strip()[:limit].rstrip()+'…' if len(text or '')>limit else re.sub(r'\s+',' ',text or '').strip()
def article_card(row,index=0):
 category=row['category'] or 'Casa e jardim';link='/portal/'+urllib.parse.quote(row['slug'],safe='')
 return f'<article class="story"><a class="story-art tone-{index%4}" href="{link}" aria-label="{E(row["title"])}"><img src="/static/garden.svg" alt="" loading="lazy"><span class="art-label">{E(category)}</span></a><div class="story-content"><div class="story-meta">{E(row["kind"] or "Artigo")} <span>·</span> {date(row["published"])}</div><h3><a href="{link}">{E(row["title"])}</a></h3><p>{E(excerpt(row["body"]))}</p><a class="read-link" href="{link}">Continuar a leitura <span aria-hidden="true">↗</span></a></div></article>'
def sidebar(d):
 return '<aside class="reading-sidebar"><section class="editor-note"><span class="eyebrow">O nosso olhar</span><h2>Pequenos espaços.<br>Grandes possibilidades.</h2><p>Uma casa acolhedora se constrói aos poucos. Comece com o que você tem, encontre seu ritmo e deixe o verde fazer parte.</p><a href="/portal/sobre" class="read-link">Conheça a Casa &amp; Verde ↗</a></section>'+ad(d,'sidebar')+'<section class="sidebar-topics"><h2>Explore por tema</h2>'+''.join(f'<a href="/?categoria={urllib.parse.quote(c)}#publicacoes">{E(c)} <span aria-hidden="true">↗</span></a>' for c in CATEGORIES)+'</section></aside>'
def inline(text):
 # Markdown limitado; todo HTML de origem é escapado, links só HTTPS.
 out=[];at=0
 pattern=re.compile(r'\[([^\]\n]+)\]\((https://[^\s)]+)\)')
 for match in pattern.finditer(text):
  out.append(E(text[at:match.start()]))
  try:target=url(match.group(2));out.append(f'<a href="{E(target)}" rel="noopener noreferrer">{E(match.group(1))}</a>')
  except ValueError:out.append(E(match.group(0)))
  at=match.end()
 out.append(E(text[at:]));return re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',''.join(out))
def body_blocks(text):
 blocks=[];paragraph=[];items=[];code=[];fenced=False
 def flush():
  if paragraph:blocks.append('<p>'+inline(' '.join(paragraph))+'</p>');paragraph.clear()
  if items:blocks.append('<ul>'+''.join('<li>'+inline(v)+'</li>' for v in items)+'</ul>');items.clear()
 for line in text.splitlines():
  if line.strip().startswith('```'):
   flush()
   if fenced:blocks.append('<pre><code>'+E('\n'.join(code))+'</code></pre>');code=[]
   fenced=not fenced;continue
  if fenced:code.append(line);continue
  if not line.strip():flush();continue
  match=re.match(r'^(#{1,6})\s+(.+)',line)
  if match:flush();level=min(len(match.group(1))+1,4);blocks.append(f'<h{level}>'+inline(match.group(2))+f'</h{level}>')
  elif re.match(r'^\s*[-*]\s+',line):
   if paragraph:flush()
   items.append(re.sub(r'^\s*[-*]\s+','',line))
  else:
   if items:flush()
   paragraph.append(line.strip())
 flush()
 if code:blocks.append('<pre><code>'+E('\n'.join(code))+'</code></pre>')
 return blocks or ['<p>'+E(text)+'</p>']
def references(raw):
 try:
  parsed=json.loads(raw);urls=parsed.get('urls',[]) if isinstance(parsed,dict) else []
 except (ValueError,TypeError):urls=re.findall(r'https://[^\s"<>]+',raw or '')
 links=[]
 for item in urls:
  try:
   target=str(item).strip();parsed=urllib.parse.urlsplit(target)
   if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:continue
   links.append(f'<li><a href="{E(target)}" rel="noopener noreferrer">{E(target)}</a></li>')
  except (ValueError,AttributeError):continue
 return '<section class="references"><h2>Fontes e referências</h2><ul>'+''.join(links)+'</ul></section>' if links else ''
def home(d,query):
 config=site(d);q=query.get('q',[''])[0][:200];category=query.get('categoria',[''])[0];kind=query.get('tipo',[''])[0]
 rows=d.execute(QUERY+" WHERE (LOWER(v.title) LIKE LOWER(?) OR LOWER(v.body) LIKE LOWER(?)) AND (?='' OR o.category=?) AND (?='' OR o.kind=?) ORDER BY p.created DESC,c.id DESC",('%'+q+'%','%'+q+'%',category,category,kind,kind)).fetchall()
 hero_image=f'<img src="{E(config["hero_image"])}" alt="{E(config["hero_alt"])}" fetchpriority="high">' if config['hero_image'] else '<img src="/static/garden.svg" alt="Ilustração de um cantinho com plantas em vasos junto à janela" fetchpriority="high">'
 hero=f'<section class="hero"><div class="hero-copy"><span class="eyebrow">{E(config["hero_label"])}</span><h1>{E(config["hero_title"])}</h1><p>{E(config["hero_text"])}</p><a class="button" href="#categorias">{E(config["hero_cta"])} <span aria-hidden="true">↗</span></a><div class="hero-foot">DECORAÇÃO ACESSÍVEL <span>✳</span> VERDE POR PERTO</div></div><div class="hero-art">{hero_image}<span class="hero-caption">Inspiração para morar bem, do seu jeito.</span></div></section>'
 cats='<section id="categorias" class="category-section"><div class="section-heading"><div><span class="eyebrow">Um tema para cada cantinho</span><h2>Por onde vamos começar?</h2></div><span class="muted">Inspiração que cabe na sua casa.</span></div><div class="category-grid">'+''.join(f'<a class="category-tile" href="/?categoria={urllib.parse.quote(c)}#publicacoes"><span class="category-number">0{i+1}</span><h3>{E(c)}</h3><span class="category-arrow" aria-hidden="true">↗</span></a>' for i,c in enumerate(CATEGORIES))+'</div></section>'
 filtered=bool(q or category or kind)
 heading=category or ('Resultados da busca' if q else 'Notícias' if kind=='Notícia' else 'Ideias fresquinhas para sua casa')
 form='<form class="search-form" method="get" action="/#publicacoes"><label class="sr-only" for="portal-search">Buscar conteúdos</label><input id="portal-search" name="q" value="'+E(q)+'" placeholder="O que você quer transformar hoje?">'+(f'<input type="hidden" name="categoria" value="{E(category)}">' if category else '')+(f'<input type="hidden" name="tipo" value="{E(kind)}">' if kind else '')+'<button type="submit">Buscar ↗</button></form>'
 feed='<section id="publicacoes"><div class="section-heading"><div><span class="eyebrow">'+('Explore o portal' if filtered else 'Para ler, aprender e colocar em prática')+'</span><h2>'+E(heading)+'</h2></div><a class="read-link" href="/?tipo=Not%C3%ADcia#publicacoes">Ver notícias ↗</a></div>'+form
 if filtered:feed+='<p class="filter-note">'+str(len(rows))+' publicação(ões) encontrada(s). <a href="/#publicacoes">Limpar filtros</a></p>'
 feed+='<div class="content-layout"><div>'
 if rows:
  feed+='<div class="story-grid">'+''.join(article_card(r,i) for i,r in enumerate(rows[:4]))+'</div>'+ad(d,'home_middle')
  if len(rows)>4:feed+='<div class="story-grid">'+''.join(article_card(r,i) for i,r in enumerate(rows[4:]))+'</div>'
 else:feed+='<div class="empty-state"><span aria-hidden="true">✳</span><h3>'+('Ainda não encontramos uma publicação para esta busca.' if filtered else 'As próximas boas ideias estão a caminho.')+'</h3><p>'+('Experimente outro termo ou explore as categorias.' if filtered else 'Nossos artigos aparecerão aqui depois de revisados e publicados pela equipe editorial.')+'</p><a class="read-link" href="#categorias">Explorar categorias ↗</a></div>'+ad(d,'home_middle')
 feed+='</div>'+sidebar(d)+'</div></section>'
 return hero+ad(d,'home_top')+cats+feed,'Casa & Verde — decoração acessível e plantas para pequenos espaços','/',200
def article(d,slug):
 row=d.execute(QUERY+' WHERE c.slug=?',(slug,)).fetchone()
 if not row:return '<section class="empty-state"><h1>Essa página ainda não criou raízes.</h1><p>O conteúdo pode não ter sido publicado ou o endereço mudou.</p><a class="button" href="/">Voltar ao início</a></section>','Conteúdo não encontrado','/portal/'+urllib.parse.quote(slug),404
 blocks=body_blocks(row['body']);target=max(1,len(blocks)//2)
 middle=next((i+1 for i,block in enumerate(blocks) if i+1>=target and block.endswith(('</p>','</ul>','</pre>'))),len(blocks))
 text=''.join(blocks[:middle])+ad(d,'article_middle')+''.join(blocks[middle:])
 category=row['category'] or 'Casa e jardim';minutes=max(1,round(len(row['body'].split())/200))
 related=d.execute(QUERY+' WHERE c.id!=? AND o.category=? ORDER BY p.created DESC LIMIT 3',(row['content_id'],category)).fetchall()
 body=f'<nav class="breadcrumbs" aria-label="Caminho"><a href="/">Início</a><span>/</span><a href="/?categoria={urllib.parse.quote(category)}#publicacoes">{E(category)}</a></nav><header class="article-header"><span class="eyebrow">{E(category)} · {E(row["kind"] or "Artigo")}</span><h1>{E(row["title"])}</h1><div class="article-meta"><span class="author-avatar" aria-hidden="true">cv</span><span>Por <strong>Redação Casa &amp; Verde</strong><br><span class="muted">Atualizado em {date(row["published"])} · {minutes} min de leitura</span></span></div></header>'+ad(d,'article_top')+'<div class="content-layout article-layout"><article class="article-body">'+text+references(row['sources'])+'<div class="editorial-signature"><span aria-hidden="true">✳</span><p>Um passo de cada vez também transforma.<br><strong>Casa bonita, verde e possível.</strong></p></div>'+ad(d,'article_bottom')+'</article>'+sidebar(d)+'</div>'
 if related:body+='<section class="related"><div class="section-heading"><div><span class="eyebrow">Continue se inspirando</span><h2>Mais ideias para o seu cantinho</h2></div></div><div class="related-grid">'+''.join(article_card(r,i) for i,r in enumerate(related))+'</div></section>'
 return body,row['title']+' · Casa & Verde','/portal/'+urllib.parse.quote(slug,safe=''),200

def render(d,path,query):
 if path in ('/','/portal','/portal/'):return home(d,query)
 if path in ('/portal/sobre','/portal/privacidade'):
  privacy=path.endswith('privacidade')
  body='<article class="institutional"><span class="eyebrow">Casa &amp; Verde</span><h1>'+('Privacidade e publicidade' if privacy else 'Uma casa bonita e verde é possível.')+'</h1>'
  if privacy:body+='<p>O portal exibe conteúdos públicos. O painel editorial exige autenticação e usa um cookie de sessão para manter o acesso.</p><h2>Publicidade</h2><p>Espaços publicitários são identificados como Publicidade. Campanhas de cursos próprios são separadas do conteúdo editorial. Quando ativados pela equipe, os anúncios do Google podem utilizar cookies e tecnologias de terceiros conforme as configurações e políticas desse serviço.</p><p>Consulte <a href="https://policies.google.com/technologies/ads" rel="noopener noreferrer">como o Google utiliza informações em publicidade</a> e suas opções de controle. Relações comerciais em um artigo devem ser identificadas no próprio conteúdo.</p>'
  else:body+='<p class="intro">Decoração acessível e plantas para espaços pequenos. Ideias para quem acredita que morar bem começa com escolhas possíveis.</p><h2>Nosso compromisso editorial</h2><p>Publicamos artigos permanentes, tutoriais, comparativos e notícias, respeitando as diferenças entre cada formato. Todo conteúdo precisa de revisão e aprovação humana antes de chegar ao portal.</p><p>Referências acompanham as orientações. Estimativas não são apresentadas como dados confirmados; análises de especificações não são tratadas como testes de produtos. Ilustrações não representam projetos executados nem identificações botânicas confiáveis.</p><h2>Transparência comercial</h2><p>Anúncios e campanhas próprias são identificados. Conteúdos com relações comerciais devem informar essa relação. A publicidade não substitui a revisão das recomendações.</p>'
  return body+'</article>','Privacidade e publicidade' if privacy else 'Sobre a Casa & Verde',path,200
 if path.startswith('/portal/'):return article(d,urllib.parse.unquote(path[len('/portal/'):]))
 return '<section class="empty-state"><h1>Página não encontrada</h1><a href="/">Voltar ao início</a></section>','Página não encontrada',path,404

def document(d,body,title,canonical,nonce,description=None):
 google=''
 if google_enabled(d):
  client=site(d)['adsense_client']
  google=f'<script nonce="{nonce}" async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={E(client)}" crossorigin="anonymous"></script><script nonce="{nonce}">window.addEventListener("load",function(){{document.querySelectorAll("ins.adsbygoogle").forEach(function(){{try{{(window.adsbygoogle=window.adsbygoogle||[]).push({{}})}}catch(e){{}}}})}});</script>'
 return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+E(title)+'</title><meta name="description" content="'+E(description or 'Decoração acessível e plantas para espaços pequenos. Ideias práticas para uma casa bonita, verde e possível.')+'"><link rel="canonical" href="'+E(origin()+canonical)+'"><link rel="stylesheet" href="/static/portal.css">'+google+'</head><body><a class="skip-link" href="#principal">Pular para o conteúdo</a><div class="topline"><span>CASA BONITA, VERDE E POSSÍVEL.</span><a href="/portal/sobre">Conheça nosso olhar ↗</a></div><header class="site-header"><a class="wordmark" href="/" aria-label="Casa e Verde — início">casa <i>&amp;</i> verde<span>.</span><small>IDEIAS PARA MORAR MELHOR</small></a><nav class="main-nav" aria-label="Navegação principal"><a href="/">Início</a><a href="/#categorias">Categorias</a><a href="/?tipo=Not%C3%ADcia#publicacoes">Notícias</a><a href="/?tipo=Tutorial#publicacoes">Faça você mesmo</a><a href="/#aprenda">Cursos</a></nav><a class="admin-link" href="/admin">Área administrativa ↗</a></header><main id="principal" class="site-main">'+body+'</main><section id="aprenda" class="learn-strip"><div class="learn-emblem" aria-hidden="true">✳</div><div><span class="eyebrow">Cultive novas possibilidades</span><h2>Aprender também é um jeito de transformar.</h2><p>Novidades sobre nossos cursos e inscrições serão divulgadas por aqui.</p></div><a class="read-link" href="/portal/sobre">Conheça a Casa &amp; Verde ↗</a></section><footer class="site-footer"><div><a class="wordmark" href="/">casa <i>&amp;</i> verde<span>.</span></a><p>Decoração acessível. Plantas por perto.<br>Uma casa que tem a sua cara.</p></div><div><strong>Explore</strong><a href="/#categorias">Categorias</a><a href="/?tipo=Not%C3%ADcia#publicacoes">Notícias</a><a href="/#aprenda">Cursos</a></div><div><strong>Casa &amp; Verde</strong><a href="/portal/sobre">Sobre e política editorial</a><a href="/portal/privacidade">Privacidade e publicidade</a><a href="/admin">Área administrativa</a></div><p class="footer-bottom">Casa &amp; Verde · Conteúdo com cuidado, referências e transparência.</p></footer></body></html>'
