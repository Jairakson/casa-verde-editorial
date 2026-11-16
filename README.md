# Casa & Verde — central editorial

Implementação inicial executável em Python 3.11+. PostgreSQL no Render via psycopg; SQLite opcional para testes e desenvolvimento local.
Interface pt-BR. Posicionamento: decoração acessível e plantas para espaços pequenos.

## Executar

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py init --email voce@example.com
# Informe uma senha de pelo menos 12 caracteres no prompt, sem expô-la no terminal.
python app.py serve --port 8000
```

Abra http://127.0.0.1:8000. Login com o administrador criado. O portal em `/portal` é acessível sem autenticação; o painel exige sessão. O servidor escuta somente localhost. Não exponha diretamente à internet. Para produção, é necessário adaptar o servidor a uma implantação HTTPS com proxy, controle persistente de tentativas, sessões e operação monitorada.

```sh
python demo.py                           # opcional; não cria publicação
python -m unittest discover -s tests -v
```

Não há senha padrão nem credenciais externas incluídas. Variáveis aceitas em `.env.example`; exporte-as no shell. O arquivo `.env` não é lido automaticamente.

## Fluxo completo

1. Em Oportunidades, cadastre título, grupo, tipo, palavra-chave, URLs e contexto. Notas editoriais podem ficar vazias. A ausência de nota mantém o critério indisponível. A nota é normalizada pelos pesos disponíveis e a contribuição exibida usa o peso original; com cobertura parcial, as contribuições somadas precisam ser divididas pela cobertura para reproduzir a nota.
2. Aprove a pauta com justificativa. A decisão cria um conteúdo uma única vez. Antes de aprovar, compare a intenção com conteúdos existentes na central.
3. Na central, abra o conteúdo e preencha/salve o brief. Esse ato é a aprovação manual do brief. O assistente Estratégia pode produzir uma estrutura em Agentes e execuções, para copiar e completar no brief.
4. Escreva o texto, com referências junto às afirmações, atribuições e declaração comercial quando aplicável. Salve como nova versão. Nenhuma versão anterior é sobrescrita.
5. Execute o assistente de revisão e faça a revisão humana: severidade, trecho, evidência, correção e limites. O assistente verifica condições locais; não acessa nem confirma fontes externas. O parecer aprovado exige ausência de pendências e registro de fontes conferidas/limitações.
6. Se houver ajustes, salve uma nova versão e repita a revisão. Administrador ou revisor pode registrar o parecer; editor não pode revisar nem publicar.
7. Administrador aprova a versão exata e publica manualmente. Publicar repetidamente atualiza a única publicação daquele conteúdo. Uma alteração posterior exige revisão/aprovação novas; a versão antiga permanece publicada até republicação explícita.
8. Em Analytics, importe CSV com métricas da publicação. Dados idênticos não são duplicados. Não há somatório de fontes ou métricas incompatíveis.

Exemplo de CSV (substitua ID, período e valor por dados reais):

```csv
content_id,source,start,end,name,value,kind
1,EXEMPLO NAO IMPORTAR COMO REAL,2026-10-01,2026-10-31,cliques_organicos,12,estimado
```

## Funciona nesta entrega

- Autenticação com scrypt, sessões de oito horas, cookies HttpOnly/SameSite, CSRF, checagem de origem e permissões no servidor. Papéis: editor, reviewer, admin; usuários criados por administrador.
- Oportunidades manuais e URLs validadas, ranking explicável, pesos configuráveis, decisão justificada.
- Brief, editor de texto simples, versões, revisão obrigatória, aprovação vinculada à versão, publicação manual idempotente no portal interno e auditoria.
- Sete assistentes **locais determinísticos**, com instruções v1, entradas/saídas JSON, versão de origem, identificação de provedor e chave de idempotência. Eles estruturam tarefas, não são modelos de IA.
- Portal com início, busca, filtros de categoria, artigo, autoria, referências, versão publicada e página institucional; sitemap local.
- Agenda em lista, registro de mídia/procedência como pendente, importação CSV, painel de falhas e custos locais reais de zero.
- SQLite e migração inicial; demonstração optativa identificada e não publicada; testes de domínio e HTTP.

## Limites e trabalho restante

Esta é uma base funcional local; não conclui todos os requisitos da plataforma solicitada.

- **IA:** conexão opcional com ChatGPT Plus pelo conector pessoal Windows. Login e autorização reais devem ser feitos pelo usuário no computador. Sem conector ativo, os assistentes continuam locais. Seleção de modelos consulta a conta autorizada. Pesquisa web e conferência remota de fontes não estão habilitadas.
- **Execução:** assistentes determinísticos são síncronos. ChatGPT Plus usa fila persistente no painel, concessões com prazo, cancelamento, retomada limitada e entregas idempotentes. Tokens são registrados quando fornecidos; preço por execução fica indisponível. Limites monetários da página Configurações não controlam a franquia Plus; essa é gerenciada nas configurações oficiais do ChatGPT.
- **Mídia:** briefs/prompts/storyboard são entregues como pendentes. Não gera imagens, áudio nem vídeo, nem faz upload. Ativos obrigatórios pendentes bloqueiam publicação. Aprovação de mídia ainda não tem interface, portanto mantenha-os opcionais neste MVP ou conclua esse módulo antes de exigir mídia.
- **Métricas:** importação manual funcional; sem GSC, GA4, afiliados ou redes conectados. Não calcula receita atribuída ou estimativas automáticas. Recomendações são orientações locais, não análise de IA.
- **Editorial:** sem comentários, notificações, quadro arrastável, comparação visual de versões, consolidação automática, agendamento executável ou arquivamento. Datas planejadas são operacionais; publicar sempre exige ação manual.
- **Portal:** sem adaptador de CMS externo, metadados SEO por artigo, URLs canônicas configuráveis, página de autor própria ou relacionados automáticos. Sitemap usa origem local HTTP; configurar origem e HTTPS antes de hospedar.
- **Segurança/produção:** sem recuperação de senha, MFA, revogação/logout na interface ou proteção persistente/distribuída de login. Escopo inicial de único portal; não é multi-tenant. Backup, TLS, monitoração e servidor de produção são pendentes.
- **Publicação da aplicação:** a habilidade Sites foi consultada; o ambiente não contém os helpers/starter de publicação. A arquitetura Python usa Render com PostgreSQL. O estado efetivo da implantação deve ser confirmado no Dashboard; a existência do Blueprint não comprova publicação.
- Testes automatizados passaram; não foi realizada inspeção visual em navegador.

## Arquitetura

`app.py`: HTTP, HTML escapado, autenticação, autorização e formulários. `domain.py`: invariantes editoriais, ranking, revisão/aprovação/publicação. `agents.py`: módulos especializados locais sem ferramentas externas. `storage.py`: adaptadores de persistência. `migrations/postgres/001_initial.sql`: esquema PostgreSQL versionado; `migrations/001_initial.sql`: esquema SQLite local. `tests/`: verificações essenciais.

Persistência: uma transação por ação; PostgreSQL usa advisory lock transacional para serializar mutações editoriais. SQLite local usa `BEGIN IMMEDIATE`. Versões são append-only na aplicação. Publicação referencia uma versão imutável e tem unicidade por conteúdo. Uma aprovação antiga continua na auditoria mas nunca autoriza uma nova versão. A revisão mais recente determina elegibilidade. Falha reverte a operação e é registrada separadamente.

Dados externos são tratados como texto e escapados no HTML; não há execução de HTML, comandos, instruções de fontes ou requisições de rede. URLs não são buscadas pelo servidor. Histórico usa UTC ISO; o planejamento é interpretado como horário de São Paulo. Timestamps ISO de histórico são formatados em America/Sao_Paulo na interface; saídas JSON preservam UTC para rastreabilidade.

A evolução recomendada separa transporte do domínio, adiciona migrations incrementais, fila persistente e adaptadores de provedor com schemas JSON e ferramentas restritas. Antes de ativar qualquer provedor: impor orçamento, timeout, retries, cancelamento e idempotência; custos estimados/confirmados devem permanecer distintos. Nenhum agente terá permissão de publicar. Ações externas deverão ficar em adaptadores com destinos autorizados.

## Verificação desta entrega

18 testes automatizados passaram, incluindo fluxo HTTP completo de oportunidade até publicação e métricas, bloqueios, permissões, CSRF, imutabilidade das versões e idempotência. Testes usam bancos temporários; nenhuma publicação de demonstração é criada no banco de operação. Sem QA visual em navegador.

## Render — gratuito, sem SQLite

O Blueprint usa o projeto `casa-verde-editorial`, ambiente `Production`, região Virginia:

- Serviço web `casa-verde-editorial`, plano **free**, sem disco.
- Banco PostgreSQL `casa-verde-editorial-db`, plano **free**, conexão interna via `DATABASE_URL` e acesso público ao banco bloqueado (`ipAllowList: []`).
- Build instala `requirements.txt` e executa testes locais. Migração PostgreSQL é aplicada uma única vez no início do serviço, protegida por lock transacional e registrada em `schema_migrations`.
- `HOST=0.0.0.0`, porta fornecida pelo Render, cookies Secure e health check `/healthz` com consulta ao banco. SIGTERM encerra o servidor.
- Login inicial: `admin@casa-verde.local`. O Render gera `ADMIN_PASSWORD` automaticamente; consulte o valor apenas no Environment do serviço, sem copiar para chat ou repositório. Após validar o primeiro login, remova a variável de senha. Reinícios não redefinem credenciais existentes.

**Limites verificados na documentação oficial do Render:** o PostgreSQL gratuito expira 30 dias após criação e não inclui backups. Há prazo de 14 dias após expiração para upgrade; depois o banco é excluído. Exporte seus dados antes da expiração. O serviço web pode suspender por inatividade e demorar para responder ao reativar. Workspace tem limite compartilhado de 750 horas gratuitas por mês e apenas um PostgreSQL gratuito ativo. Esses planos são para avaliação, não produção permanente.

O servidor HTTP deste MVP usa a biblioteca padrão Python atrás do proxy TLS do Render. A migração para servidor/framework de produção, limitação persistente de login e backups continua necessária antes de operação pública de maior escala. Conectar o repositório não habilita IA ou outras integrações.

SQLite permanece opcional no código para testes locais. Quando `DATABASE_URL` está configurada, somente PostgreSQL é utilizado; não há arquivo SQLite no serviço Render. Este projeto ainda não tem ferramenta de migração de registros SQLite existentes para PostgreSQL; o primeiro banco remoto inicia vazio.

## Testes PostgreSQL

A suíte `tests/test_postgres.py` valida migração, aprovação, versionamento, idempotência, permissões, CSRF e fluxo HTTP completo em PostgreSQL real. Execute somente contra um banco descartável: ela limpa as tabelas da aplicação desse banco.

```sh
# Defina TEST_POSTGRES_URL com a URL do banco descartável, somente no ambiente.
python -m unittest discover -s tests -v
```

Sem `TEST_POSTGRES_URL`, os testes exclusivos de PostgreSQL são explicitamente pulados e os testes locais continuam ativos. A suíte atual foi executada também contra PostgreSQL 18 descartável, incluindo o conector. Não definir `DATABASE_URL` com um banco real para rodar a suíte; a aplicação usa essa variável em runtime.

## ChatGPT Plus no Windows

O conector pessoal está em `connector/`, com iniciador `Iniciar-Conector.bat`. O guia completo de instalação, pareamento, login oficial, seleção de modelos, execução e solução de problemas está em [connector/README.md](connector/README.md).

A página `/conector` do painel permite autorizar ou revogar computadores. Pareamento exige uma sessão de administrador e CSRF; o token de dispositivo fica protegido no computador e apenas seu hash é salvo no servidor. APIs de fila aceitam exclusivamente o token limitado do computador, sem autorizar aprovação ou publicação. Tokens OpenAI nunca são enviados ao painel.

Tarefas são criadas pela página do conteúdo, consumidas uma por vez pelo conector e vinculadas ao snapshot exato. Redação cria uma nova versão com pendência explícita de conferência humana. Revisão do modelo é um parecer e não é uma aprovação. Alterações no conteúdo/brief/fontes durante a execução impedem aplicar o resultado antigo. Resultado enviado novamente não duplica versões. Um computador pode ser revogado a qualquer momento.

Migrations incrementais `002_connector.sql` (SQLite local) e `postgres/002_connector.sql` criam fila e registros de pareamento. Os testes de login usam chaves sintéticas, validam OIDC/nonce/audience e simulam o stream; não consomem Plus nem criam API keys. A execução real do login e o DPAPI precisam ser confirmados no Windows do usuário.

## Portal público, banner e anúncios

A raiz `/` agora é o site/blog público para todos os visitantes, inclusive administradores autenticados. A antiga Visão geral está em `/admin`, com autenticação e permissão de administrador. Editores e revisores entram na Central editorial. Os endereços existentes de artigos em `/portal/<slug>` e do conector continuam funcionando; `/portal` também abre o portal público.

O portal inclui banner inicial com ilustração editorial própria, oito categorias, busca, filtro exclusivo de notícias, listagem de publicações, texto integral com formatação segura, referências, data, relacionados por categoria e páginas institucionais. Somente a versão referenciada em `publications` aparece no site: rascunhos e mudanças não publicadas continuam privados. Não foram criadas notícias de demonstração nem publicações automáticas para preencher o layout.

Como administrador, abra `/anuncios` (**Portal e anúncios**) para editar o título, texto, botão e imagem HTTPS opcional do banner. Também há seis posições: faixa superior do início, entre publicações, barra lateral, antes do artigo, dentro do artigo e fim do artigo. A posição lateral é compartilhada entre início e artigos.

Cada posição pode ser **Desativado**, **Espaço reservado**, **Google AdSense** ou **Curso / campanha própria**. Campanhas próprias permitem título, descrição, botão, link HTTPS e imagem HTTPS com texto alternativo. As molduras seguem as cores do site e sempre identificam Publicidade. Os criativos servidos pelo Google não são modificados nem apresentados como conteúdo editorial.

Para ativar Google, informe o ID real `ca-pub-` seguido de 16 dígitos e a unidade de 10 dígitos em cada posição. Sem isso, não há anúncio real nem solicitação ao Google. A aprovação do site, configuração da conta e disponibilidade de anúncios dependem do Google. O ID também gera `/ads.txt`. Não são aceitos scripts/HTML colados livremente no painel. As configurações são persistidas no banco e exigem administrador e CSRF.

O Google usa o script oficial assíncrono. Quando anúncios Google estão ativos, apenas as páginas públicas adotam a CSP com nonce e strict-dynamic conforme orientação oficial; o painel mantém sua política restrita. Referência consultada: https://support.google.com/adsense/answer/16283098. A integração não foi verificada com conta ou anúncios reais, pois os identificadores não foram fornecidos. Os testes inspecionam a geração segura do código, sem executar anúncios ou registrar impressões.

`portal.py` concentra composição pública e configuração; `static/portal.css` contém o layout responsivo; `static/garden.svg` é uma ilustração vetorial original, não uma foto de projeto executado. As configurações usam a tabela `settings` existente e não exigem migração de esquema. O sitemap e as canônicas usam `PUBLIC_SITE_URL`, `RENDER_EXTERNAL_URL` ou a origem padrão do projeto. HTML de artigos é escapado; há suporte limitado a títulos, parágrafos, listas, negrito e links Markdown HTTPS.

Verificação inclui fluxo HTTP, exclusividade do dashboard para administradores, persistência/validação de anúncios, CSRF, isolamento entre versão publicada e rascunho, leitura integral e CSP/nonce. A infraestrutura de controle visual do navegador não está disponível neste ambiente; não houve inspeção visual automatizada.
