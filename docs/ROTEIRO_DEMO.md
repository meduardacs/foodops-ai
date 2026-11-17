# Roteiro de demonstração — 2 minutos

**0:00–0:20 — Visão geral.** Abra FoodOps AI no navegador. Mostre faturamento, pedidos concluídos, ticket médio e receita por categoria. Alterne de 7 para 30 dias para evidenciar consulta real à API.

**0:20–0:50 — Pergunta de negócio.** Abra Copiloto IA. Pergunte: “Quais itens mais venderam e quanto devo preparar amanhã?”. Leia o ranking e a previsão e aponte as ferramentas SQL e ML listadas embaixo da resposta. Diga que os números vêm do banco e do modelo, e são fictícios.

**0:50–1:15 — Busca verificável.** Pergunte “O que diz o manual sobre controle de desperdício?”. Mostre a fonte do documento. Em Documentos, pesquise “validade de ingredientes” e mostre título, trecho e nome do arquivo.

**1:15–1:40 — Machine learning avaliado.** Abra Previsões. Mostre unidades estimadas amanhã, curva dos próximos 7 dias e MAE do modelo versus baseline; explique que é estimativa de unidades de produtos, não de pedidos ou de ingredientes.

**1:40–2:00 — Engenharia.** Abra Avaliação técnica. Mostre os comandos de teste e aponte para o relatório com 50 perguntas, a documentação da arquitetura e o GitHub. Finalize dizendo que a aplicação roda offline em SQLite ou com PostgreSQL + Docker, e que LLM/pgvector são opcionais.

> Grave a tela após iniciar backend e frontend; não inclua chaves de API, nomes de clientes reais ou arquivos corporativos. Este arquivo é um roteiro — nenhum vídeo foi gerado automaticamente.
