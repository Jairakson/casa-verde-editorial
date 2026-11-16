import sqlite3,json,datetime,re,hashlib
from pathlib import Path
ROOT=Path(__file__).parent
CRITERIA=['Demanda e tendência','Oportunidade na busca','Monetização','Originalidade','Aderência editorial']
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
from storage import connect,migrate
def ranking(scores,weights):
 if len(scores)!=5 or len(weights)!=5 or sum(weights)!=100 or any(w<0 for w in weights):raise ValueError('Pesos devem somar 100 e conter cinco critérios.')
 if any(s is not None and (not isinstance(s,(int,float)) or not 0<=s<=100) for s in scores):raise ValueError('Notas devem estar entre 0 e 100 ou vazias.')
 coverage=sum(w for s,w in zip(scores,weights) if s is not None)
 return {'score':round(sum(s*w for s,w in zip(scores,weights) if s is not None)/coverage,1) if coverage else None,'coverage':coverage,'provisional':coverage<100,'contributions':[None if s is None else round(s*w/100,1) for s,w in zip(scores,weights)]}
def audit(d,u,a,e,data=''):d.execute('INSERT INTO audit(user_id,action,entity,data,created) VALUES(?,?,?,?,?)',(u,a,str(e),str(data),now()))
def current(d,c):
 x=d.execute('SELECT * FROM contents WHERE id=?',(c,)).fetchone()
 if not x:raise ValueError('Conteúdo não encontrado.')
 return x,d.execute('SELECT * FROM versions WHERE content_id=? AND number=?',(c,x['current_version'])).fetchone()
def save_version(d,c,u,title,body,claims=''):
 x,v=current(d,c)
 if not title.strip() or not body.strip():raise ValueError('Título e texto são obrigatórios.')
 n=x['current_version']+1
 d.execute('INSERT INTO versions(content_id,number,title,body,claims,created,author) VALUES(?,?,?,?,?,?,?)',(c,n,title,body,claims,now(),u))
 d.execute("UPDATE contents SET current_version=?,title=?,state='revisao_texto' WHERE id=?",(n,title,c));audit(d,u,'nova_versao',c,n)
 return n
def review(d,c,u,result,issues,limitations):
 x,v=current(d,c)
 if not v:raise ValueError('Crie uma versão antes da revisão.')
 if result not in ('aprovado','ajustes','bloqueado'):raise ValueError('Resultado inválido.')
 if result=='aprovado' and (v['claims'].strip() or issues.strip() or not limitations.strip()):raise ValueError('Resolva afirmações e problemas; registre as fontes verificadas e limitações.')
 d.execute('INSERT INTO reviews(version_id,reviewer,result,issues,limitations,created) VALUES(?,?,?,?,?,?)',(v['id'],u,result,issues,limitations,now()))
 d.execute('DELETE FROM approvals WHERE version_id=?',(v['id'],))
 d.execute('UPDATE contents SET state=? WHERE id=?',('aprovacao_humana' if result=='aprovado' else 'ajustes',c));audit(d,u,'revisao',v['id'],result)
def eligible(d,c):
 x,v=current(d,c)
 if not v:raise ValueError('Nenhuma versão.')
 r=d.execute('SELECT * FROM reviews WHERE version_id=? ORDER BY id DESC LIMIT 1',(v['id'],)).fetchone()
 if not r or r['result']!='aprovado':raise ValueError('Revisão aprovada da versão atual é obrigatória.')
 if d.execute("SELECT 1 FROM assets WHERE content_id=? AND required=1 AND (status!='aprovado' OR version_id!=? OR version_id IS NULL)",(c,v['id'])).fetchone():raise ValueError('Ativos obrigatórios pendentes ou desatualizados.')
 return x,v
def approve(d,c,u):
 x,v=eligible(d,c);d.execute('INSERT INTO approvals VALUES(?,?,?) ON CONFLICT(version_id) DO UPDATE SET user_id=excluded.user_id,created=excluded.created',(v['id'],u,now()));audit(d,u,'aprovacao_humana',v['id'])
def publish(d,c,u):
 x,v=eligible(d,c)
 if not d.execute('SELECT 1 FROM approvals WHERE version_id=?',(v['id'],)).fetchone():raise ValueError('Aprovação humana da versão exata é obrigatória.')
 d.execute("INSERT INTO publications(content_id,version_id,created,destination) VALUES(?,?,?,'portal') ON CONFLICT(content_id) DO UPDATE SET version_id=excluded.version_id,created=CASE WHEN publications.version_id!=excluded.version_id THEN excluded.created ELSE publications.created END",(c,v['id'],now()))
 d.execute("UPDATE contents SET state='publicado' WHERE id=?",(c,));audit(d,u,'publicacao',v['id'])
def valid_url(url):
 from urllib.parse import urlsplit
 p=urlsplit(url)
 if p.scheme not in ('https','http') or not p.hostname or p.username or p.password:raise ValueError('Use URL HTTP(S) sem credenciais.')
 return url
