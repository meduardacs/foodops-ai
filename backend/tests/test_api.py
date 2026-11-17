def test_health(client):
    data = client.get('/api/health').json()
    assert data['status'] == 'ok'
    assert data['orders'] > 100
    assert data['products'] >= 10
    assert data['data_kind'] == 'synthetic'


def test_dashboard_sql_metrics(client):
    data = client.get('/api/dashboard?days=7').json()
    assert data['summary']['orders'] > 0
    assert data['summary']['revenue'] > 0
    assert len(data['daily_sales']) == 7
    assert data['top_products'][0]['units'] > 0
    assert sum(x['revenue'] for x in data['categories']) > 0


def test_forecast_is_evaluated(client):
    data = client.get('/api/forecast').json()
    assert data['tomorrow_units'] > 0
    assert len(data['daily']) == 7
    assert sum(p['tomorrow'] for p in data['products']) == data['tomorrow_units']
    assert data['evaluation']['observations'] > 0
    assert data['evaluation']['model_mae'] >= 0
    assert data['evaluation']['baseline_mae'] >= 0


def test_local_chat_uses_data_tools(client):
    response = client.post('/api/chat',json={'message':'Quais foram os produtos mais vendidos na semana e quanto preparar amanhã?','mode':'local'})
    assert response.status_code == 200
    data = response.json()
    assert 'get_top_products' in data['tools_used']
    assert 'get_demand_forecast' in data['tools_used']
    assert str(data['tool_results']['get_demand_forecast']['tomorrow_units']) in data['answer']
    assert data['mode'] == 'local'


def test_rag_has_traceable_sources(client):
    response = client.get('/api/knowledge/search',params={'q':'como evitar desperdício e organizar validade dos ingredientes?'})
    assert response.status_code == 200
    data = response.json()
    assert data['results']
    assert all(x['source'] and x['section'] and x['excerpt'] for x in data['results'])


def test_document_upload_and_search(client):
    response = client.post('/api/knowledge/upload',files={'file':('operacao.md',b'Planejar estoque e reposicao de materia prima no fechamento do dia.','text/markdown')})
    assert response.status_code == 201
    assert response.json()['chunks'] == 1
    results = client.get('/api/knowledge/search?q=reposicao%20de%20materia%20prima').json()
    assert any(x['source'] == 'operacao.md' for x in results['results'])


def test_validation_and_pdf_errors(client):
    assert client.get('/api/dashboard?days=120').status_code == 422
    assert client.post('/api/chat',json={'message':'a'}).status_code == 422
    invalid = client.post('/api/knowledge/upload',files={'file':('danger.exe',b'exe','application/octet-stream')})
    assert invalid.status_code == 400
