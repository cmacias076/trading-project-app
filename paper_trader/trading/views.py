from .models import Portfolio, Holding, Transaction, Instrument, PortfolioSnapshot
from datetime import date
from decimal import Decimal
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import BuyForm
import yfinance as yf
from curl_cffi.requests.errors import CurlError
from requests.exceptions import RequestException
from django.http import JsonResponse

def sell_instrument(request, symbol):
    instrument = get_object_or_404(Instrument, symbol=symbol)
    portfolio = Portfolio.objects.first()

    try:
        ticker = yf.Ticker(symbol)
        latest_price = ticker.info.get("regularMarketPrice")
    except (CurlError, RequestException):
        messages.error(request, f"Unable to fetch latest price for {symbol}. Are you offline?")
        return redirect("portfolio")

    if latest_price is None:
        messages.error(request, "Unable to fetch latest price.")
        return redirect("portfolio")

    price = Decimal(str(latest_price))
    instrument.current_price = price
    instrument.save(update_fields=["current_price"])

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 0))

        try:
            holding = Holding.objects.get(portfolio=portfolio, instrument=instrument)
        except Holding.DoesNotExist:
            messages.error(request, f"You don’t own any shares of {instrument.symbol}.")
            return redirect("portfolio")

        if quantity <= 0:
            messages.error(request, "Invalid quantity entered.")
            return redirect("portfolio")

        if quantity > holding.quantity:
            messages.error(request, f"You only own {holding.quantity} shares of {instrument.symbol}.")
            return redirect("portfolio")

        # Process valid sale
        total_value = price * quantity
        portfolio.cash_balance += total_value
        portfolio.save()

        holding.quantity -= quantity
        if holding.quantity == 0:
            holding.delete()
        else:
            holding.save()

        Transaction.objects.create(
            instrument=instrument,
            portfolio=portfolio,
            type="SELL",
            quantity=quantity,
            price=price,
        )

        messages.success(request, f"Successfully sold {quantity} shares of {instrument.symbol} at ${price}")
        return redirect("portfolio")

    return render(request, "trading/sell_instrument.html", {"instrument": instrument, "price": price})


def instrument_list(request):
    instruments_data = []

    for inst in Instrument.objects.all().order_by("symbol"):
        latest = None
        prev = None
        try:
            ticker = yf.Ticker(inst.symbol)
            hist = ticker.history(period="5d")

            if not hist.empty and len(hist["Close"]) >= 2:
                latest = round(float(hist["Close"].iloc[-1]), 2)
                prev = round(float(hist["Close"].iloc[-2]), 2)
                inst.current_price = Decimal(str(latest))
                inst.save(update_fields=["current_price"])
        except (CurlError, RequestException):
            messages.error(request, f"Could not fetch data for {inst.symbol}")

        instruments_data.append({
            "name": inst.name,
            "symbol": inst.symbol,
            "price": latest if latest is not None else "N/A",
            "previous_close": prev if prev is not None else "N/A",
        })

    return render(request, "trading/instrument_list.html", {"instruments": instruments_data})

def instrument_detail(request, symbol):
    instrument = get_object_or_404(Instrument, symbol=symbol)

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        dates = hist.index.strftime('%Y-%m-%d').tolist()
        close_prices = hist['Close'].round(2).tolist()
        latest_price = ticker.info.get('regularMarketPrice')
        previous_close = ticker.info.get('previousClose', 'N/A')
    except (CurlError, RequestException):
        messages.error(request, f"Unable to load data for {symbol}. Check your internet connection.")
        dates = []
        close_prices = []
        latest_price = None
        previous_close = "N/A"

    portfolio = Portfolio.objects.first()

    latest_price_value = latest_price if latest_price is not None else 'N/A'

    if request.method == 'POST':
        form = BuyForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if latest_price is None:
                messages.error(request, "Unable to fetch latest price.")
            else:
                price = Decimal(str(latest_price))
                total_cost = quantity * price

                if portfolio.cash_balance >= total_cost:
                    portfolio.cash_balance -= total_cost
                    portfolio.save()

                    holding, created = Holding.objects.get_or_create(
                        instrument=instrument,
                        portfolio=portfolio,
                        defaults={'quantity': quantity}
                    )
                    if not created:
                        holding.quantity += quantity
                        holding.save()

                    Transaction.objects.create(
                        instrument=instrument,
                        portfolio=portfolio,
                        type='BUY',
                        quantity=quantity,
                        price=price
                    )

                    instrument.current_price = price
                    instrument.save(update_fields=["current_price"])

                    messages.success(
                        request,
                        f"Bought {quantity} shares of {instrument.symbol} at ${price:.2f} each (Total: ${total_cost:.2f})"
                    )
                else:
                    messages.error(request, "Insufficient cash to complete purchase.")
        else:
            messages.error(request, "Invalid quantity entered.")    
    else:
        form = BuyForm()

    context = {
        'instrument': instrument,
        'dates_json': json.dumps(dates),
        'close_prices_json': json.dumps(close_prices),
        'latest_price': latest_price_value,
        'previous_close': previous_close,
        'form': form,
        'portfolio': portfolio,
        'message': "",
        'success': False
    }

    return render(request, 'trading/instrument_detail.html', context)

