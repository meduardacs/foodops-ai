"""Development helper: generate the human-readable 50-question static suite."""
import json
from pathlib import Path

samples = [
 ('vendas',['get_sales_summary'],[
 'Quanto faturamos nos últimos sete dias?',
 'Qual foi o ticket médio da última semana?',
 'Qual o resultado de vendas desta semana?',
 'Quantos pedidos tivemos e qual a receita?',
 'Mostre o balanço das vendas nos últimos 30 dias?']),
 ('produtos',['get_top_products'],[
 'Quais foram os itens mais vendidos nesta semana?',
 'Mostre o ranking dos produtos mais populares.',
 'Quais os cinco produtos campeões de venda?',
 'Qual foi o produto mais pedido nos últimos 7 dias?',
 'Liste os produtos mais vendidos na quinzena.']),
 ('previsao',['get_demand_forecast'],[
 'Quanto devo preparar amanhã?',
 'Qual é a previsão para amanhã?',
 'Como está a demanda estimada para o próximo dia?',
 'Mostre a previsão de consumo dos próximos sete dias.',
 'Quantas unidades devo produzir amanhã?']),
 ('documentos',['search_knowledge'],[
 'O que diz o manual sobre armazenamento?',
 'Como devo reduzir o desperdício no restaurante?',
 'Quais as orientações de validade?',
 'Como funciona o procedimento de atendimento?',
 'Consulte o cardápio e os ingredientes.']),
 ('vendas_e_top',['get_sales_summary','get_top_products'],[
 'Qual o faturamento e quais os produtos mais vendidos?',
 'Quanto vendemos e qual o ranking dos itens?',
 'Compare receita e produtos mais pedidos nesta semana.',
 'Mostre ticket médio e os produtos campeões.',
 'Quantos pedidos tivemos e quais os itens populares?']),
 ('previsao_e_top',['get_top_products','get_demand_forecast'],[
 'Quais itens mais vendidos e quanto preparar amanhã?',
 'Quero o ranking dos produtos e a previsão para amanhã.',
 'Quais os produtos populares e qual a demanda futura?',
 'Identifique os itens campeões e indique quanto produzir amanhã.',
 'Produtos mais pedidos e previsão dos próximos dias.']),
 ('previsao_e_vendas',['get_sales_summary','get_demand_forecast'],[
 'Quanto faturamos na semana e qual a previsão para amanhã?',
 'Mostre vendas e demanda para amanhã.',
 'Quero ticket médio e quanto produzir amanhã.',
 'Qual foi a receita e qual a previsão para amanhã?',
 'Quantos pedidos tivemos na semana e quanto devo preparar amanhã?']),
 ('procedimento_e_previsao',['get_demand_forecast','search_knowledge'],[
 'Qual o procedimento para preparar a demanda de amanhã?',
 'Consulte o manual e a previsão de amanhã.',
 'Como evitar desperdício com a previsão de demanda?',
 'Quais orientações de estoque devo usar com a previsão?',
 'Qual a previsão para amanhã e como armazenar ingredientes?']),
 ('recentes',['get_recent_orders'],[
 'Mostre os pedidos recentes.',
 'Quais foram os últimos pedidos?',
 'Liste os últimos pedidos registrados.',
 'Quero ver pedidos recentes da operação.',
 'Quais são os últimos pedidos concluídos?']),
 ('serie',['get_sales_timeseries'],[
 'Mostre a evolução do faturamento por dia.',
 'Qual a tendência do movimento dia a dia?',
 'Preciso do gráfico histórico de faturamento.',
 'Mostre o histórico de faturamento diário.',
 'Como foi a evolução dos pedidos por dia?'])
]
cases = [{'id':f'{cat}-{i+1:02d}','question':q,'expected_tools':tools} for cat,tools,qs in samples for i,q in enumerate(qs)]
assert len(cases)==50
Path(__file__).with_name('agent_cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
