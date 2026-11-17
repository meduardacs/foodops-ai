"""Idempotent deterministic demo dataset, no real restaurant/customer data."""
from datetime import date, datetime, time, timedelta
import math
import random
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import Product, Order, OrderItem, KnowledgeDocument

PRODUCTS = [
    ('Smash Burger', 'Hambúrgueres', 29.90, 1.48),
    ('Burger da Casa', 'Hambúrgueres', 34.90, 1.16),
    ('Cheeseburger', 'Hambúrgueres', 26.90, 1.27),
    ('Pizza Margherita', 'Pizzas', 47.90, .92),
    ('Pizza Calabresa', 'Pizzas', 52.90, 1.03),
    ('Pizza Quatro Queijos', 'Pizzas', 59.90, .72),
    ('Açaí 500ml', 'Açaí e sobremesas', 22.90, 1.22),
    ('Brownie com Sorvete', 'Açaí e sobremesas', 19.90, .73),
    ('Refrigerante Lata', 'Bebidas', 7.90, 1.34),
    ('Suco Natural', 'Bebidas', 11.90, .96),
    ('Água Mineral', 'Bebidas', 5.90, .78),
    ('Batata Frita', 'Acompanhamentos', 15.90, 1.08),
    ('Onion Rings', 'Acompanhamentos', 18.90, .56),
]

DOCS = [
    ('Manual de produção', 'Boas práticas de preparo', 'manual-operacional.md',
     'Registre o volume produzido e as sobras ao final de cada turno. Para o pré-preparo, use a previsão como referência inicial e ajuste por reservas, eventos locais e disponibilidade de insumos. A previsão é uma estimativa e deve ser revisada pelo responsável.'),
    ('Manual de produção', 'Armazenamento e validade', 'manual-operacional.md',
     'Ingredientes perecíveis devem seguir condições de armazenamento e validade definidas pelo fabricante e pelas normas sanitárias aplicáveis. Identifique data de recebimento, abertura e vencimento. Aplique PVPS: primeiro que vence, primeiro que sai.'),
    ('Manual de produção', 'Controle de desperdício', 'manual-operacional.md',
     'Acompanhe perdas por item e motivo: vencimento, erro de preparo, devolução ou sobra. Considere o volume vendido, o percentual de desperdício e o estoque atual antes de definir nova compra. Não aumente automaticamente a produção apenas porque uma previsão cresceu.'),
    ('Cardápio demonstrativo', 'Hambúrgueres', 'cardapio-demo.md',
     'Smash Burger: pão brioche, blend bovino, queijo e molho da casa. Burger da Casa: blend bovino, queijo, cebola caramelizada e salada. Cheeseburger: pão, carne e queijo. Preços são exemplos sintéticos do sistema e podem ser atualizados no cadastro.'),
    ('Cardápio demonstrativo', 'Pizzas', 'cardapio-demo.md',
     'Pizza Margherita: molho de tomate, muçarela e manjericão. Pizza Calabresa: muçarela, calabresa e cebola. Pizza Quatro Queijos: blend de queijos. Verifique ingredientes e restrições alimentares com a equipe; esta documentação é demonstrativa.'),
    ('Procedimento de atendimento', 'Picos de movimento', 'atendimento.md',
     'Em períodos de pico, priorize conferência de comandas, comunicação de tempos estimados e reposição de embalagens. Antes do turno, confirme a equipe disponível e organize a bancada por volume esperado dos itens mais pedidos.'),
    ('Procedimento de atendimento', 'Pedidos por canal', 'atendimento.md',
     'O relatório separa pedidos por balcão, salão e delivery. Uma mudança importante na participação do delivery pode exigir revisão dos materiais de embalagem e da escala de expedição.'),
    ('Gestão de estoque', 'Ponto de reposição', 'estoque.md',
     'O ponto de reposição depende do consumo médio durante o prazo de entrega do fornecedor mais um estoque de segurança adequado. Não confunda quantidade vendida de um prato com quantidade de cada ingrediente necessária para produzi-lo.'),
]


def seed_demo(db: Session, today: date | None = None, days: int = 112) -> dict:
    today = today or date.today()
    if db.scalar(select(func.count(Product.id))) == 0:
        db.add_all([Product(name=n, category=c, price=p) for n, c, p, _ in PRODUCTS])
        db.commit()
    if db.scalar(select(func.count(KnowledgeDocument.id))) == 0:
        db.add_all([KnowledgeDocument(title=t, section=s, source_name=f, content=body)
                    for t, s, f, body in DOCS])
        db.commit()
    count = db.scalar(select(func.count(Order.id)))
    if count:
        return {'seeded': False, 'orders': count}

    rng = random.Random(20261117)
    ids = {p.name: p.id for p in db.scalars(select(Product)).all()}
    weights = [x[3] for x in PRODUCTS]
    channels = ['delivery', 'salao', 'balcao']
    orders = []
    items_to_insert = []
    # Date-relative reproducible sample; run only on an empty database.
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        weekday = day.weekday()
        day_factor = [1.00, .91, .98, 1.08, 1.27, 1.43, 1.15][weekday]
        trend = 0.90 + (days - offset) / days * .17
        seasonality = 1 + .08 * math.sin(offset / 6)
        n_orders = max(15, int(rng.gauss(65 * day_factor * trend * seasonality, 7)))
        for _ in range(n_orders):
            hour = rng.choices([11, 12, 13, 18, 19, 20, 21], [1, 2, 2, 1, 3, 3, 2])[0]
            created_at = datetime.combine(day, time(hour, rng.randrange(60), rng.randrange(60)))
            order = Order(created_at=created_at, channel=rng.choices(channels, [6, 3, 1])[0], status='concluido')
            selected = rng.choices(range(len(PRODUCTS)), weights=weights, k=rng.choices([1,2,3,4], [30,48,19,3])[0])
            selected_counts = {i: selected.count(i) for i in set(selected)}
            order.total = round(sum(PRODUCTS[i][2] * qty for i, qty in selected_counts.items()), 2)
            orders.append(order)
            for i, qty in selected_counts.items():
                items_to_insert.append((order, ids[PRODUCTS[i][0]], qty, PRODUCTS[i][2]))
    db.add_all(orders)
    db.flush()
    db.add_all([OrderItem(order_id=o.id, product_id=product_id, quantity=qty, unit_price=price)
                for o, product_id, qty, price in items_to_insert])
    db.commit()
    return {'seeded': True, 'orders': len(orders), 'items': len(items_to_insert)}
