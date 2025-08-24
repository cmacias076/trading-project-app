from .models import Portfolio, Holding, Transaction, Instrument, PortfolioSnapshot
from datetime import date
from decimal import Decimal
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import BuyForm
import yfinance as yf

def sell_instrument(request, symbol):
    instrument = get_object_or_404(Instrument, symbol=symbol)
    portfolio = Portfolio.objects.first()

    ticker = yf.Ticker(symbol)
    latest_price = ticker.info.get("regularMarketPrice")

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
        ticker = yf.Ticker(inst.symbol)
        hist = ticker.history(period="5d")

        if hist.empty or len(hist["Close"]) < 2:
            latest = None
            prev = None
        else:
            latest = round(float(hist["Close"].iloc[-1]), 2)
            prev = round(float(hist["Close"].iloc[-2]), 2)

            inst.current_price = Decimal(str(latest))
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

    latest_price = ticker.info.get('regularMarketPrice')
    message = ""
    success = False

    if request.method == 'POST':
        form = BuyForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            if latest_price is None:
                message = "Unable to fetch latest price."
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

                    messages.success(request, f"Bought {quantity} shares of {instrument.symbol} at ${price}")
                else:
                    messages.error(request, "Insufficient cash to complete purchase.")
        else:
            message = "Invalid quantity entered."
    else:
        form = BuyForm()

    context = {
        'instrument': instrument,
        'dates_json': json.dumps(dates),
        'close_prices_json': json.dumps(close_prices),
        'latest_price': latest_price if latest_price is not None else 'N/A',
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

    total_holdings_value = Decimal("0")
    for h in holdings:
        ticker = yf.Ticker(h.instrument.symbol)
        latest_price = ticker.info.get("regularMarketPrice")

        if latest_price is not None:
            price = Decimal(str(latest_price))
            h.instrument.current_price = price
            h.instrument.save(update_fields=["current_price"])
            total_holdings_value += h.quantity * price

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
    portfolio.cash_balance = Decimal("10000.00")
    portfolio.save()

    Holding.objects.filter(portfolio=portfolio).delete()
    Transaction.objects.filter(portfolio=portfolio).delete()

    messages.success(request, "Portfolio has been reset to $10,000 with no holdings.")
    return redirect('portfolio')