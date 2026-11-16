import unittest,urllib.request,urllib.error,urllib.parse,json,re
import app,portal
from domain import connect,migrate,save_version,review,approve,publish
from test_http import HTTP as _HTTP
class Ads(unittest.TestCase):
 def setUp(self):self.d=connect(':memory:');migrate(self.d)
 def tearDown(self):self.d.close()
 def test_default_reserved_no_google(self):
  self.assertFalse(portal.google_enabled(self.d));self.assertIn('Publicidade',portal.ad(self.d,'home_top'));self.assertNotIn('adsbygoogle',portal.ad(self.d,'home_top'))
 def test_course_config_persists_and_escapes(self):
  value={**portal.DEFAULT_AD,'mode':'course','title':'Curso <script>alert(1)</script>','description':'Comece sua horta','url':'https://example.org/curso','button':'Conhecer'}
  portal.save_ad(self.d,'sidebar',value)
  self.assertEqual(portal.ad_config(self.d,'sidebar')['url'],value['url'])
  output=portal.ad(self.d,'sidebar');self.assertIn('rel="sponsored',output);self.assertIn('&lt;script&gt;',output);self.assertNotIn('<script>',output)
 def test_validate_google_and_urls(self):
  for bad in ['javascript:alert(1)','http://example.org/','https://user:pass@example.org/']:
   with self.assertRaises(ValueError):portal.save_ad(self.d,'home_top',{**portal.DEFAULT_AD,'mode':'course','title':'Curso','url':bad})
  with self.assertRaises(ValueError):portal.save_ad(self.d,'home_top',{**portal.DEFAULT_AD,'mode':'google','google_slot':'1234567890'})
  with self.assertRaises(ValueError):portal.save_site(self.d,{**portal.DEFAULT_SITE,'adsense_client':'<script>'})
  portal.save_site(self.d,{**portal.DEFAULT_SITE,'adsense_client':'ca-pub-1234567890123456'})
  portal.save_ad(self.d,'home_top',{**portal.DEFAULT_AD,'mode':'google','google_slot':'1234567890'})
  self.assertTrue(portal.google_enabled(self.d));self.assertIn('data-ad-slot="1234567890"',portal.ad(self.d,'home_top'))
 def test_disabled_and_banner_validation(self):
  portal.save_ad(self.d,'home_top',{**portal.DEFAULT_AD,'mode':'disabled'});self.assertEqual(portal.ad(self.d,'home_top'),'')
  with self.assertRaises(ValueError):portal.save_site(self.d,{**portal.DEFAULT_SITE,'hero_image':'https://example.org/image.jpg'})
 def test_safe_article_markdown(self):
  output=''.join(portal.body_blocks('# Título\n\nTexto **importante** <script>alert(1)</script>\n\n- Item\n\n[Fonte](https://example.org/)'))
  self.assertIn('<h2>Título</h2>',output);self.assertIn('<strong>importante</strong>',output);self.assertNotIn('<script>',output);self.assertIn('<ul>',output);self.assertIn('href="https://example.org/"',output)

