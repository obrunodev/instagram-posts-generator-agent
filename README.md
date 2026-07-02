# 🤖 Agente Brunopythonista - Repositório Multi-Ferramentas de Automação e IA

Este repositório contém uma suite unificada de ferramentas de automação e agentes baseados em Inteligência Artificial para otimizar processos de criação de conteúdo e estudos do perfil **@brunopythonista**. O projeto é desenvolvido em **Python** e utiliza a API do **Gemini 2.5 Flash** (via SDK oficial `google-genai`).

---

## 📂 Estrutura Geral do Projeto

O repositório é organizado de forma modular para que novas ferramentas e integradores possam ser adicionados facilmente:

```text
instagram-posts-generator-agent/
├── pyproject.toml                     # Dependências do projeto e scripts CLI
├── README.md                          # Visão geral do repositório (este arquivo)
├── .env                               # Configurações confidenciais locais
│
├── src/                               # Código-fonte principal
│   ├── cli.py                         # Ponto de entrada (CLI central)
│   ├── core/                          # Recursos e configurações compartilhados
│   └── tools/                         # Ferramentas independentes (Módulos)
│       ├── instagram/                 # Agente do Instagram (Posts e Imagens)
│       └── youtube_to_obsidian/       # Transcritor e Resumos do YouTube para o Obsidian
│
└── data/                              # Banco de dados e mídias geradas localmente
    ├── posts.db                       # Banco SQLite unificado
    └── generated/                     # Mídias e artefatos de saída
```

---

## 🗺️ Ferramentas e Documentações Específicas

Para entender os detalhes de funcionamento, fluxos de escopo e comandos CLI de cada ferramenta, consulte suas respectivas documentações:

### 📸 1. Instagram Post Generator
Agente de geração de posts carrosséis técnicos (Python, Django, FastAPI) com motor de captura de imagens em terminal dark mode usando Playwright.
*   👉 **[Documentação do Módulo Instagram](file:///c:/Users/Ariadne/dev/instagram-posts-generator-agent/src/tools/instagram/README.md)**
*   📋 **[Escopo do Módulo Instagram](file:///c:/Users/Ariadne/dev/instagram-posts-generator-agent/src/tools/instagram/escopo_agente_instagram.md)**

### 🎥 2. YouTube to Obsidian Transcriber
Transcritor de vídeos e gerador de notas e resumos didáticos estruturados em Markdown integrado diretamente ao seu vault de estudos local.
*   👉 **[Documentação do Módulo YouTube/Obsidian](file:///c:/Users/Ariadne/dev/instagram-posts-generator-agent/src/tools/youtube_to_obsidian/README.md)**
*   📋 **[Escopo do Módulo YouTube/Obsidian](file:///c:/Users/Ariadne/dev/instagram-posts-generator-agent/src/tools/youtube_to_obsidian/escopo_youtube_to_obsidian.md)**

---

## 🚀 Instalação e Setup Global

### 1. Instalar Gerenciador `uv`
Certifique-se de ter o gerenciador de pacotes `uv` instalado em sua máquina:
```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. Configurar o Ambiente Virtual e Dependências
Execute a sincronização do ambiente virtual a partir da raiz do projeto:
```bash
uv sync
```

### 3. Instalar Dependências Externas (Browser Playwright)
Instale o browser Chromium headless para habilitar o gerador de imagens do Instagram:
```bash
uv run playwright install chromium
```

### 4. Configurar Variáveis no `.env`
Crie ou edite o arquivo `.env` na raiz do projeto contendo as seguintes configurações:
```env
# Chave de API do Google AI Studio (Gemini)
GEMINI_API_KEY=sua_chave_de_api_aqui

# Caminho absoluto da pasta do seu Vault do Obsidian (necessário apenas para a ferramenta youtube)
OBSIDIAN_VAULT_PATH=C:/Users/seu_usuario/Documents/Obsidian/SeuVault
```

---

## 🕹️ Roteamento de Comandos CLI

A partir de agora, todas as ferramentas podem ser chamadas a partir da CLI unificada usando o formato `uv run python -m src.cli [ferramenta] [ação]`:

```bash
# Instagram: Gerar Conteúdo
uv run python -m src.cli instagram generate "Tema do Post"

# Instagram: Renderizar Design dos Slides
uv run python -m src.cli instagram design [ID_DO_POST]

# YouTube/Obsidian: Transcrever e Resumir Vídeo
uv run python -m src.cli youtube process --url "URL_DO_VIDEO"
```
