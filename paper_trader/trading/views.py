import json
from django.shortcuts import render, get_object_or_404
import yfinance as yf
from .models import Instrument

def instrument_list(request):
    instruments_data = []

    for inst in Instrument.objects.all().order_by("symbol"):
        ticker = yf.Ticker(inst.symbol)
        hist = ticker.history(period="5d")

        if hist.empty or len(hist["Close"]) < 2:
            latest = None
            prev = None
        else:
            latest = round(float(hist["Close"].iloc[-1]), 2)
            prev = round(float(hist["Close"].iloc[-2]), 2)

        instruments_data.append({
            "name": inst.name,
            "symbol": inst.symbol,
            "price": latest if latest is not None else "N/A",
            "previous_close": prev if prev is not None else "N/A",
        })

    return render(request, "trading/instrument_list.html", {"instruments": instruments_data})


def instrument_detail(request, symbol):
    instrument = get_object_or_404(Instrument, symbol=symbol)
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1mo")
    dates = hist.index.strftime('%Y-%m-%d').tolist()
    close_prices = hist['Close'].round(2).tolist()

    context = {
        'instrument': instrument,
        'dates_json': json.dumps(dates),
        'close_prices_json': json.dumps(close_prices),
        'latest_price': ticker.info.get('regularMarketPrice', 'N/A'),
        'previous_close': ticker.info.get('previousClose', 'N/A'),
    }

    return render(request, 'trading/instrument_detail.html', context)