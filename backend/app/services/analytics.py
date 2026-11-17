from datetime import date, datetime, timedelta, time
from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session
from app.models import Order, OrderItem, Product


def _range(days: int) -> tuple[datetime, datetime]:
    start = datetime.combine(date.today() - timedelta(days=days - 1), time.min)
    end = datetime.combine(date.today() + timedelta(days=1), time.min)
    return start, end


def summary(db: Session, days: int = 7) -> dict:
    start, end = _range(days)
    row = db.execute(select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0))
        .where(Order.created_at >= start, Order.created_at < end)).one()
    previous_start = start - timedelta(days=days)
    prev = db.execute(select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0))
        .where(Order.created_at >= previous_start, Order.created_at < start)).one()
    orders, revenue = int(row[0]), round(float(row[1]), 2)
    previous_revenue = float(prev[1])
    growth = round((revenue - previous_revenue) / previous_revenue * 100, 1) if previous_revenue else 0
    return {
        'days': days, 'orders': orders, 'revenue': revenue,
        'avg_ticket': round(revenue / orders, 2) if orders else 0,
        'previous_orders': int(prev[0]), 'previous_revenue': round(previous_revenue, 2),
        'revenue_growth_pct': growth, 'currency': 'BRL',
        'data_kind': 'synthetic', 'period_start': start.date().isoformat(),
        'period_end': date.today().isoformat(),
    }


def top_products(db: Session, days: int = 7, limit: int = 8) -> list[dict]:
    start, end = _range(days)
    rows = db.execute(select(Product.id, Product.name, Product.category,
         func.sum(OrderItem.quantity).label('units'),
         func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue'))
         .join(OrderItem, Product.id == OrderItem.product_id)
         .join(Order, Order.id == OrderItem.order_id)
         .where(Order.created_at >= start, Order.created_at < end)
         .group_by(Product.id, Product.name, Product.category)
         .order_by(desc('units')).limit(limit)).all()
    return [{'id': r[0], 'name': r[1], 'category': r[2], 'units': int(r[3]),
             'revenue': round(float(r[4]), 2)} for r in rows]


def daily_sales(db: Session, days: int = 30) -> list[dict]:
    start, end = _range(days)
    day_sql = func.date(Order.created_at)
    rows = db.execute(select(day_sql, func.count(Order.id), func.sum(Order.total))
        .where(Order.created_at >= start, Order.created_at < end)
        .group_by(day_sql)).all()
    by_day = {str(r[0]): (int(r[1]), round(float(r[2]), 2)) for r in rows}
    result = []
    for offset in range(days - 1, -1, -1):
        d = (date.today() - timedelta(days=offset)).isoformat()
        orders, revenue = by_day.get(d, (0, 0.0))
        result.append({'date': d, 'orders': orders, 'revenue': revenue})
    return result


def categories(db: Session, days: int = 7) -> list[dict]:
    start, end = _range(days)
    rows = db.execute(select(Product.category, func.sum(OrderItem.quantity).label('units'),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue'))
           .join(OrderItem, OrderItem.product_id == Product.id)
           .join(Order, OrderItem.order_id == Order.id)
           .where(Order.created_at >= start, Order.created_at < end)
           .group_by(Product.category).order_by(desc('revenue'))).all()
    return [{'name': r[0], 'units': int(r[1]), 'revenue': round(float(r[2]),2)} for r in rows]


def recent_orders(db: Session, limit: int = 12) -> list[dict]:
    rows = db.scalars(select(Order).order_by(Order.created_at.desc(), Order.id.desc()).limit(limit)).all()
    return [{'id': f'#{o.id:06d}', 'date': o.created_at.isoformat(), 'channel': o.channel,
             'status': o.status, 'total': round(o.total,2)} for o in rows]


def daily_units_by_product(db: Session, days: int = 112) -> tuple[list[date], list[dict]]:
    dates = [date.today() - timedelta(days=i) for i in range(days-1,-1,-1)]
    start, end = _range(days)
    d_sql = func.date(Order.created_at)
    rows = db.execute(select(Product.id, Product.name, Product.category, d_sql, func.sum(OrderItem.quantity))
       .join(OrderItem, OrderItem.product_id == Product.id)
       .join(Order, Order.id == OrderItem.order_id)
       .where(Order.created_at >= start, Order.created_at < end)
       .group_by(Product.id, Product.name, Product.category, d_sql)).all()
    products = {p.id: {'id': p.id,'name': p.name,'category':p.category,'values':[0]*days}
                for p in db.scalars(select(Product).order_by(Product.id)).all()}
    date_to_index = {d.isoformat(): i for i, d in enumerate(dates)}
    for p_id, _, _, d, qty in rows:
        idx = date_to_index.get(str(d))
        if idx is not None:
            products[p_id]['values'][idx] = int(qty)
    return dates, list(products.values())
