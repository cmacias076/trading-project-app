
from .models import Portfolio, Holding, Transaction, Instrument, PortfolioSnapshot
from datetime import date
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import BuyForm
import yfinance as yf

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

            inst.current_price = latest
            inst.save(update_fields=["current_price"])

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

    portfolio = Portfolio.objects.first()

    latest_price = ticker.info.get("regularMarketPrice") 
    if latest_price is None:
        latest_price = instrument.current_price
    else:
        latest_price = round(float(latest_price), 2)
        instrument.current_price = latest_price
        instrument.save(update_fields=["current_price"])

    message = ""
    success = False

    if request.method == 'POST':
        form = BuyForm(request.POST)
        if form.is_valid():
            quantity= form.cleaned_data['quantity']
            total_cost= quantity * latest_price

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
                    price=latest_price
                )
                message = f"Successfully bought {quantity} shares of {instrument.symbol} at ${latest_price}"
                success = True
            else:
                message = "Insufficient cash to complete purchase."
        else:
            message = "Invalid quantity entered."
    else:
        form = BuyForm()

    context = {
        'instrument': instrument,
        'dates_json': json.dumps(dates),
        'close_prices_json': json.dumps(close_prices),
        'latest_price': latest_price,
        'previous_close': ticker.info.get('previousClose', 'N/A'),
        'form': form,
        'portfolio': portfolio,
        'message': message,
        'success': success
    }

    return render(request, 'trading/instrument_detail.html', context)

    

    # Portfolio for the "single user"
    portfolio = Portfolio.objects.first()
    price = instrument.current_price
    message = ""
    success = False

    if request.method == 'POST':
        form = BuyForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            total_cost = quantity * price
             
            # Check if the user has enough cash
            if portfolio.cash_balance >= total_cost:
                # Deduct from cash
                portfolio.cash_balance -= total_cost
                portfolio.save()

                 # Add to holdings
                holding, created = Holding.objects.get_or_create(
                    instrument=instrument,
                    portfolio=portfolio,
                    defaults={'quantity': quantity}
                )
                if not created:
                    holding.quantity += quantity
                    holding.save()

                # Record the transaction
                Transaction.objects.create(
                    instrument=instrument,
                    portfolio=portfolio,
                    type='BUY',
                    quantity=quantity,
                    price=price
                )

                message = f"Successfully bought {quantity} shares of {instrument.symbol} at ${price}"
                success = True
            else:
                message = "Insufficient cash to complete purchase."
        else:
            message = "Invalid quantity entered."

    else:
        form = BuyForm()

    context = {
        'instrument': instrument,
        'dates_json': json.dumps(dates),
        'close_prices_json': json.dumps(close_prices),
        'latest_price': ticker.info.get('regularMarketPrice', 'N/A'),
        'previous_close': ticker.info.get('previousClose', 'N/A'),
        'form': form,
        'portfolio': portfolio,
        'message': message,
        'success': success
    }

    return render(request, 'trading/instrument_detail.html', context)


def portfolio_view(request):
    portfolio = Portfolio.objects.first()
    holdings = Holding.objects.filter(portfolio=portfolio)
    transactions = Transaction.objects.filter(portfolio=portfolio).order_by("-timestamp")

    total_holdings_value = 0
    for h in holdings:
        ticker = yf.Ticker(h.instrument.symbol)
        latest_price = ticker.info.get("regularMarketPrice")

        if latest_price:
            h.instrument.current_price = latest_price
            h.instrument.save()
            total_holdings_value += h.quantity * latest_price
                
    total_value = portfolio.cash_balance + total_holdings_value

    today = date.today()
    if not PortfolioSnapshot.objects.filter(portfolio=portfolio, date=today).exists():
        PortfolioSnapshot.objects.create(
            portfolio=portfolio,
            total_value=round(total_value, 2)
        )

    snapshots = PortfolioSnapshot.objects.filter(portfolio=portfolio).order_by("date")
    snapshot_dates = [snap.date.strftime('%Y-%m-%d') for snap in snapshots]
    snapshot_values = [float(snap.total_value) for snap in snapshots]

    context = {
        "portfolio": portfolio,
        "holdings": holdings,
        "transactions": transactions,
        "snapshot_dates": json.dumps(snapshot_dates),
        "snapshot_values": json.dumps(snapshot_values),
        "total_value": round(total_value, 2),
    }
    return render(request, "trading/portfolio.html", context)

def reset_portfolio(request):
    portfolio = Portfolio.objects.first() 
    portfolio.cash_balance = 10000
    portfolio.save()

    Holding.objects.filter(portfolio=portfolio).delete()
    Transaction.objects.filter(portfolio=portfolio).delete()

    return redirect('portfolio')
