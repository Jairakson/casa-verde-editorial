# Conector Windows — Casa & Verde + ChatGPT Plus

Este conector é executado **no seu computador**, usando o login oficial e a autorização de uso do plano ChatGPT. Os tokens do ChatGPT não são enviados ao Render. Não usa `OPENAI_API_KEY` e não alterna para cobrança de API quando há erro ou limite.

A conexão só estará ativa depois que você fizer o pareamento e autorizar a conta no navegador. A disponibilidade depende da conta, permissões, modelos e limites retornados pela OpenAI. A autorização real não pode ser feita por outra pessoa nesta conversa.

## 1. Instalar no Windows

1. Instale **Python 3.11 ou superior** pelo site oficial: https://www.python.org/downloads/windows/. Se houver a opção, marque **Add Python to PATH**.
2. Baixe o projeto em https://github.com/Jairakson/casa-verde-editorial/archive/refs/heads/main.zip.
3. No Explorador de Arquivos, clique com o botão direito no ZIP e selecione **Extrair Tudo**. Não execute de dentro do ZIP.
4. Abra a pasta extraída `casa-verde-editorial-main`.
5. Dê dois cliques em **Iniciar-Conector.bat**. Na primeira abertura, ele prepara um ambiente Python e instala as dependências do conector. Mantenha a janela aberta.

Não precisa instalar PostgreSQL, Docker ou o servidor da aplicação no computador. O banco e o painel continuam no Render.

## 2. Parear o computador com o painel

1. Na janela do conector, digite **1** e pressione Enter.
2. A janela mostrará um **código de oito caracteres** e abrirá o painel no navegador.
3. Entre no painel Casa & Verde como administrador. Se o login abrir a página inicial, clique em **Conector ChatGPT Plus** no menu lateral.
4. Compare o código do navegador com o código da janela do computador.
5. No painel, clique em **Autorizar este computador**. O código expira em dez minutos e só pode ser usado uma vez.
6. Volte à janela do conector e aguarde a mensagem **Computador conectado ao painel**.

O pareamento não exige copiar a senha do painel para o conector. Autorize apenas um código iniciado por você. O computador autorizado pode buscar as pautas na fila e devolver resultados; não pode aprovar nem publicar.

## 3. Entrar no ChatGPT Plus

1. Na janela do conector, digite **2**.
2. Na primeira vez, escolha **0 — Usar outra conta / registrar o conector**.
3. O navegador abrirá o domínio oficial `auth.openai.com`.
4. Entre na sua conta ChatGPT Plus.
5. Confira o aplicativo **Casa & Verde Connector** e a permissão para usar seu plano. Autorize apenas se concordar.
6. O navegador retornará para um endereço `http://127.0.0.1:.../auth/callback`. Isso é esperado: é a comunicação com o conector no próprio computador.
7. Volte à janela e confira a mensagem de conta autorizada. Se o navegador disser apenas “Autorização recebida”, aguarde a validação na janela antes de considerar o login concluído.

A autorização permite uso dos recursos elegíveis do plano, não acesso às suas conversas ou memórias. O programa não solicita sua senha do ChatGPT no terminal. Não copie cookies, tokens, chaves ou arquivos de credenciais para chats ou para o Render.

## 4. Escolher modelo e iniciar

1. Digite **3** para consultar os modelos disponíveis na sua conta.
2. Escolha o número do modelo desejado. A lista é consultada na OpenAI; nenhum modelo é presumido como disponível.
3. Digite **4** para iniciar o processamento.
4. Mantenha a janela aberta, o computador ligado, conectado à internet e sem suspensão.

## 5. Enviar uma tarefa

1. No painel, abra **Central editorial** e selecione um conteúdo.
2. Para redação, salve/aprove primeiro um brief. Para vídeo, é necessária uma versão de texto aprovada.
3. Em **ChatGPT Plus no seu computador**, escolha pesquisa, estratégia, redação, imagens, vídeo, revisão ou desempenho.
4. Clique em **Enviar tarefa ao conector**.
5. Acompanhe na janela do Windows e em **Agentes e execuções**. Atualize a página para ver mudanças.
6. Uma redação concluída é salva como **nova versão**, com revisão humana obrigatória. As outras entregas aparecem no histórico estruturado de execuções.
7. O agente revisor gera um parecer e problemas; esse resultado não substitui a conferência humana das fontes, nem aprova ou publica automaticamente.

As sete especialidades usam o modelo textual selecionado. Pesquisa organiza dados e fontes já fornecidos; não navega na web nesta versão. Imagens produzem briefs/prompts pendentes; vídeo produz roteiro/storyboard pendentes. Não gera arquivos de imagem, áudio ou vídeo. O suporte da assinatura via este fluxo não inclui automaticamente todas as ferramentas do ChatGPT.

