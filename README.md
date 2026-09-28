# CDM AI Assistant

Aplicação full stack de chat para o CDM, com frontend React/Vite, API FastAPI, persistência PostgreSQL e respostas Gemini com Google File Search.

## Pré-requisitos

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Google AI Studio com uma chave `GOOGLE_API_KEY` e um File Search Store persistente

## Configuração

1. Crie um banco PostgreSQL.
2. Copie `backend/.env.example` para `backend/.env` e preencha `JWT_SECRET_KEY`, `GOOGLE_API_KEY`, `GOOGLE_FILE_SEARCH_STORE_NAME`, `SSH_PASSWORD` e `DB_PASSWORD`. Com `SSH_ENABLE=true`, a aplicação abre o túnel SSH e usa o PostgreSQL remoto em `DB_HOST`/`DB_PORT`; mantenha `DATABASE_URL` vazio.
3. Crie o ambiente Python e instale as dependências:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

4. Aplique a migration antes de iniciar o modo persistente:

```powershell
cd backend
alembic upgrade head
```

## Usuário administrador e colaboradores

O cadastro público está desativado. Após aplicar as migrations, execute o seed idempotente com `ADMIN_PASSWORD` definido no ambiente:

```powershell
$env:ADMIN_PASSWORD='defina-uma-senha-forte'
python backend\scripts\seed_admin.py
```

O administrador entra pelo mesmo login, acessa o chat e também o painel de administração. Colaboradores são criados pelo painel, podem ser ativados ou desativados, ter a senha trocada e ser colocados em blacklist. Contabilização de tokens ainda não faz parte do modelo.

Para executar a versão empacotada, execute `iniciar.bat`. O batch abre `dist\cdm-ai-assistant.exe`; use `iniciar.bat --dev` somente para iniciar o ambiente de desenvolvimento com Vite e Uvicorn.

## Desenvolvimento

Em um terminal:

```powershell
cd backend
uvicorn main:app --reload
```

Em outro terminal:

```powershell
npm install --prefix frontend
npm run dev --prefix frontend
```

Acesse `http://localhost:5173`. O Vite encaminha `/api` para `http://127.0.0.1:8000`.

## Google Gemini File Search

A API consulta o `GOOGLE_FILE_SEARCH_STORE_NAME` compartilhado usando Gemini e Agno. O store permanece na Google até exclusão manual; os arquivos brutos temporários da Files API expiram, mas o conteúdo indexado do store permanece.
O `GOOGLE_API_KEY` configurado deve ter acesso aos Stores cadastrados. Um Store criado com outra chave ou em outro projeto retorna `403 PERMISSION_DENIED`; nesse caso, configure a chave proprietária ou recrie o Store e atualize `GOOGLE_FILE_SEARCH_STORE_NAME`/o cadastro da base.


Para indexar ou substituir documentos explicitamente:

```powershell
python backend\scripts\sync_file_search.py <pasta>
python backend\scripts\sync_file_search.py <pasta> --replace
```

O script rejeita extensões desconhecidas, não cria nem apaga o store, recusa duplicados sem `--replace` e registra metadados de nome relativo, extensão e tamanho.

## Testes e build

```powershell
pytest backend\tests -q
npm install --prefix frontend
npm run build --prefix frontend
python build_executable.py
```

O build copia `frontend/dist` para `dist` e gera `dist` de assets junto do executável `dist`/`cdm-ai-assistant.exe` conforme o PyInstaller. O executável usa o `.env` acessível ao processo e não embute segredos. Ele escolhe uma porta livre entre 8000 e 8090, aguarda `/health` e então abre o navegador.

## Segurança

- Access token JWT permanece apenas em memória no navegador.
- Refresh token JWT fica em cookie HttpOnly `cdm_refresh_token`, SameSite Lax e Secure configurável.
- Visitantes usam apenas `sessionStorage`; o histórico guest nunca é copiado para o banco.
- Imagens são validadas como PNG/JPEG, limitadas a `IMAGE_MAX_BYTES` e, em conversas autenticadas, os bytes são persistidos no banco junto dos metadados. Visitantes usam somente `sessionStorage`, sem persistir bytes de imagem.
- Em produção, use HTTPS, `COOKIE_SECURE=true`, segredo JWT aleatório e origens CORS explícitas.
