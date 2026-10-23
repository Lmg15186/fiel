# FIEL — pacote final para a Luiza

Atualizado em 23 de outubro de 2026.

## Links definitivos

- Demonstração pública: https://willian-yudy-f.github.io/fiel-live/
- API pública no Azure: https://fiel-api-c3839e.azurewebsites.net/docs
- Health check: https://fiel-api-c3839e.azurewebsites.net/health
- Repositório oficial: https://github.com/Lmg15186/fiel
- Código da hospedagem: https://github.com/Willian-Yudy-F/fiel-live
- Testes do GitHub Actions: https://github.com/Lmg15186/fiel/actions

## Estado da entrega

- Código completo enviado ao repositório oficial.
- Demonstração pública disponível sem login, segredo ou conta Azure.
- 38 testes automatizados passando localmente e no GitHub Actions.
- Microsoft Foundry usado com uma implantação real de `gpt-5-mini`.
- FastAPI hospedada no Azure App Service em plano F1 Free, com sete rotas OpenAPI e seis partidas sintéticas.
- Microsoft Agent Framework 1.23 executando o fluxo Explainer/Verifier → Producer → Personalizer.
- Resultado real do Foundry preservado em `data/demo_agents.json` para a demonstração dos jurados.
- Avaliação em 30 partidas concluída: 49/49 sinais detectados, 49/49 alegações causais inseguras rejeitadas e 49/49 correções seguras aceitas.
- README, arquitetura, avaliação, texto de submissão e roteiro do vídeo atualizados.

## O que falta para enviar

1. Escolher o representante oficial da equipe.
2. Gravar o vídeo de aproximadamente 1 minuto e 45 segundos usando `docs/VIDEO_SCRIPT.md`.
3. Publicar o vídeo como **não listado** no YouTube.
4. Colocar o link do vídeo em `docs/SUBMISSION.md` e no formulário.
5. Copiar para o formulário as respostas da seção **Ready-to-paste form answers** de `docs/SUBMISSION.md`.
6. Conferir nomes dos integrantes e enviar antes do prazo.

## Caminho recomendado para a demonstração

1. Abrir a demo pública.
2. Mover o replay de 59' para 69' e mostrar a mudança de 7% para 71%.
3. Abrir **Agent Desk** e mostrar agentes, baseline histórico e receipt.
4. Abrir **Verification Lab** e mostrar a frase causal rejeitada e a correção aprovada.
5. Abrir **Ground Truth** e mostrar a avaliação das 30 partidas.

## Declarações que podem ser feitas

- O Foundry e o Agent Framework foram realmente usados.
- A demonstração usa o resultado armazenado de uma execução real do Foundry para funcionar sem credenciais.
- Todos os clubes, jogadores, partidas e eventos são fictícios.
- Nenhum dado proprietário da Premier League foi usado.
- O verificador recalcula as métricas em Python e não permite que o modelo avalie a própria resposta.
- A demo pública está no GitHub Pages.
- A API pública e sua documentação OpenAPI estão no Azure App Service.

## Declarações que não devem ser feitas

- Não afirmar que a interface da demonstração está hospedada no Azure: a interface está no GitHub Pages e a API está no Azure App Service.
- Não afirmar que o modelo preditivo possui precisão esportiva de produção.
- Não apresentar 49/49 como avaliação subjetiva da qualidade do LLM; são resultados contra ground truth sintético e guardrails.
- Não usar nomes, escudos, jogadores ou vídeos reais de clubes.

## Azure

O acesso foi confirmado no tenant `dca88b7a-af4d-4f29-abec-d5bf59ce75ef`. O grupo `fiel-rg` contém o recurso Microsoft Foundry `fiel-foundry`, o projeto `fiel`, o deployment `gpt-5-mini`, o App Service Plan F1 `fiel-api-free-plan` e o Web App `fiel-api-c3839e`. O health check público retorna `{"status":"ok","matches":6}`.

## Arquivos importantes

- `README.md` — apresentação e instruções principais.
- `docs/SUBMISSION.md` — texto pronto para o formulário.
- `docs/VIDEO_SCRIPT.md` — roteiro exato do vídeo.
- `docs/ARCHITECTURE.md` — desenho técnico.
- `docs/EVALUATION.md` — metodologia e resultados.
- `docs/SETUP.md` — execução local.
- `data/demo_agents.json` — execução real do Foundry usada na demo.

## Mensagem pronta para enviar

> Luiza, o FIEL está pronto para a entrega. A demonstração pública é https://willian-yudy-f.github.io/fiel-live/, a API no Azure é https://fiel-api-c3839e.azurewebsites.net/docs e o repositório oficial é https://github.com/Lmg15186/fiel. Os 38 testes estão passando, o deployment `gpt-5-mini` foi validado com uma execução real e o fluxo Microsoft Foundry + Agent Framework está documentado. Deixei em `docs/SUBMISSION.md` os textos prontos para o formulário e em `docs/VIDEO_SCRIPT.md` o roteiro de 1:45. Agora precisamos apenas escolher o representante, gravar/publicar o vídeo como não listado e preencher o formulário.
