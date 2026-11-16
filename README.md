# Casa & Verde — central editorial

Implementação inicial executável, Python 3.11+ e SQLite, sem dependências de terceiros.
Interface pt-BR. Posicionamento: decoração acessível e plantas para espaços pequenos.

## Executar

```sh
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

- **IA:** nenhum provedor/modelo externo conectado. Não gera artigos factuais por IA. Pesquisa conectada, checagem remota de evidências, redação por modelo e avaliação semântica ainda precisam de adaptadores, segredos e configuração autorizada. Não há seletor de modelo funcional.
- **Execução:** assistentes locais curtos são síncronos e idempotentes; fila persistente, cancelamento, timeout, retries, limites por execução/período e contabilização por tokens ainda não implementados. O limite em Configurações é registrado para evolução e não aplicado a provedores, pois estes estão desabilitados.
- **Mídia:** briefs/prompts/storyboard são entregues como pendentes. Não gera imagens, áudio nem vídeo, nem faz upload. Ativos obrigatórios pendentes bloqueiam publicação. Aprovação de mídia ainda não tem interface, portanto mantenha-os opcionais neste MVP ou conclua esse módulo antes de exigir mídia.
- **Métricas:** importação manual funcional; sem GSC, GA4, afiliados ou redes conectados. Não calcula receita atribuída ou estimativas automáticas. Recomendações são orientações locais, não análise de IA.
- **Editorial:** sem comentários, notificações, quadro arrastável, comparação visual de versões, consolidação automática, agendamento executável ou arquivamento. Datas planejadas são operacionais; publicar sempre exige ação manual.
- **Portal:** sem adaptador de CMS externo, metadados SEO por artigo, URLs canônicas configuráveis, página de autor própria ou relacionados automáticos. Sitemap usa origem local HTTP; configurar origem e HTTPS antes de hospedar.
- **Segurança/produção:** sem recuperação de senha, MFA, revogação/logout na interface ou proteção persistente/distribuída de login. Escopo inicial de único portal; não é multi-tenant. Backup, TLS, monitoração e servidor de produção são pendentes.
- **Publicação da aplicação:** não hospedada. A habilidade Sites foi consultada; o ambiente não contém os helpers/starter de publicação. A arquitetura local Python não é um Worker Cloudflare e exige implantação compatível ou adaptação.
- Testes automatizados passaram; não foi realizada inspeção visual em navegador.

## Arquitetura

`app.py`: HTTP, HTML escapado, autenticação, autorização e formulários. `domain.py`: invariantes editoriais, ranking, revisão/aprovação/publicação. `agents.py`: módulos especializados locais sem ferramentas externas. `migrations/001_initial.sql`: esquema. `tests/`: verificações essenciais.

Persistência: uma transação SQLite por ação; `BEGIN IMMEDIATE` serializa mutações. Versões são append-only na aplicação. Publicação referencia uma versão imutável e tem unicidade por conteúdo. Uma aprovação antiga continua na auditoria mas nunca autoriza uma nova versão. A revisão mais recente determina elegibilidade. Falha reverte a operação e é registrada separadamente.

Dados externos são tratados como texto e escapados no HTML; não há execução de HTML, comandos, instruções de fontes ou requisições de rede. URLs não são buscadas pelo servidor. Histórico usa UTC ISO; o planejamento é interpretado como horário de São Paulo. Timestamps ISO de histórico são formatados em America/Sao_Paulo na interface; saídas JSON preservam UTC para rastreabilidade.

A evolução recomendada separa transporte do domínio, adiciona migrations incrementais, fila persistente e adaptadores de provedor com schemas JSON e ferramentas restritas. Antes de ativar qualquer provedor: impor orçamento, timeout, retries, cancelamento e idempotência; custos estimados/confirmados devem permanecer distintos. Nenhum agente terá permissão de publicar. Ações externas deverão ficar em adaptadores com destinos autorizados.

## Verificação desta entrega

18 testes automatizados passaram, incluindo fluxo HTTP completo de oportunidade até publicação e métricas, bloqueios, permissões, CSRF, imutabilidade das versões e idempotência. Testes usam bancos temporários; nenhuma publicação de demonstração é criada no banco de operação. Sem QA visual em navegador.

## Render

`render.yaml` define um serviço Python no projeto `casa-verde-editorial`, ambiente `Production`, região Virginia, uma instância no plano `0.5c-512mb` e disco persistente de 1 GB em `/var/data`. Esse plano é pago; revisar o custo no Render antes de aplicar. Não usar SQLite em filesystem efêmero para dados reais. A migração roda no início do processo, quando o disco está montado, nunca no build.

O build executa os testes. `HOST=0.0.0.0` e `PORT` fornecida pelo Render permitem roteamento. `/healthz` verifica acesso ao esquema. Cookies são Secure em HTTPS. SIGTERM encerra a aceitação de requisições; manter apenas uma instância para o SQLite local.

Definir `ADMIN_EMAIL` e `ADMIN_PASSWORD` (12+ caracteres) exclusivamente no Environment do serviço. Só são usados para criar a primeira conta em banco vazio; redeploy não redefine a senha. Depois de criar e testar a conta, remover `ADMIN_PASSWORD` do Environment. Nunca registrar senha em código, terminal ou logs.

O servidor HTTP deste MVP continua sendo o servidor da biblioteca padrão Python, apropriado para validação inicial controlada atrás do proxy TLS do Render. A migração para servidor/framework de produção, limitação persistente de login e backups SQLite consistentes continua necessária antes de operação pública de maior escala. A conexão do repositório não ativa provedores de IA nem remove os limites documentados.
