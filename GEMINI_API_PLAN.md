# google-file-search-setup

## Contexto
Configurar a integração deste projeto com a Gemini API e um Google File Search Store persistente. O código já lê `GOOGLE_API_KEY`, `GOOGLE_FILE_SEARCH_STORE_NAME`, `GOOGLE_GEMINI_MODEL` e `GOOGLE_TIMEOUT_SECONDS` de `backend/.env`; `AgnoGeminiClient.create_model()` conecta o Agno ao store configurado, e `sync_file_search.py` indexa documentos em um store existente. A configuração deve manter a chave somente no backend e não alterar o frontend nem expor segredo no repositório.

## Abordagem
1. Criar ou importar um projeto no Google AI Studio e gerar uma chave Gemini autenticada/restrita em `https://aistudio.google.com/apikey`. Usar uma chave compatível com a política atual do Gemini API; a documentação oficial informa que chaves padrão sem restrições são rejeitadas e que chaves de autorização são o caminho recomendado para novas chaves.
2. Confirmar que a chave tem acesso à Gemini API e quota/billing adequados. Não usar credencial OAuth de Vertex AI nesta configuração: o código atual instancia `agno.models.google.Gemini` com `api_key`, portanto o contrato de configuração é API key do Gemini.
3. Criar um File Search Store persistente uma única vez, executando a partir de `backend` para que `app.core.config.get_settings()` carregue `backend/.env`:
   ```powershell
   Set-Location backend
   @'
   from app.core.config import get_settings
   from google import genai

   settings = get_settings()
   client = genai.Client(api_key=settings.google_api_key)
   store = client.file_search_stores.create(config={
       'display_name': 'cdm-ai-assistant',
       'embedding_model': 'models/gemini-embedding-2',
   })
   print(store.name)
   '@ | ..\.venv\Scripts\python.exe -
   ```
   Capturar apenas o identificador impresso no formato `fileSearchStores/...`; nunca imprimir ou registrar a chave.
4. Preencher `backend/.env` com os valores reais:
   - `GOOGLE_API_KEY=<chave criada no AI Studio>`
   - `GOOGLE_FILE_SEARCH_STORE_NAME=fileSearchStores/<id retornado>`
   - `GOOGLE_GEMINI_MODEL=<modelo Gemini disponível para a chave>`; manter o modelo já configurado se ele estiver disponível, e trocar somente se a chamada retornar erro de modelo inexistente.
   - `GOOGLE_TIMEOUT_SECONDS=90` inicialmente, preservando o valor existente salvo necessidade operacional.
   Manter `backend/.env` fora do Git; não colocar valores Google em `frontend`, código-fonte, screenshots ou comandos commitados.
5. Indexar os documentos desejados no store existente, também a partir de `backend`:
   ```powershell
   ..\.venv\Scripts\python.exe scripts\sync_file_search.py ..\documentos
   ```
   O diretório deve conter somente extensões suportadas pelo script. O comando não cria nem apaga o store; ele recusa documentos com o mesmo `display_name`. Para substituir deliberadamente documentos já indexados, usar:
   ```powershell
   ..\.venv\Scripts\python.exe scripts\sync_file_search.py ..\documentos --replace
   ```
   Aguardar as operações assíncronas terminarem e confirmar as linhas `Indexado: ...` e `Documentos no store: N`.
6. Reiniciar a API pelo `iniciar.bat` para recarregar `backend/.env`. Fazer uma pergunta no chat autenticado que dependa de um documento indexado e confirmar uma resposta com citações em `Fontes consultadas`; uma pergunta sobre conteúdo ausente deve deixar claro que não há contexto recuperado, em vez de inventar conteúdo.
7. Se a chamada falhar, diagnosticar nesta ordem: `GOOGLE_API_KEY` ausente/restrita ou expirada; `GOOGLE_FILE_SEARCH_STORE_NAME` incorreto; documento ainda processando ou extensão rejeitada; modelo indisponível; quota/billing; timeout de rede. Corrigir apenas a variável ou o store correspondente e repetir a sincronização sem `--replace`, exceto quando a intenção for substituir.

## Arquivos críticos e âncoras
- `backend/.env.example` — contrato das variáveis Google que devem existir em `backend/.env`.
- `backend/app/core/config.py`, `Settings` e `get_settings()` — valida presença da chave/store e carrega `.env` relativo ao diretório de execução.
- `backend/app/services/agno_client.py`, `AgnoGeminiClient.create_model()` — passa `api_key`, `file_search_store_names`, modelo e timeout ao Agno/Gemini.
- `backend/scripts/sync_file_search.py`, `sync()` — lista o store, recusa duplicatas, substitui somente com `--replace` e espera operações de upload.
- `README.md`, seção `Google Gemini File Search` — comandos operacionais existentes; executar o script a partir de `backend` para garantir que o `.env` seja encontrado.

## Verificação
- A partir de `backend`, executar `..\.venv\Scripts\python.exe -c "from app.core.config import get_settings; s=get_settings(); print(bool(s.google_api_key), s.google_file_search_store_name.startswith('fileSearchStores/'))"`; saída esperada: `True True`, sem exibir o segredo.
- Indexar uma pasta fixture contendo um arquivo suportado; saída esperada inclui `Indexado: <nome-relativo>` e `Documentos no store: N`.
- Reiniciar a API, autenticar no frontend e enviar uma pergunta relacionada ao fixture; saída esperada é resposta HTTP bem-sucedida renderizada no chat com pelo menos uma fonte/citação do File Search quando o provedor retornar a anotação.
- Repetir a sincronização sem `--replace`; saída esperada é rejeição explícita de duplicatas. Usar `--replace` somente na substituição intencional e confirmar que o documento continua listado.
- Não considerar conexão concluída se apenas a API responder `/health`; a prova necessária é uma consulta Gemini real usando o store configurado.

## Assumptions & contingencies
- O projeto continuará usando Gemini API via Google AI Studio/API key, não Vertex AI/IAM; se a organização exigir Vertex AI, a integração terá de ser redesenhada antes da execução.
- O usuário possui ou obterá acesso de administrador ao projeto Google para criar a chave e o store; sem essa permissão, parar após identificar a permissão faltante e solicitar ao administrador as permissões oficiais de criação de chave/serviço.
- O diretório real de documentos será informado na execução; se ele não existir ou tiver extensões não suportadas, corrigir o caminho/extensões antes de sincronizar, sem alterar o script para aceitar formatos não previstos.
- A criação do store é única; se `GOOGLE_FILE_SEARCH_STORE_NAME` já apontar para um store válido, não criar outro: validar listagem e iniciar diretamente na sincronização.