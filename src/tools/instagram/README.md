# 📸 Instagram Post Generator Agent

Este módulo contém o agente automatizado responsável pela criação de posts no formato carrossel para o perfil do Instagram **@brunopythonista**. Ele gera o roteiro dos slides estruturados por meio do Gemini 2.5 Flash e renderiza imagens PNG de alta resolução a partir de um template HTML.

---

## 🛠️ Tecnologias e Recursos

- **IA (Gemini 2.5 Flash)**: Cria conteúdo estruturado com Pydantic (Structured Outputs).
- **Design Dinâmico (Jinja2 & Playwright)**: Utiliza [card_template.html](file:///c:/Users/Ariadne/dev/instagram-posts-generator-agent/src/tools/instagram/templates/card_template.html) no formato 1080x1350px para tirar screenshots em formato headless dos cards do carrossel.
- **Área de Transferência**: Copia a legenda gerada automaticamente para o clipboard.
- **Visualizador Local (`preview.html`)**: Salva uma cópia estática HTML dos slides para visualização no navegador.
- **Abertura automática de pastas**: No Windows, abre o Explorador de Arquivos na pasta do post finalizado automaticamente.

---

## 📋 Escopo do Módulo
Para acompanhar o andamento do projeto e suas fases de desenvolvimento, consulte:
*   [escopo_agente_instagram.md](file:///c:/Users/Ariadne/dev/instagram-posts-generator-agent/src/tools/instagram/escopo_agente_instagram.md)

---

## 🕹️ Guia de Uso (CLI)

O entrypoint central direciona os comandos para esta ferramenta usando o prefixo `instagram`:

### 1. Gerar Novo Post (Conteúdo)
Gera os textos dos cards e legenda técnica, salvando no banco de dados SQLite local em `data/posts.db` com o status `Rascunho`:
```bash
uv run python -m src.cli instagram generate "Como funciona a injeção de dependência no FastAPI"
```

### 2. Listar Histórico de Posts
Mostra todos os posts já gerados salvos no banco local:
```bash
uv run python -m src.cli instagram list
```

### 3. Alterar Status de um Post
Altera manualmente o status de um post no banco de dados (ex: `Postado`):
```bash
uv run python -m src.cli instagram update-status <ID_DO_POST> "Postado"
```
*(Status válidos: `Rascunho`, `Pronto para Imagem` e `Postado`)*

### 4. Renderizar Imagens e Preparar Postagem (Design)
Renderiza as imagens dos slides do carrossel em PNG, gera a legenda em `.txt`, copia a legenda para o clipboard e abre a pasta de saída:
```bash
uv run python -m src.cli instagram design <ID_DO_POST>
```
*Dica: se omitir o ID, ele renderizará o post mais recente.*

As saídas serão geradas em:
`data/generated/instagram/post_<ID_DO_POST>/`

---

## 🗃️ Estrutura do Banco de Dados (SQLite)

Os posts gerados para o Instagram são mantidos na tabela `posts` dentro do banco `data/posts.db`:

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | INTEGER (PK) | Identificador autoincrementado do post. |
| `tema` | TEXT | Tema/Prompt técnico fornecido para geração. |
| `title` | TEXT | Título curto gerado pela IA. |
| `carousel_cards` | TEXT | Lista em formato JSON das strings contendo o texto de cada card. |
| `caption` | TEXT | Legenda gerada com quebras de linha e exatamente 5 hashtags. |
| `status` | TEXT | Status atual do post (`Rascunho`, `Pronto para Imagem`, `Postado`). |
| `created_at` | TIMESTAMP | Data e hora de criação do registro no banco. |
