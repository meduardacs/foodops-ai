# FoodOps AI

**Copiloto de operações para restaurantes** · React + FastAPI + SQL + RAG + Machine Learning

FoodOps AI é um projeto full-stack demonstrativo para transformar o histórico de pedidos de um restaurante em informações úteis para a operação. A interface reúne indicadores de vendas, um assistente conversacional com ferramentas, previsões por produto, documentos consultáveis e métricas de avaliação.

Ele não depende de APIs privadas do iFood, não contém dados de clientes reais e **funciona sem chave de IA paga**: o modo local usa regras de roteamento, consultas SQL e respostas compostas a partir dos resultados. Com uma chave OpenAI, habilita-se também um agente LLM com *tool calling*. A interface é a mesma nos dois casos.

## O que já está implementado

| Área | O que faz | Origem dos dados |
|---|---|---|
| Visão geral | Faturamento, pedidos, ticket médio, crescimento, série temporal, categorias e ranking | Agregações SQL dos pedidos demonstrativos |
| Copiloto | Responde perguntas sobre vendas, itens mais pedidos, previsão, procedimentos e pedidos recentes | Ferramentas SQL, modelo ML e documentos |
| Previsões | Estima unidades por produto para amanhã e para os próximos sete dias | Random Forest por produto, com histórico diário e variáveis temporais |
| Documentos | Pesquisa e exibe trechos com fonte; aceita upload de PDF com texto, TXT e MD | TF-IDF offline; pgvector opcional |
| Avaliação | Compara modelo com baseline; 50 perguntas de avaliação do roteador | Métricas calculadas e script reproduzível |
| API | Endpoints FastAPI com documentação Swagger | PostgreSQL ou SQLite |

## Executar no Windows (VS Code + Git Bash)

**Atalho Windows:** você também pode abrir `iniciar-backend.bat` e `iniciar-frontend.bat` (duas janelas), sem digitar os comandos. Instruções completas em `docs/INICIAR_WINDOWS.md`.

Pré-requisitos: **Python 3.11, 3.12 ou 3.13**, **Node.js 20.19+ ou 22+** e Git Bash. Não é necessário Docker para o modo local.

**1. Extraia o ZIP** e abra a pasta `foodops-ai` no VS Code (`File > Open Folder`). No terminal do VS Code, selecione Git Bash.

**2. Inicie o backend (terminal 1):**

