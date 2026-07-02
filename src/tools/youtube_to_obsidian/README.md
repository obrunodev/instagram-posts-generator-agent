# 🎥 YouTube to Obsidian Transcriber & Summarizer

Este módulo contém a ferramenta responsável por automatizar a transcrição de vídeos do YouTube e o salvamento de notas de estudo estruturadas em Markdown diretamente no seu Vault do Obsidian.

---

## 🛠️ Tecnologias e Recursos

- **Download Otimizado (`yt-dlp`)**: Baixa apenas a trilha sonora compactada em `.m4a` para economizar banda e diminuir o tempo de upload para a API.
- **IA Multimodal (Gemini 2.5 Flash)**: Faz o upload do áudio usando a API de arquivos do Gemini e gera a transcrição técnica precisa juntamente com um resumo estruturado.
- **Integração Obsidian**: Adiciona metadados Frontmatter YAML (data, URL original e tags) e grava a nota final no diretório configurado.
- **Cleanup Automático**: Deleta arquivos de áudio temporários salvos localmente após a conclusão bem-sucedida do processo.

---

## 📋 Escopo do Módulo
Para acompanhar o andamento do projeto e suas fases de desenvolvimento, consulte:
*   [escopo_youtube_to_obsidian.md](file:///c:/Users/Ariadne/dev/instagram-posts-generator-agent/src/tools/youtube_to_obsidian/escopo_youtube_to_obsidian.md)

---

## ⚙️ Configuração Requerida

Esta ferramenta requer que a variável `OBSIDIAN_VAULT_PATH` esteja definida no seu arquivo `.env` apontando para o diretório local do seu cofre do Obsidian:
```env
OBSIDIAN_VAULT_PATH=C:/Users/seu_usuario/Documents/Obsidian/SeuVault
```

---

## 🕹️ Guia de Uso (CLI)

O entrypoint central direciona os comandos para esta ferramenta usando o prefixo `youtube`:

### Processar Vídeo do YouTube
Baixa o áudio, transcreve com IA, cria o resumo didático em Markdown com Frontmatter e salva no Obsidian Vault configurado:
```bash
uv run python -m src.cli youtube process --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

A nota gerada conterá o título limpo de caracteres inválidos e a seguinte estrutura estipulada nas System Instructions do Gemini:
1.  **Frontmatter YAML** (título, data, URL e tags).
2.  **# Título Principal**.
3.  **## Conceitos Chave** (bullet points com definições).
4.  **## Explicação Detalhada** (resumo explicativo das seções).
5.  **## Código e Exemplos Práticos** (caso existam códigos ou tutoriais técnicos explicados no vídeo).
