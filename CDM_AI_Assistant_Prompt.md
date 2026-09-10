# PROMPT: CDM AI Assistant (FastAPI + React Vite + n8n RAG + Executável)

Você atuará como Engenheiro de Software Full Stack Sênior. Sua tarefa é implementar uma aplicação completa composta por um **Backend FastAPI**, um **Frontend React (Vite)** e um script de empacotamento em **executável único (PyInstaller)**, integrada a um workflow de RAG no **n8n** e com persistência em banco **PostgreSQL**.

---

## 1. Stack Tecnológica e Arquitetura

- **Backend:** Python 3.11+ com FastAPI, Uvicorn, SQLAlchemy / SQLModel e Alembic/migrations.
- **Frontend:** React 18+ com Vite, TypeScript, Tailwind CSS, Lucide React (ícones), Axios e React-Markdown.
- **Banco de Dados:** PostgreSQL (hospedado na VPS, configurável via connection string).
- **IA / RAG Engine:** Webhook HTTP do n8n (recebe payload contendo texto, session ID e imagem opcional em Base64).
- **Distribuição Desktop:** O backend compila e serve estaticamente os assets do frontend (`/dist`) em modo produção. Um arquivo `launcher.py` orquestra a inicialização do servidor Uvicorn em porta livre e abre o navegador padrão automaticamente (`webbrowser.open`). O PyInstaller empacota o executável único.

---

## 2. Design System & Ergonomia (CDM Brand + ChatGPT Layout)

Harmonize a ergonomia e layout do ChatGPT com os tokens de identidade visual da CDM:

### 2.1 Tokens CDM
Configure o Tailwind CSS com a seguinte paleta institucional:
- `brand-wine`: `#71211A` (Destaque institucional, active tabs e criticidade)
- `brand-wine-soft`: `#9C3D3B`
- `brand-navy`: `#1A2C52` (Background da sidebar institucional)
- `brand-blue`: `#1A4E85` (Botões de envio, links, estados de foco e CTAs principais)
- `brand-gold`: `#EBAA35` (Avisos de limites, tags e badges de atenção)
- `brand-charcoal`: `#1D1D1B` (Texto primário em fundos claros)
- `text-secondary`: `#526071` (Metadados e timestamps)
- `surface`: `#FFFFFF` (Cards, balões de mensagem e painéis)
- `canvas`: `#F4F6F9` (Fundo geral da área de conversa)
- `border`: `#DDE3EC` (Linhas divisórias e hairlines)

### 2.2 Tipografia e Formatos
- Fonte única: **Outfit** (`@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;650&display=swap');`).
- Números contábeis/fiscais com `tabular-nums`.
- Raio de borda: 10px para botões/inputs, 14px para containers e cards principais.

### 2.3 Estrutura Visual
- **Sidebar (260px - 280px):**
  - Fundo em `brand-navy` ou tonalidade neutra com cabeçalho institucional CDM.
  - Botão "+ Nova Consulta" no topo.
  - Lista de conversas agrupadas (Hoje, Ontem, Dias Anteriores) com opções de renomear e excluir.
  - Rodapé com card de autenticação: se logado, mostra nome/email e botão de Logout; se anônimo, exibe botão pill "Entrar / Login".
- **Área Central de Mensagens:**
  - Largura de leitura confortável (~768px centralizado).
  - Balões de mensagem diferenciados (Usuário vs Assistente CDM).
  - Suporte completo a Markdown, tabelas fiscais bem estruturadas e blocos de código com cópia.
- **Barra de Entrada Inferior (Input Bar):**
  - Fixa na parte inferior com cantos arredondados (14px) e borda sutil.
  - Botão de clipe de papel para upload de imagem (com preview em miniatura removível acima do input antes do disparo).
  - Textarea auto-expansível (1 a 6 linhas) com envio via `Enter` e quebra com `Shift+Enter`.
  - Botão de envio em `brand-blue` com spinner de carregamento durante a resposta do n8n.

---

## 3. Modo Anônimo vs. Modo Autenticado

