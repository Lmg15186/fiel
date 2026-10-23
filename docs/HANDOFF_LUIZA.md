# FIEL — pacote final para a Luiza

Atualizado em 23 de outubro de 2026.

## Links definitivos

- Demonstração pública: https://willian-yudy-f.github.io/fiel-live/
- Repositório oficial: https://github.com/Lmg15186/fiel
- Código da hospedagem: https://github.com/Willian-Yudy-F/fiel-live
- Testes do GitHub Actions: https://github.com/Lmg15186/fiel/actions

## Estado da entrega

- Código completo enviado ao repositório oficial.
- Demonstração pública disponível sem login, segredo ou conta Azure.
- 38 testes automatizados passando localmente e no GitHub Actions.
- Microsoft Foundry usado com uma implantação real de `gpt-5-mini`.
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

## Declarações que não devem ser feitas

- Não afirmar que a demonstração pública está hospedada no Azure.
- Não afirmar que o modelo preditivo possui precisão esportiva de produção.
- Não apresentar 49/49 como avaliação subjetiva da qualidade do LLM; são resultados contra ground truth sintético e guardrails.
- Não usar nomes, escudos, jogadores ou vídeos reais de clubes.

## Azure

O Azure continua opcional. Willian possui função de Proprietário no grupo `fiel-rg`, mas o convite B2B do Microsoft Entra ainda não foi resgatado corretamente e o Azure CLI não encontra a assinatura. Isso não bloqueia a submissão, a demonstração ou a reprodução local.

## Arquivos importantes

- `README.md` — apresentação e instruções principais.
- `docs/SUBMISSION.md` — texto pronto para o formulário.
- `docs/VIDEO_SCRIPT.md` — roteiro exato do vídeo.
- `docs/ARCHITECTURE.md` — desenho técnico.
- `docs/EVALUATION.md` — metodologia e resultados.
- `docs/SETUP.md` — execução local.
- `data/demo_agents.json` — execução real do Foundry usada na demo.

## Mensagem pronta para enviar

> Luiza, o FIEL está pronto para a entrega. A demonstração pública é https://willian-yudy-f.github.io/fiel-live/ e o repositório oficial é https://github.com/Lmg15186/fiel. Os 38 testes estão passando e o fluxo real do Microsoft Foundry + Agent Framework está documentado. Deixei em `docs/SUBMISSION.md` os textos prontos para o formulário e em `docs/VIDEO_SCRIPT.md` o roteiro de 1:45 para o vídeo. Agora precisamos apenas escolher o representante, gravar/publicar o vídeo como não listado e preencher o formulário. O Azure ficou como melhoria opcional e não bloqueia a entrega.
