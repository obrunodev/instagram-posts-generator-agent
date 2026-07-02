# Projeto: Transcritor de Vídeos e Integrador Obsidian (Youtube to Obsidian)

## Fase 1: Setup e Captura de Mídia (Local)
- [x] Adicionar dependências necessárias no projeto usando `uv add yt-dlp`.
- [x] Configurar a variável `OBSIDIAN_VAULT_PATH` no arquivo `.env` apontando para o diretório local do Vault.
- [x] Criar o script `downloader.py` usando `yt-dlp` para baixar apenas o áudio do vídeo do YouTube no formato compactado (ex: `.mp3` ou `.m4a`), minimizando o tamanho do upload para a API.

## Fase 2: Transcrição e Resumo Multimodal (Gemini API)
- [x] Implementar o script `processador_audio.py` usando o SDK `google-genai`.
- [x] Utilizar a API de Files do Gemini (`client.files.upload`) para enviar o áudio diretamente ao modelo `gemini-2.5-flash`.
- [x] Configurar System Instruction especializada para:
    - Transcrever o conteúdo técnico com precisão (identificando termos de Python, Django, Cloud, etc).
    - Gerar um resumo altamente didático estruturado com: # Título, ## Conceitos Chave, ## Explicação Detalhada e ## Código/Exemplos Práticos (se houver).
- [x] Garantir que o output do Gemini retorne uma string contendo o Markdown puríssimo.

## Fase 3: Organização de Arquivos e Integração Obsidian
- [x] Criar o script `gerenciador_obsidian.py`.
- [x] Implementar uma função que recebe o título do vídeo (limpo de caracteres especiais) e o conteúdo em Markdown.
- [x] Adicionar metadados automáticos no topo do arquivo (Frontmatter/YAML) contendo:
    - Data de criação.
    - URL original do YouTube.
    - Tags automáticas (ex: `#estudos #python #resumo-youtube`).
- [x] Escrever o arquivo `.md` final diretamente dentro do path configurado do Vault do Obsidian.

## Fase 4: CLI de Automação (Interface do Usuário)
- [x] Criar o script principal de execução `estudar_video.py`.
- [x] Implementar interface CLI simples (via `argparse` ou `click`) que aceita o parâmetro `--url`.
- [x] Adicionar limpeza automática (cleanup) para deletar o arquivo de áudio local após o processamento completo para não entulhar o disco da máquina.