## Uso, limites e custos

O uso compartilha os limites do seu Plus; cada agente não ganha uma franquia separada. Modelos, acesso e limites podem variar. Consulte https://chatgpt.com/settings/usage e revise os limites do aplicativo. O conector não habilita compras de créditos nem troca para uma chave de API. Se o plano ou a autorização estiverem indisponíveis, a execução para com uma mensagem.

O painel registra origem `chatgpt-plus-local`, modelo, versão de instruções e tokens quando fornecidos. Não inventa preço por execução; custo monetário fica indisponível, com indicação `assinatura_plus`. O custo da assinatura não é dividido artificialmente entre os artigos.

## Parar, cancelar e reconectar

- **Parar:** pressione Ctrl+C na janela. O menu continua disponível. Para sair, digite 0. O fechamento da janela impede novas tarefas.
- **Cancelar uma tarefa:** em Agentes e execuções, informe o ID em Controlar tarefa e escolha Cancelar. O conector verifica cancelamentos durante o stream. Uma geração já iniciada pode consumir uso antes da interrupção.
- **Falha/interrupção:** não há repetição automática da chamada ao modelo depois de uma falha conhecida. Confira o erro e escolha Repetir no painel. Uma concessão perdida pode ser retomada até duas vezes após expirar; a entrega permanece idempotente.
- **Envio interrompido após gerar:** o resultado fica protegido na caixa de saída local e é reenviado no próximo início do processamento, sem chamar o modelo de novo. Se a tarefa expirou, foi cancelada ou o conteúdo mudou, não é aplicado. Use a opção 7 do menu para consultar o último resultado preservado.
- **Conta expirada:** escolha 2 e selecione o registro da conta existente. Isso reutiliza o registro e o identificador do computador.
- **Trocar conta:** escolha 2 e outra conta registrada, ou 0 para adicionar uma. Escolha o modelo novamente.
- **Desconectar ChatGPT:** escolha 5. O programa tenta revogar a sessão e remove os tokens locais. Se a revogação falhar por problema de rede, desconecte também o aplicativo nas configurações do ChatGPT.
- **Revogar o computador:** no painel, abra Conector ChatGPT Plus, informe o ID do dispositivo e clique em Revogar acesso. Isso bloqueia o acesso ao painel; não revoga por si só a autorização na OpenAI.

## Onde ficam as credenciais

No Windows, `%LOCALAPPDATA%\CasaVerdeConnector\credentials.bin` é criptografado com **Windows DPAPI**, vinculado ao usuário do Windows. O arquivo inclui separadamente a autorização do painel e os registros ChatGPT, sem enviá-los um ao outro. Ele não faz parte do projeto, não deve ser compartilhado e não deve ser copiado para o GitHub.

Em macOS/Linux, o mesmo módulo usa diretório local protegido e arquivo com permissões 0600. Não inclui integração com Keychain/keyring desses sistemas. Esta entrega foi preparada para Windows; os testes automatizados foram executados em Linux. A execução real do iniciador e do DPAPI ainda precisa ser confirmada no seu Windows.

## Se algo não funcionar

- **Janela fecha ou Python não encontrado:** instale Python 3.11+ e reabra o iniciador após a instalação. Use a pasta extraída, não o ZIP.
- **Código expirado:** escolha 1 para gerar um novo. Não tente reaproveitar um código antigo.
- **Pareamento fica aguardando:** verifique se entrou no painel como administrador e clicou em Autorizar. O serviço gratuito do Render pode demorar ao sair de suspensão.
- **Permissão do plano recusada:** a conta pode não estar elegível para esse fluxo ou a autorização pode ter sido recusada. O conector não contorna essa limitação; registre apenas a mensagem mostrada, sem credenciais.
- **Limite de uso:** confira Configurações → Uso no ChatGPT e aguarde o prazo informado ali. Reconectar não restaura franquia.
- **Tarefa ficou na fila:** verifique a opção 4, conexão à internet e suspensão do Windows.
- **Conteúdo mudou durante a execução:** o painel rejeita a aplicação do resultado antigo. Envie uma nova tarefa para a versão atual.

## Referências oficiais utilizadas

- Fluxo de login/PKCE/OIDC: https://developers.openai.com/siwc/token-sharing-open-source/sign-in
- Modelos e inferência: https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference
- Credenciais e renovação: https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions
- Limitações de ferramentas: https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations

O fluxo usa endpoints públicos oficiais, `store: false` e `stream: true`, com confirmação de `response.completed`. Não usa endpoints privados do ChatGPT, automação de login por senha ou sessão extraída de navegador. Os testes de autenticação e inferência usam respostas controladas; nenhuma conta Plus real foi autorizada por esta sessão de desenvolvimento.
