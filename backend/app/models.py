from datetime import datetime, date, timezone
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    price: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default='un')
    active: Mapped[bool] = mapped_column(default=True)
    items: Mapped[list['OrderItem']] = relationship(back_populates='product')


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    channel: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default='concluido')
    total: Mapped[float] = mapped_column(Float, default=0)
    items: Mapped[list['OrderItem']] = relationship(back_populates='order', cascade='all,delete-orphan')


class OrderItem(Base):
    __tablename__ = 'order_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    order: Mapped[Order] = relationship(back_populates='items')
    product: Mapped[Product] = relationship(back_populates='items')


class KnowledgeDocument(Base):
    __tablename__ = 'knowledge_documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    source_name: Mapped[str] = mapped_column(String(220))
    section: Mapped[str] = mapped_column(String(160), default='Geral')
    content: Mapped[str] = mapped_column(Text)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    origin: Mapped[str] = mapped_column(String(30), default='demo')


class DailyNote(Base):
    __tablename__ = 'daily_notes'
    __table_args__ = (UniqueConstraint('date', name='uq_daily_note'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(255))
    impact: Mapped[float] = mapped_column(Float, default=0)
