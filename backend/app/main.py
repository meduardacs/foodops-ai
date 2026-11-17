from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Literal
import logging
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db import Base, engine, SessionLocal, get_db
from app.models import Product, Order, KnowledgeDocument
from app.services.seed import seed_demo
from app.services.analytics import summary, top_products, daily_sales, categories, recent_orders
from app.services.forecasting import forecast
from app.services.knowledge import add_document, extract_file, search_knowledge, index_pgvector
from app.services.agent import answer

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('foodops')


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if get_settings().demo_seed:
        with SessionLocal() as db:
            result = seed_demo(db)
            logger.info('Demo database ready: %s',result)
            if get_settings().rag_embeddings == 'pgvector':
                try:
                    logger.info('pgvector: %s', index_pgvector(db))
                except Exception:
                    logger.exception('Vector index unavailable; offline TF-IDF will be used')
    yield

app = FastAPI(title='FoodOps AI API',version='1.0.0',
              description='Copiloto operacional com dados sintéticos, SQL, RAG e previsão de demanda.',
              lifespan=lifespan)
settings = get_settings()
app.add_middleware(CORSMiddleware,allow_origins=[s.strip() for s in settings.frontend_origin.split(',') if s.strip()],
                   allow_credentials=False, allow_methods=['GET','POST'], allow_headers=['*'])


class ChatTurn(BaseModel):
    role: Literal['user','assistant']
    content: str = Field(min_length=1,max_length=2500)


class ChatRequest(BaseModel):
    message: str = Field(min_length=2,max_length=1500)
    mode: Literal['auto','local'] = 'auto'
    history: list[ChatTurn] = Field(default_factory=list,max_length=10)


@app.get('/')
def root():
    return {'name':'FoodOps AI', 'api':'/docs','health':'/api/health'}


@app.get('/api/health')
def health(db: Session = Depends(get_db)):
    return {'status':'ok','time':datetime.now(timezone.utc).isoformat(),
            'database':'postgresql' if engine.dialect.name == 'postgresql' else 'sqlite',
            'orders':db.scalar(select(func.count(Order.id))),
            'products':db.scalar(select(func.count(Product.id))),
            'assistant_mode':'openai_available' if settings.openai_api_key else 'local',
            'data_kind':'synthetic'}


@app.get('/api/dashboard')
def dashboard(days: int = Query(7,ge=1,le=90),db: Session = Depends(get_db)):
    return {'summary':summary(db,days), 'active_products':db.scalar(select(func.count(Product.id)).where(Product.active.is_(True))), 'top_products':top_products(db,days,6),
            'daily_sales':daily_sales(db,days), 'categories':categories(db,days),
            'recent_orders':recent_orders(db,8)}


@app.get('/api/summary')
def get_summary(days: int = Query(7,ge=1,le=90),db: Session = Depends(get_db)):
    return summary(db,days)


@app.get('/api/products/top')
def get_top(days: int = Query(7,ge=1,le=90),limit: int = Query(8,ge=1,le=25),db: Session = Depends(get_db)):
    return top_products(db,days,limit)


@app.get('/api/sales/daily')
def get_sales(days: int = Query(30,ge=1,le=90),db: Session = Depends(get_db)):
    return daily_sales(db,days)


@app.get('/api/orders')
def get_orders(limit: int = Query(12,ge=1,le=50),db: Session = Depends(get_db)):
    return recent_orders(db,limit)


@app.get('/api/forecast')
def get_forecast(horizon: int = Query(7,ge=1,le=14),db: Session = Depends(get_db)):
    return forecast(db,horizon)


@app.get('/api/evaluation')
def get_evaluation(db: Session = Depends(get_db)):
    snapshot_path = Path(__file__).with_name('evaluation_snapshot.json')
    agent = {'status':'not_run','command':'python backend/scripts/evaluate.py'}
    if snapshot_path.exists():
        agent = json.loads(snapshot_path.read_text(encoding='utf-8'))
        agent['status'] = 'snapshot'
    return {'forecast': forecast(db)['evaluation'], 'agent': agent}


@app.post('/api/chat')
def chat(payload: ChatRequest,db: Session = Depends(get_db)):
    return answer(db,payload.message,payload.mode,[h.model_dump() for h in payload.history])


@app.get('/api/knowledge')
def get_knowledge(db: Session = Depends(get_db)):
    docs = db.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.id.desc())).all()
    return [{'id':d.id,'title':d.title,'source':d.source_name,'section':d.section,
             'origin':d.origin,'excerpt':d.content[:320]} for d in docs]


@app.get('/api/knowledge/search')
def query_knowledge(q: str = Query(min_length=2,max_length=500),db: Session = Depends(get_db)):
    results, mode = search_knowledge(db,q,6)
    return {'query':q,'mode':mode,'results':results}


@app.post('/api/knowledge/upload',status_code=201)
async def upload_knowledge(file: UploadFile = File(...),db: Session = Depends(get_db)):
    filename = (file.filename or 'documento').split('/')[-1].split('\\')[-1]
    max_size = settings.max_upload_mb * 1024 * 1024
    content = await file.read(max_size+1)
    await file.close()
    if len(content) > max_size:
        raise HTTPException(413,detail=f'Arquivo excede {settings.max_upload_mb} MB.')
    try:
        raw = extract_file(filename,content)
        chunks = add_document(db,filename.rsplit('.',1)[0],filename,raw)
    except ValueError as exc:
        raise HTTPException(400,detail=str(exc)) from exc
    return {'filename':filename,'chunks':len(chunks),'ids':[x['id'] for x in chunks],
            'note':'Trechos armazenados e disponíveis na busca com fonte.'}
