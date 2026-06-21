# Projeto: Agente de Conteúdo Automático - @djangiota

## Fase 1: Arquitetura Local e Gerenciamento com UV
- [ ] Configurar o projeto utilizando o `uv` para gerenciamento de dependências e ambiente virtual.
- [ ] Criar módulo `config.py` para gerenciar chaves (Google AI Studio e Meta Graph API) via `.env`.
- [ ] Criar banco de dados local simples (JSON ou SQLite) para salvar o status dos posts (Rascunho, Pronto para Imagem, Postado).

## Fase 2: Agente de Geração de Conteúdo (Gemini API)
- [ ] Implementar o script `gerador_conteudo.py` usando o SDK `google-genai` e modelo `gemini-2.5-flash`.
- [ ] Usar Structured Outputs (Pydantic) para garantir o formato correto do JSON sem desperdício de tokens.
- [ ] Criar System Instruction focada em Python, Django, FastAPI, Backend e Dados (com ganchos virais para Instagram).
- [ ] Output estruturado em JSON contendo: Título do post, Texto de cada Card (1 a 5) e Legenda final com hashtags.

## Fase 3: Motor de Design Automatizado (HTML to PNG)
- [ ] Criar script `gerador_design.py` usando Playwright ou Jinja2+WeasyPrint.
- [ ] Desenvolver um template HTML/CSS "Dark Mode" (estilo editor de código/terminal) que recebe o JSON da Fase 2 e cospe as imagens 1080x1080 exatas para o carrossel.

## Fase 4: Integração com a API do Instagram
- [ ] Criar script `publicador_instagram.py` que faz o upload das imagens para um storage temporário (ex: Supabase Storage gratuito) e dispara o fluxo de Carrossel da Meta Graph API.
- [ ] Adicionar validação manual no terminal (`Deseja postar? y/n`) antes do disparo final.