def portfolio_view(request):
    portfolio = Portfolio.objects.first()
    holdings = Holding.objects.filter(portfolio=portfolio)
    transactions = Transaction.objects.filter(portfolio=portfolio).order_by("-timestamp")

    total_holdings_value = Decimal("0.00")

    for h in holdings:
        try:
            ticker = yf.Ticker(h.instrument.symbol)
            latest_price = ticker.info.get("regularMarketPrice")
        except (CurlError, RequestException):
            messages.error(request, f"Unable to fetch price for {h.instrument.symbol}. Are you offline?")
            latest_price = None

        if latest_price is not None:
            price = Decimal(str(latest_price))
            h.instrument.current_price = price
            h.instrument.save(update_fields=["current_price"])
            total_holdings_value += h.quantity * price

    total_value = portfolio.cash_balance + total_holdings_value

    # Snapshot portfolio value
    today = date.today()
    if not PortfolioSnapshot.objects.filter(portfolio=portfolio, date=today).exists():
        PortfolioSnapshot.objects.create(
            portfolio=portfolio,
            total_value=round(total_value, 2)
        )

    snapshots = PortfolioSnapshot.objects.filter(portfolio=portfolio).order_by("date")
    snapshot_dates = [snap.date.strftime('%Y-%m-%d') for snap in snapshots]
    snapshot_values = [float(snap.total_value) for snap in snapshots]

    # === NEW: Gain/loss percentage ===
    INITIAL_CASH = Decimal("10000.00")
    gain_loss_percent = ((total_value - INITIAL_CASH) / INITIAL_CASH) * 100

    context = {
        "portfolio": portfolio,
        "holdings": holdings,
        "transactions": transactions,
        "snapshot_dates": json.dumps(snapshot_dates),
        "snapshot_values": json.dumps(snapshot_values),
        "total_value": round(total_value, 2),
        "gain_loss_percent": gain_loss_percent,  # Add to context
    }
    return render(request, "trading/portfolio.html", context)

def reset_portfolio(request):
    portfolio = Portfolio.objects.first() 
    portfolio.cash_balance = Decimal("10000.00")
    portfolio.save()

    Holding.objects.filter(portfolio=portfolio).delete()
    Transaction.objects.filter(portfolio=portfolio).delete()

    messages.success(request, "Portfolio has been reset to $10,000 with no holdings.")
    return redirect('portfolio')

def instrument_history_view(request):
    instruments = Instrument.objects.all().order_by("symbol")
    historical_data = []

    for inst in instruments:
        try:
            ticker = yf.Ticker(inst.symbol)
            hist = ticker.history(period="1mo")  # Adjust period as needed
            if hist.empty:
                continue
            dates = hist.index.strftime('%Y-%m-%d').tolist()
            prices = hist['Close'].round(2).tolist()
            historical_data.append({
                "symbol": inst.symbol,
                "dates": dates,
                "prices": prices,
            })
        except (CurlError, RequestException):
            continue

    context = {
        "historical_data": json.dumps(historical_data),
    }
    return render(request, "trading/instrument_history.html", context)