"""Verifiable document retrieval. TF-IDF always works offline; pgvector is opt-in."""
from __future__ import annotations
import io
import logging
import re
import unicodedata
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import get_settings
from app.models import KnowledgeDocument

logger = logging.getLogger(__name__)


def chunks_from_text(content: str, max_chars: int = 1250) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
    result, current = [], ''
    for paragraph in paragraphs:
        for fragment in [paragraph[i:i+max_chars] for i in range(0,len(paragraph),max_chars)]:
            if len(current) + len(fragment) > max_chars and current:
                result.append(current)
                current = ''
            current = (current + '\n\n' + fragment).strip()
    if current:
        result.append(current)
    return result[:100]


def add_document(db: Session, title: str, filename: str, content: str, origin='upload') -> list[dict]:
    chunks = chunks_from_text(content)
    if not chunks:
        raise ValueError('Documento sem texto legível.')
    saved = []
    for i, chunk in enumerate(chunks, 1):
        doc = KnowledgeDocument(title=title[:200], source_name=filename[:220],
                                section=f'Trecho {i}', content=chunk, origin=origin)
        db.add(doc)
        db.flush()
        saved.append({'id': doc.id, 'section': doc.section})
    db.commit()
    try:
        index_pgvector(db)  # optional, ignored when not configured
    except Exception:
        logger.exception('Optional vector indexing failed; TF-IDF remains available')
    return saved


def extract_file(filename: str, data: bytes) -> str:
    extension = filename.lower().rsplit('.',1)[-1] if '.' in filename else ''
    if extension in ('txt','md'):
        try:
            return data.decode('utf-8-sig')
        except UnicodeDecodeError:
            raise ValueError('Arquivo de texto deve estar em UTF-8.') from None
    if extension == 'pdf':
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(data))
            if len(reader.pages) > 70:
                raise ValueError('Limite de 70 páginas por PDF.')
            content = '\n\n'.join(p.extract_text() or '' for p in reader.pages)
            if not content.strip():
                raise ValueError('PDF sem texto extraível. PDFs escaneados precisam de OCR externo.')
            return content
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('Não foi possível ler este PDF.') from exc
    raise ValueError('Formatos aceitos: PDF, TXT e MD.')


def _result(doc: KnowledgeDocument, score: float) -> dict:
    return {'id': doc.id, 'title': doc.title, 'section': doc.section,
            'source': doc.source_name, 'excerpt': doc.content[:520],
            'score': round(float(score), 3), 'origin': doc.origin}


def _search_tfidf(db: Session, query: str, limit: int) -> list[dict]:
    documents = db.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.id)).all()
    if not documents:
        return []
    corpus = [f'{d.title} {d.section} {d.content}' for d in documents]
    vectorizer = TfidfVectorizer(strip_accents='unicode', lowercase=True,
                                 ngram_range=(1,2), sublinear_tf=True, max_features=12000)
    matrix = vectorizer.fit_transform(corpus)
    q = vectorizer.transform([query])
    scores = cosine_similarity(q, matrix)[0]
    ranked = sorted(range(len(documents)), key=lambda i: float(scores[i]), reverse=True)
    return [_result(documents[i],scores[i]) for i in ranked[:limit] if scores[i] > 0.005]


def _pg_enabled(db: Session) -> bool:
    s = get_settings()
    return bool(s.rag_embeddings == 'pgvector' and s.openai_api_key and db.bind.dialect.name == 'postgresql')


def _embedding(text_value: str) -> list[float]:
    from openai import OpenAI
    return OpenAI(api_key=get_settings().openai_api_key, timeout=25, max_retries=1) \
        .embeddings.create(model='text-embedding-3-small',input=text_value[:7000]).data[0].embedding


def index_pgvector(db: Session) -> dict:
    """Create native vector index/table on PostgreSQL only when explicitly enabled."""
    if not _pg_enabled(db):
        return {'enabled': False}
    try:
        db.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        db.execute(text('CREATE TABLE IF NOT EXISTS document_vectors (doc_id INTEGER PRIMARY KEY REFERENCES knowledge_documents(id) ON DELETE CASCADE, embedding vector(1536) NOT NULL)'))
        db.commit()
        indexed_ids = set(db.execute(text('SELECT doc_id FROM document_vectors')).scalars().all())
        docs = db.scalars(select(KnowledgeDocument).where(~KnowledgeDocument.id.in_(indexed_ids))).all()
        for doc in docs:
            vector = '[' + ','.join(str(x) for x in _embedding(doc.title + '\n' + doc.content)) + ']'
            db.execute(text('INSERT INTO document_vectors(doc_id,embedding) VALUES (:id,CAST(:v AS vector)) ON CONFLICT (doc_id) DO UPDATE SET embedding=EXCLUDED.embedding'), {'id':doc.id, 'v':vector})
        db.commit()
        return {'enabled': True, 'indexed': len(docs)}
    except Exception:
        db.rollback()
        raise


def search_knowledge(db: Session, query: str, limit: int = 4) -> tuple[list[dict],str]:
    if not query.strip():
        return [], 'tfidf'
    if _pg_enabled(db):
        try:
            vector = '[' + ','.join(str(x) for x in _embedding(query)) + ']'
            rows = db.execute(text('''SELECT d.id, 1 - (v.embedding <=> CAST(:v AS vector)) AS score
                FROM document_vectors v JOIN knowledge_documents d ON d.id=v.doc_id
                ORDER BY v.embedding <=> CAST(:v AS vector) LIMIT :k'''), {'v':vector, 'k':limit}).all()
            documents = {d.id:d for d in db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.id.in_([r[0] for r in rows]))).all()}
            return [_result(documents[r[0]],r[1]) for r in rows if r[0] in documents], 'pgvector'
        except Exception:
            db.rollback()
            logger.warning('Vector retrieval unavailable; falling back to TF-IDF')
    return _search_tfidf(db,query,limit), 'tfidf'
