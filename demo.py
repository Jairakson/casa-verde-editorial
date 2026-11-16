"""Dados fictícios e identificados. Não publica nem cria credenciais."""
import app,json
with app.connect(app.DB) as d:
 app.migrate(d)
 if not d.execute("SELECT 1 FROM opportunities WHERE title LIKE '[DEMONSTRAÇÃO]%' ").fetchone():
  d.execute('INSERT INTO opportunities(title,category,kind,keyword,sources,scores,priority,created) VALUES(?,?,?,?,?,?,?,?)',('[DEMONSTRAÇÃO] Como planejar uma horta em vasos','Hortas em vasos','Tutorial','horta em vasos',json.dumps({'urls':['https://www.embrapa.br/'],'consulted':None,'context':'Exemplo de cadastro, não pesquisa realizada. Confirmar fonte específica antes de escrever.'},ensure_ascii=False),json.dumps([None,None,55,80,95]),'Notas editoriais fictícias para demonstração, sem dados de demanda.',app.now()))
  d.commit()
 print('Oportunidade de demonstração disponível; nenhuma publicação criada.')
