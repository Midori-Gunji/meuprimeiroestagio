# Buscador de estágios

1. Envie todos os arquivos deste repositório (incluindo a pasta `.github`).
2. Settings > Pages > Deploy from a branch > `main` / root.
3. Settings > Actions > General > Workflow permissions > Read and write permissions.
4. Actions > "Coletar vagas" > Run workflow (a primeira coleta cria o `vagas.json`; depois roda todo dia).
5. Alertas: o robô abre uma issue quando há vagas novas. Ative as notificações do repositório (Watch > All activity) para receber por e-mail.
6. Mais fontes (opcional): crie uma conta gratuita em developer.adzuna.com e salve `ADZUNA_APP_ID` e `ADZUNA_APP_KEY` em Settings > Secrets and variables > Actions.

Para mudar o que é coletado e alertado, edite `config.json`.
