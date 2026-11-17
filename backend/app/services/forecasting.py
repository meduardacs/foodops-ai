"""One-step time-series holdout + recursive seven-day product forecasts.

Split respects chronological order. No target dates or future realized sales enter features.
"""
from datetime import timedelta
from functools import lru_cache
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy.orm import Session
from app.services.analytics import daily_units_by_product


def _features(history: list[int], weekday: int, index: int) -> list[float]:
    return [weekday, int(weekday >= 5), index,
            history[-1], history[-7],
            float(np.mean(history[-7:])), float(np.mean(history[-14:]))]


def _metrics(actual: list[int], predicted: list[float]) -> dict:
    a, p = np.asarray(actual, float), np.asarray(predicted, float)
    return {
        'mae': round(float(np.mean(np.abs(a-p))), 2) if a.size else 0,
        'wape_pct': round(float(np.sum(np.abs(a-p))/np.sum(a)*100), 2) if np.sum(a) else 0,
    }


def _train_forecast(dates, products, horizon: int) -> dict:
    rows = []
    all_actual, all_model, all_baseline = [], [], []
    tomorrow = dates[-1] + timedelta(days=1)
    forecast_dates = [(tomorrow + timedelta(days=i)).isoformat() for i in range(horizon)]
    for product in products:
        series = list(product['values'])
        features = [_features(series[:i], dates[i].weekday(), i) for i in range(14, len(series))]
        target = series[14:]
        if len(features) < 32:
            continue
        split = max(16, len(features) - 21)
        test_model = RandomForestRegressor(n_estimators=42, min_samples_leaf=2,
                                           max_depth=9, random_state=42, n_jobs=1)
        test_model.fit(features[:split], target[:split])
        predicted_test = [max(0, float(v)) for v in test_model.predict(features[split:])]
        baseline_test = [series[14 + split + i - 7] for i in range(len(target[split:]))]
        all_actual.extend(target[split:])
        all_model.extend(predicted_test)
        all_baseline.extend(baseline_test)
        model = RandomForestRegressor(n_estimators=42, min_samples_leaf=2,
                                      max_depth=9, random_state=42, n_jobs=1)
        model.fit(features, target)
        history = series[:]
        preds = []
        for i in range(horizon):
            next_date = tomorrow + timedelta(days=i)
            pred = max(0, int(round(model.predict([_features(history, next_date.weekday(), len(history))])[0])))
            preds.append(pred)
            history.append(pred)
        rows.append({'product_id': product['id'], 'name': product['name'],
                     'category': product['category'], 'tomorrow': preds[0],
                     'seven_day_total': sum(preds), 'series': preds,
                     'last_7_units': sum(series[-7:])})
    rows.sort(key=lambda x: x['tomorrow'], reverse=True)
    totals = [sum(p['series'][i] for p in rows) for i in range(horizon)]
    model_m = _metrics(all_actual, all_model)
    baseline_m = _metrics(all_actual, all_baseline)
    return {
        'forecast_date': tomorrow.isoformat(),
        'horizon': horizon,
        'tomorrow_units': totals[0] if totals else 0,
        'next_7_days_units': sum(totals),
        'daily': [{'date': d, 'units': totals[i]} for i, d in enumerate(forecast_dates)],
        'products': rows,
        'evaluation': {
            'split': 'últimos 21 dias; janela temporal sem embaralhamento',
            'observations': len(all_actual),
            'model': 'RandomForestRegressor', 'baseline': 'mesmo dia da semana anterior',
            'model_mae': model_m['mae'], 'baseline_mae': baseline_m['mae'],
            'model_wape_pct': model_m['wape_pct'], 'baseline_wape_pct': baseline_m['wape_pct'],
            'improvement_mae_pct': round((baseline_m['mae']-model_m['mae']) / baseline_m['mae'] * 100, 1) if baseline_m['mae'] else 0,
            'note': 'Estimativas em unidades de itens, não número de pedidos. Dados sintéticos.'
        },
        'assumptions': 'Base histórica por produto; dia da semana, médias móveis e vendas recentes. Não usa estoque nem reservas.',
        'data_kind': 'synthetic',
    }


@lru_cache(maxsize=3)
def _cached_forecast(date_key: str, count_key: int, serialized: tuple, horizon: int):
    # Keep caching independent of db/session. serialized is tiny: 13 × 112 daily values.
    dates, products = serialized
    from datetime import date
    dates = [date.fromisoformat(d) for d in dates]
    products = [{'id': p[0], 'name': p[1], 'category': p[2], 'values': list(p[3])} for p in products]
    return _train_forecast(dates, products, horizon)


def forecast(db: Session, horizon: int = 7) -> dict:
    dates, products = daily_units_by_product(db)
    serialized = (tuple(d.isoformat() for d in dates),
                  tuple((p['id'],p['name'],p['category'],tuple(p['values'])) for p in products))
    return _cached_forecast(dates[-1].isoformat(), sum(map(lambda p: sum(p['values']),products)), serialized, horizon)
