# FoodOps AI — Relatório de avaliação

Execução (UTC): 2026-11-17T17:50:02.881335+00:00

## Escopo

Dados de vendas **sintéticos**. Foram avaliadas 50 perguntas em português no **roteador local determinístico**; o script não avalia a qualidade de uma resposta gerada pela OpenAI. A previsão usa um holdout cronológico separado do treino.

## Resultado do agente

| Indicador | Resultado |
|---|---:|
| Casos executados | 50 |
| Correspondência exata das ferramentas | 94.0% |
| Recuperação de todas as ferramentas esperadas | 100.0% |
| Verificação pontual de valores na resposta | 100.0% |
| Latência média por pergunta (ambiente de execução) | 26.4 ms |

A verificação pontual de valores inspeciona presença de quantidades, identificadores ou fontes fornecidos pelas ferramentas. **Não prova ausência de alucinações**, não inspeciona todas as afirmações e não substitui avaliação humana.

## Demanda — comparativo temporal

| Métrica | Modelo RandomForest | Baseline: mesmo dia da semana anterior |
|---|---:|---:|
| MAE (unidades de item/dia) | 3.32 | 3.9 |
| WAPE | 28.33% | 33.28% |

Diferença relativa de MAE a favor do modelo: **14.9%** (valor negativo significa desempenho pior que a baseline). Foram avaliadas **273** observações por produto/dia.

**Protocolo:** últimos 21 dias; janela temporal sem embaralhamento. O modelo recebe calendário, últimas vendas e médias móveis. Nenhum dado de pedidos futuros entra como atributo; a avaliação mede previsão de um passo com histórico observado.

## Limitações e próximos passos

- Os dados são artificiais e não contêm feriados, clima, ruptura de estoque ou promoções.
- Não há backtesting de previsões recursivas de 7 dias; o teste de MAE é de um passo.
- O roteamento local usa regras linguísticas e pode classificar mensagens ambíguas incorretamente.
- A busca TF-IDF não captura todos os sinônimos; pgvector pode ser testado como alternativa opcional.
- Antes do uso comercial: autenticação, multiempresa, permissões, observabilidade e revisão de segurança.

## Reprodução

`python backend/scripts/evaluate.py` gera este arquivo e `reports/evaluation.json` com detalhes dos 50 casos.