A aplicação deve oferecer funcionamento híbrido e transparente:
1. **Modo Anônimo (Guest):**
   - O usuário pode abrir o app e começar a conversar imediatamente sem credenciais.
   - O chat envia requisições para o n8n usando um `session_id` temporário (UUID gerado no frontend).
   - Nenhuma conversa, pergunta ou resposta é persistida no PostgreSQL.
   - Os dados residem exclusivamente no estado da sessão do navegador (`sessionStorage` ou memória). Ao fechar a aba/aplicação, o histórico é descartado.
2. **Modo Autenticado:**
   - Autenticação via email/senha utilizando tokens JWT armazenados com segurança.
   - Todas as sessões de chat e mensagens são persistidas no PostgreSQL remoto.
   - O usuário tem acesso ao histórico completo na barra lateral em qualquer inicialização.

---

## 4. Banco de Dados PostgreSQL (Esquema Relacional)

Defina os modelos via SQLAlchemy / SQLModel:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'Nova Consulta',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user' ou 'assistant'
    content TEXT NOT NULL,
    has_image BOOLEAN DEFAULT FALSE,
    image_metadata JSONB DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chats_user ON chats(user_id);
CREATE INDEX idx_messages_chat ON messages(chat_id);
```

---

## 5. Integração com o n8n (RAG Pipeline)

- O frontend envia a requisição para o backend FastAPI (`POST /api/chat/query`).
- O FastAPI atua como proxy seguro e repassa a requisição para a URL do Webhook do n8n (`N8N_WEBHOOK_URL`).
- **Payload enviado ao n8n:**
  ```json
  {
    "sessionId": "uuid-da-conversa",
    "chatInput": "Dúvida do usuário",
    "image": "data:image/png;base64,... (ou null)",
    "user": {
      "isAuthenticated": true,
      "userId": "uuid-do-usuario"
    }
  }
  ```
- O FastAPI aguarda a resposta do n8n (ex: `{ "output": "Resposta da IA..." }`), persiste no PostgreSQL (caso logado) e retorna o resultado ao frontend.

---

## 6. Launcher Desktop & Empacotamento

1. **`launcher.py`:**
   - Localiza uma porta livre (ex: entre 8000 e 8090).
   - Inicia o Uvicorn em uma thread em background montando o build estático do React (`app.mount("/", StaticFiles(directory="dist", html=True))`).
   - Executa `webbrowser.open(f"http://127.0.0.1:{port}")`.
   - Trata encerramento gracioso via interrupção de processos.
2. **Build Script (`build.sh` / `build.bat`):**
   - Passo 1: Entra na pasta `/frontend`, roda `npm install` e `npm run build`.
   - Passo 2: Copia a pasta `dist` resultante para o backend.
   - Passo 3: Executa PyInstaller apontando para `launcher.py` incluindo os templates/estáticos (`--add-data "dist:dist"`).

---

## 7. Estrutura do Projeto Requerida

Gere o código organizando a estrutura a seguir:

```text
├── backend/
│   ├── app/
│   │   ├── api/             # Rotas de auth, chats, messages e proxy n8n
│   │   ├── core/            # Config, segurança (JWT, hash), database session
│   │   ├── models/          # Modelos SQLModel / SQLAlchemy
│   │   └── services/        # Cliente HTTP para webhook do n8n
│   ├── main.py              # Aplicação FastAPI com montagem dos estáticos
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # Sidebar, ChatArea, InputBox, ImageUploader, AuthModal
│   │   ├── contexts/        # AuthContext, ChatContext (com fallback anônimo)
│   │   ├── services/        # API client (Axios)
│   │   ├── styles/          # Tailwind com os tokens CDM
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── launcher.py              # Script inicializador com webbrowser.open
├── build_executable.py      # Script de automação do PyInstaller
└── README.md                # Instruções de configuração do .env, build e execução
```

---

## 8. Critérios de Aceite

1. O projeto deve inicializar localmente em desenvolvimento com `npm run dev` no frontend e `uvicorn main:app --reload` no backend.
2. O envio de imagens deve suportar PNG/JPEG, com compressão/validação antes do envio e exibição em miniatura no chat.
3. Se deslogado, as interações acontecem fluidamente com o n8n sem gravar linhas no PostgreSQL.
4. Ao autenticar, o usuário visualiza o histórico persistido, pode criar novas conversas e retomar chats antigos.
5. O executável gerado deve abrir o navegador padrão no carregamento sem travar a interface.