```bash
cd backend
py -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Se `py` não funcionar, use `python -m venv .venv` no lugar. Execute os comandos **dentro da pasta `backend`**. Na primeira inicialização, a API cria `foodops.db` e popula automaticamente vendas e documentos sintéticos.

Teste no navegador: <http://localhost:8000/docs> ou <http://localhost:8000/api/health>.

**3. Inicie o frontend (terminal 2):**

```bash
cd frontend
npm install
npm run dev
```

Abra **<http://localhost:5173>**. A aplicação está pronta para navegar e conversar com os dados no modo local, sem configurar OpenAI.

**Importante:** os terminais devem estar nas respectivas pastas `backend` e `frontend`. Se executar `npm install` na raiz, o `package.json` não será encontrado. Se executar `pip install -r requirements.txt` na raiz, também não: o arquivo está em `backend/requirements.txt`.

### Executar com Docker (PostgreSQL + pgvector)

Instale Docker Desktop com Docker Compose. Na raiz do projeto:

```bash
cp .env.example .env
# Edite .env se quiser alterar a senha local ou habilitar OpenAI.
docker compose up --build
```

- App: **http://localhost:3000**
- Swagger: **http://localhost:8000/docs**
- Banco: PostgreSQL 16 com extensão pgvector disponível na imagem; sem necessidade de embeddings para o funcionamento padrão.

Para encerrar: `Ctrl+C` e `docker compose down`. O volume `postgres_data` mantém os registros entre reinicializações. `docker compose down -v` também **apaga o volume**: use somente se desejar reiniciar os dados.

> Docker não é requisito para executar o modo local. Com Docker, o frontend é servido pelo Nginx e encaminha `/api` para o FastAPI.

### Configurar a OpenAI (opcional)

Para desenvolvimento local, copie `backend/.env.example` para `backend/.env` e preencha:

```dotenv
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
RAG_EMBEDDINGS=tfidf
```

Se a chave estiver ausente, o copiloto usa regras locais, mas as **consultas SQL, busca documental, previsões e testes seguem funcionando**. Com chave, o agente pode selecionar ferramentas por chamada de funções. O endpoint aceita `mode=local` para forçar uso offline.

Para usar **busca vetorial** no Docker, configure `OPENAI_API_KEY` e `RAG_EMBEDDINGS=pgvector` no `.env` da raiz. Ao iniciar, o backend tenta criar a extensão e indexar os documentos com o modelo `text-embedding-3-small`. Isso faz chamadas pagas à API de embeddings e envia o texto dos documentos ao provedor. Se o PostgreSQL/serviço de embeddings não estiver disponível, a busca cai para TF-IDF. Não use esse modo com documentos sensíveis sem política e consentimento adequados.

## Fluxo de demonstração

1. Abra **Visão geral** e altere o período entre 7, 14 e 30 dias. Os gráficos e indicadores são consultados novamente da API.
2. Abra **Copiloto IA** e pergunte: **“Quais foram os produtos mais vendidos esta semana e quanto devo preparar amanhã?”**. A resposta combina SQL e previsão de demanda. Os nomes das ferramentas aparecem abaixo do texto.
3. Pergunte: **“O que o manual diz sobre desperdício e validade?”**. Os documentos apresentados incluem arquivo e seção.
4. Acesse **Documentos**, pesquise um termo e envie um `.md`, `.txt` ou PDF pesquisável. O novo trecho passa a fazer parte da base de consulta.
5. Vá a **Previsões** para conferir MAE e WAPE versus baseline e a estimativa por produto.
6. Veja **Avaliação técnica** e consulte `reports/evaluation.md` para resultados do conjunto de 50 perguntas.

## Estrutura

```text
foodops-ai/
├── backend/
│   ├── app/
│   │   ├── core/config.py          # settings via environment
│   │   ├── db.py                   # engines e sessions SQLAlchemy
│   │   ├── models.py               # products, orders, order_items, documents
│   │   ├── main.py                 # FastAPI e endpoints
│   │   └── services/
│   │       ├── analytics.py        # aggregations SQL
│   │       ├── agent.py            # tool routing + OpenAI opcional
│   │       ├── forecasting.py      # modelos e holdout temporal
│   │       ├── knowledge.py        # RAG e upload
│   │       └── seed.py             # dados sintéticos determinísticos
│   ├── tests/                      # 7 smoke/integration tests
│   ├── scripts/evaluate.py         # 50 perguntas + métricas ML
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/pages/                  # dashboards, chat, ML, docs, avaliação
│   ├── src/components/             # shell e elementos compartilhados
│   ├── src/lib/api.js              # cliente REST
│   ├── src/styles.css              # UI responsiva
│   └── Dockerfile
├── eval/agent_cases.json           # 50 prompts com ferramentas esperadas
├── reports/evaluation.md          # relatório gerado, não números fictícios
├── reports/evaluation.json        # resultados detalhados por pergunta
├── docs/                           # arquitetura, escolhas, roteiro de demo
├── .github/workflows/ci.yml       # checks da API e build React
└── docker-compose.yml
```

## Endpoints principais

| Método | URL | Descrição |
|---|---|---|
| GET | `/api/health` | Estado da API e tipo de banco |
| GET | `/api/dashboard?days=7` | Indicadores, categorias, itens, séries e pedidos |
| GET | `/api/forecast?horizon=7` | Previsão + avaliação por janela temporal |
| POST | `/api/chat` | Assistente com ferramentas (modo auto ou local) |
| GET | `/api/knowledge` | Trechos e fontes disponíveis |
| GET | `/api/knowledge/search?q=...` | Busca documental com fontes |
| POST | `/api/knowledge/upload` | Arquivo multipart (`file`) |
| GET | `/api/evaluation` | Métricas do modelo de previsão |

Exemplo de pergunta:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Quais produtos mais venderam e quanto preparar amanhã?","mode":"local"}'
```

A resposta JSON contém `answer`, `tools_used`, `tool_results`, `sources`, `mode` e um aviso de dados sintéticos. O agente tem **ferramentas somente de leitura**; o endpoint de upload é separado.

## Rodar testes e avaliação

Com o backend instalado:

```bash
cd backend
pytest -q
cd ..
python backend/scripts/evaluate.py
```

Os testes usam um SQLite temporário e não apagam o banco principal. O script de avaliação gera `reports/evaluation.json` e `reports/evaluation.md`. A precisão de roteamento e as métricas de erro **não são declaradas como garantia de produção**: são calculadas sobre dados sintéticos e um conjunto fixo de 50 perguntas.

## Arquitetura em uma frase

**React → REST FastAPI → ferramentas específicas → SQLAlchemy (vendas), scikit-learn (previsões), TF-IDF/pgvector (documentos) → resposta rastreável.** A OpenAI é uma camada opcional de seleção e síntese, não a origem dos dados.

Para o diagrama e a justificativa das decisões, consulte `docs/ARQUITETURA.md`. Para um vídeo de demonstração de até dois minutos, veja `docs/ROTEIRO_DEMO.md`.

## Limitações / uso responsável

Este repositório é um **MVP demonstrativo, não um sistema pronto para operar restaurantes reais**. Não há login, RBAC, isolamento entre restaurantes, auditoria de alterações, integração POS, previsão de ingredientes por ficha técnica ou atualização transacional por dados reais. A previsão estima **unidades de itens vendidos**, não número de pedidos nem quantidade de insumos; não há inventário real, portanto não deve ser usada como ordem de compra automática. A busca em PDFs não faz OCR. As rotinas locais são verificáveis, enquanto respostas feitas por LLM ainda exigem revisão humana.

Para publicar online em produção, adicione autenticação, autorização multi-tenant, HTTPS, backups, gerenciamento de segredos, limitação de taxa, tratamento de documentos sensíveis, observabilidade, migrações Alembic e importação confiável de pedidos de um PDV.

## Portfólio

Esse projeto demonstra domínio de React, APIs Python, SQL, machine learning com baseline, RAG verificável, orquestração de ferramentas, Docker e avaliação. Os dados e procedimentos são **exclusivamente demonstrativos** e não representam o iFood ou qualquer restaurante real.

Licença: MIT (`LICENSE`).