class PublicPortal(_HTTP):
 def seed_publication(self):
  with app.connect(app.DB) as d:
   admin=d.execute("SELECT id FROM users WHERE role='admin'").fetchone()[0]
   oid=d.execute('INSERT INTO opportunities(title,category,kind,sources,scores) VALUES(?,?,?,?,?) RETURNING id',('Pauta de teste','Hortas em vasos','Notícia',json.dumps({'urls':['https://example.org/fonte']}),'[null,null,null,null,null]')).fetchone()[0]
   cid=d.execute('INSERT INTO contents(opportunity_id,title,slug,brief) VALUES(?,?,?,?) RETURNING id',(oid,'Notícia publicada','noticia-'+str(oid),'Brief')).fetchone()[0]
   save_version(d,cid,admin,'Notícia publicada','# Texto completo\n\nPrimeiro parágrafo.\n\nSegundo parágrafo.\n\nFINAL INTEGRAL DA PUBLICAÇÃO.')
   review(d,cid,admin,'aprovado','','Fontes verificadas no teste.');approve(d,cid,admin);publish(d,cid,admin)
   save_version(d,cid,admin,'RASCUNHO PRIVADO','NUNCA EXIBIR ESTE RASCUNHO')
  return cid,oid
 def test_home_is_blog_for_everyone_admin_is_private(self):
  code,body=self.request('/');self.assertEqual(code,200);self.assertIn('Uma casa mais leve',body);self.assertIn('Plantas para apartamentos',body);self.assertNotIn('Fluxo de produção',body)
  self.assertIn('Uma casa mais leve',self.request('/',cookie=self.identity('admin'))[1])
  self.assertIn('Entrar',self.request('/admin')[1]);self.assertEqual(self.request('/admin',cookie=self.identity('editor'))[0],403)
  self.assertIn('Visão geral',self.request('/admin',cookie=self.identity('admin'))[1])
 def test_full_article_ads_search_and_version_isolation(self):
  cid,oid=self.seed_publication();code,body=self.request('/portal/noticia-'+str(oid))
  self.assertEqual(code,200);self.assertIn('FINAL INTEGRAL DA PUBLICAÇÃO.',body);self.assertIn('<h2>Texto completo</h2>',body)
  self.assertNotIn('RASCUNHO PRIVADO',body);self.assertNotIn('NUNCA EXIBIR',body)
  for slot in ['article_top','article_middle','article_bottom','sidebar']:self.assertIn('data-position="'+slot+'"',body)
  self.assertIn('https://example.org/fonte',body)
  home=self.request('/?tipo=Not%C3%ADcia')[1];self.assertIn('Notícia publicada',home);self.assertNotIn('RASCUNHO PRIVADO',home)
  self.assertNotIn('Notícia publicada',self.request('/?tipo=Comparativo')[1])
  self.assertEqual(self.request('/portal/inexistente')[0],404)
 def test_settings_permissions_and_course_ad_end_to_end(self):
  editor=self.identity('editor');admin=self.identity('admin')
  data=dict(portal.DEFAULT_AD,action='portal_ad',csrf='csrf',slot='home_top',mode='course',title='Curso de horta em vasos',description='Campanha de teste',url='https://example.org/curso',button='Ver curso')
  self.assertEqual(self.request('/action',data,editor)[0],403)
  self.assertEqual(self.request('/anuncios',cookie=editor)[0],403)
  self.assertEqual(self.request('/action',data,admin)[0],200)
  self.assertIn('Curso de horta em vasos',self.request('/')[1]);self.assertIn('https://example.org/curso',self.request('/')[1])
  data['csrf']='wrong';self.assertEqual(self.request('/action',data,admin)[0],403)
 def test_adsense_nonce_and_admin_csp_separate(self):
  admin=self.identity('admin')
  config={**portal.DEFAULT_SITE,'adsense_client':'ca-pub-1234567890123456','action':'portal_site','csrf':'csrf'}
  self.assertEqual(self.request('/action',config,admin)[0],200)
  unit={**portal.DEFAULT_AD,'mode':'google','google_slot':'1234567890','action':'portal_ad','csrf':'csrf','slot':'home_top'}
  self.assertEqual(self.request('/action',unit,admin)[0],200)
  with urllib.request.urlopen(self.base+'/') as response:
   body=response.read().decode();csp=response.headers['Content-Security-Policy']
  self.assertIn('adsbygoogle.js',body);nonce=re.search(r'script nonce="([^"]+)"',body).group(1)
  self.assertIn("'nonce-"+nonce+"'",csp);self.assertIn("'strict-dynamic'",csp)
  req=urllib.request.Request(self.base+'/anuncios',headers={'Cookie':admin})
  with urllib.request.urlopen(req) as response:
   self.assertNotIn('strict-dynamic',response.headers['Content-Security-Policy'])
  self.assertIn('google.com, pub-1234567890123456',self.request('/ads.txt')[1])
 def test_static_routes_and_sitemap(self):
  self.assertEqual(self.request('/static/portal.css')[0],200);self.assertEqual(self.request('/static/garden.svg')[0],200)
  self.assertEqual(self.request('/static/../app.py')[0],404)
  self.assertIn('<urlset',self.request('/sitemap.xml')[1]);self.assertIn('/portal/sobre',self.request('/sitemap.xml')[1])
del _HTTP
