"""Read-only data assistant. Grounded deterministic mode plus optional OpenAI tool calling."""
from __future__ import annotations
import json
import logging
import re
import unicodedata
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.services.analytics import summary, top_products, recent_orders, daily_sales
from app.services.forecasting import forecast
from app.services.knowledge import search_knowledge

log = logging.getLogger(__name__)

TOOLS = ['get_sales_summary','get_top_products','get_demand_forecast',
         'search_knowledge','get_recent_orders','get_sales_timeseries']

def normalize(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))


def detect_tools(message: str) -> list[str]:
    q = normalize(message)
    flags = {
        'get_top_products': bool(re.search(r'mais vendid|mais pedid|top |ranking|produto|item popular|itens populares|campe|campea',q)),
        'get_demand_forecast': bool(re.search(r'amanha|previs|prever|preparar|produzir|demanda|proximo|semana que vem|quantidade futura',q)),
        'search_knowledge': bool(re.search(r'manual|procedimento|cardapio|armazen|conserv|validade|estoque|desperdic|norma|orientac|como devo|boas praticas|ingrediente|reposic|pvps',q)),
        'get_recent_orders': bool(re.search(r'pedido[s]? recente|ultimo[s]? pedido|pedidos de hoje|ultimas compras',q)),
        'get_sales_timeseries': bool(re.search(r'evoluc|tendencia|grafico|dia a dia|por dia|historico de faturamento',q)),
        'get_sales_summary': bool(re.search(r'fatur|receita|quanto vend|ticket|vendas|resultado|balanco|total de pedidos|pedido[s]? da semana|quantos pedidos|pedidos tivemos|semana passada',q)),
    }
    matches = [tool for tool in TOOLS if flags[tool]]
    return matches or ['get_sales_summary']


def _days(message: str) -> int:
    q = normalize(message)
    if 'mes' in q or '30 dia' in q: return 30
    if '14 dia' in q or 'quinzena' in q or 'duas semanas' in q: return 14
    return 7


def run_tool(db: Session, name: str, args: dict | None = None) -> dict | list:
    args = args or {}
    days = max(1,min(90,int(args.get('days',7))))
    if name == 'get_sales_summary': return summary(db,days)
    if name == 'get_top_products': return top_products(db,days,limit=max(1,min(15,int(args.get('limit',5)))))
    if name == 'get_demand_forecast': return forecast(db,7)
    if name == 'search_knowledge':
        matches,mode = search_knowledge(db,str(args.get('query','')),limit=4)
        return {'matches': matches,'retrieval_mode':mode}
    if name == 'get_recent_orders': return recent_orders(db,limit=8)
    if name == 'get_sales_timeseries': return daily_sales(db,days)
    raise ValueError('Ferramenta não autorizada')


def _brl(value) -> str:
    return f'R$ {value:,.2f}'.replace(',','X').replace('.',',').replace('X','.')


def _render(tool_data: dict, days: int) -> tuple[str,list[dict]]:
    lines = []
    sources = []
    if 'get_sales_summary' in tool_data:
        s = tool_data['get_sales_summary']
        lines.append(f"**Resumo dos últimos {s['days']} dias:** {s['orders']} pedidos concluídos, faturamento de **{_brl(s['revenue'])}** e ticket médio de **{_brl(s['avg_ticket'])}**. Variação no faturamento frente ao período anterior: **{s['revenue_growth_pct']:+.1f}%**.")
    if 'get_top_products' in tool_data:
        rows = tool_data['get_top_products']
        lines.append('**Produtos com maior volume de vendas:**\n' + ('\n'.join(f'{i}. {p["name"]}: **{p["units"]} unidades**' for i,p in enumerate(rows,1)) if rows else 'Nenhum pedido encontrado nesse período.'))
    if 'get_demand_forecast' in tool_data:
        f = tool_data['get_demand_forecast']
        p = f['products'][:5]
        lines.append(f"**Estimativa para amanhã ({f['forecast_date']}): {f['tomorrow_units']} unidades de itens**, somadas entre produtos — não {f['tomorrow_units']} pedidos.\n" + '\n'.join(f'• {r["name"]}: **{r["tomorrow"]} un.**' for r in p))
        lines.append('Use a previsão como ponto de partida: ajuste pelo estoque disponível, reservas e eventos. O modelo usa dados sintéticos.')
    if 'get_recent_orders' in tool_data:
        rows = tool_data['get_recent_orders'][:5]
        lines.append('**Pedidos recentes:**\n' + '\n'.join(f'• {r["id"]}: {_brl(r["total"])} ({r["channel"]})' for r in rows))
    if 'get_sales_timeseries' in tool_data:
        rows = tool_data['get_sales_timeseries']
        if rows:
            lines.append(f'**Série diária:** {len(rows)} dias. Último dia: **{_brl(rows[-1]["revenue"])}** e **{rows[-1]["orders"]} pedidos**. Veja a evolução completa no painel.')
    if 'search_knowledge' in tool_data:
        matches = tool_data['search_knowledge']['matches']
        if matches:
            lines.append('**O que dizem os documentos:**')
            for match in matches[:3]:
                lines.append(f'• **{match["title"]} · {match["section"]}**: {match["excerpt"][:280]}')
                sources.append(match)
        else:
            lines.append('Não encontrei orientação relevante na base documental. Não vou inventar um procedimento.')
    return '\n\n'.join(lines) if lines else 'Não encontrei dados para responder.', sources


def answer_offline(db: Session, message: str) -> dict:
    days = _days(message)
    names = detect_tools(message)
    data = {n: run_tool(db,n, {'days':days,'query':message,'limit':5}) for n in names}
    text_value, sources = _render(data, days)
    return {'answer':text_value, 'mode':'local', 'tools_used':names,
            'tool_results':data,'sources':sources,
            'disclaimer':'Demonstração com dados sintéticos; previsões são estimativas.'}


TOOL_SCHEMAS = [
    {'type':'function','function':{'name':name, 'description':desc,'parameters':{
        'type':'object', 'properties':props, 'additionalProperties':False}}}
    for name,desc,props in [
        ('get_sales_summary','Agrega número de pedidos, faturamento e ticket médio.',{'days':{'type':'integer','description':'Período entre 1 e 90 dias'}}),
        ('get_top_products','Lista produtos mais vendidos, quantidade e receita.',{'days':{'type':'integer'},'limit':{'type':'integer'}}),
        ('get_demand_forecast','Retorna previsão de demanda por produto e erro do modelo.',{}),
        ('search_knowledge','Localiza trechos documentais com título e fonte.',{'query':{'type':'string'}}),
        ('get_recent_orders','Lista pedidos reais recentes do banco.',{}),
        ('get_sales_timeseries','Retorna faturamento diário para gráficos e tendências.',{'days':{'type':'integer'}}),
    ]
]

SYSTEM_PROMPT = '''Você é o copiloto FoodOps AI para um restaurante demonstrativo.
Responda SOMENTE com dados retornados pelas ferramentas. NUNCA invente vendas,
pedidos, estoque, fontes, ingredientes ou precisão do modelo. Todas as vendas são
sintéticas. Use ferramentas antes de mencionar números. Distinga unidades de itens
de número de pedidos. Para procedimentos, cite título, seção e nome do arquivo
exatamente como a ferramenta os retorna. Se não houver evidência, explique a lacuna.
Responda em português conciso e prático. Não execute alterações no banco.'''


def answer_openai(db: Session, message: str, history: list[dict] | None = None) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=get_settings().openai_api_key, timeout=28, max_retries=1)
    messages = [{'role':'system','content':SYSTEM_PROMPT}]
    for turn in (history or [])[-6:]:
        if turn.get('role') in ('user','assistant') and isinstance(turn.get('content'),str):
            messages.append({'role':turn['role'],'content':turn['content'][:2500]})
    messages.append({'role':'user','content':message})
    results, used = {}, []
    for _ in range(3):
        response = client.chat.completions.create(model=get_settings().openai_model,
           messages=messages,tools=TOOL_SCHEMAS,tool_choice='required' if not used else 'auto',temperature=0.1)
        choice = response.choices[0].message
        messages.append(choice.model_dump(exclude_none=True))
        if not choice.tool_calls:
            return {'answer':choice.content or 'Não encontrei resposta suficiente.', 'mode':'openai',
                    'tools_used':used,'tool_results':results,
                    'sources':results.get('search_knowledge',{}).get('matches',[]),
                    'disclaimer':'Dados demonstrativos; conteúdo gerado por LLM sujeito a revisão.'}
        for call in choice.tool_calls:
            if call.function.name not in TOOLS:
                value = {'error':'tool não autorizada'}
            else:
                try:
                    value = run_tool(db,call.function.name,json.loads(call.function.arguments or '{}'))
                    used.append(call.function.name)
                    results[call.function.name] = value
                except (ValueError, TypeError) as exc:
                    value = {'error':str(exc)}
            messages.append({'role':'tool','tool_call_id':call.id,'content':json.dumps(value,ensure_ascii=False,default=str)})
    # Avoid unconstrained LLM completion; return tool-grounded deterministic render.
    rendered, sources = _render(results,7)
    return {'answer':rendered, 'mode':'openai', 'tools_used':used,
            'tool_results':results,'sources':sources,
            'disclaimer':'Limite de execução do agente; resposta montada a partir das ferramentas.'}


def answer(db: Session, message: str, mode: str = 'auto', history: list[dict] | None = None) -> dict:
    settings = get_settings()
    if mode == 'local' or not settings.openai_api_key:
        return answer_offline(db,message)
    try:
        return answer_openai(db,message,history)
    except Exception:
        log.exception('OpenAI agent failed; using local grounded response')
        response = answer_offline(db,message)
        response['disclaimer'] += ' O provedor de IA ficou indisponível; utilizei o modo local.'
        return response
