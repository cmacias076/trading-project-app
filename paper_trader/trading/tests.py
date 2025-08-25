from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from decimal import Decimal
import pandas as pd
import datetime as dt

from .models import Instrument, Portfolio, Holding, Transaction


class TradingAppTests(TestCase):
    def setUp(self):
        self.portfolio = Portfolio.objects.create(cash_balance=Decimal("10000.00"))
        self.instrument = Instrument.objects.create(symbol="TEST", name="Test Instrument")

    def mock_yf_data(self, mock_ticker_class):
        """Sets up the yf.Ticker mock with price and history."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"regularMarketPrice": 100}

        # Create mock historical data as a DataFrame
        dates = pd.date_range(end=dt.datetime.now(), periods=5)
        prices = [100, 101, 102, 99, 100]
        hist_df = pd.DataFrame({"Close": prices}, index=dates)

        mock_ticker.history.return_value = hist_df
        mock_ticker_class.return_value = mock_ticker

    @patch("trading.views.yf.Ticker")
    def test_buy_valid_quantity(self, mock_ticker_class):
        self.mock_yf_data(mock_ticker_class)

        response = self.client.post(
            reverse("instrument_detail", args=[self.instrument.symbol]),
            {"quantity": 10},
            follow=True
        )
        self.assertContains(response, "Bought 10 shares of TEST")
        self.assertEqual(Holding.objects.get().quantity, 10)

    @patch("trading.views.yf.Ticker")
    def test_buy_invalid_quantity(self, mock_ticker_class):
        self.mock_yf_data(mock_ticker_class)

        response = self.client.post(
            reverse("instrument_detail", args=[self.instrument.symbol]),
            {"quantity": -5},
            follow=True
        )
        self.assertContains(response, "Invalid quantity entered")
        self.assertFalse(Holding.objects.exists())

    @patch("trading.views.Portfolio.objects.first")
    @patch("trading.views.yf.Ticker")
    def test_sell_valid_quantity(self, mock_ticker_class, mock_portfolio_first):
        self.mock_yf_data(mock_ticker_class)
        mock_portfolio_first.return_value = self.portfolio

        Holding.objects.create(
        portfolio=self.portfolio, instrument=self.instrument, quantity=10
     )

        response = self.client.post(
            reverse("sell_instrument", args=[self.instrument.symbol]),
            {"quantity": 5},
            follow=True
        )
        self.assertContains(response, "Successfully sold 5 shares of TEST")
        self.assertEqual(Holding.objects.get().quantity, 5)


    @patch("trading.views.Portfolio.objects.first")
    @patch("trading.views.yf.Ticker")
    def test_sell_invalid_quantity(self, mock_ticker_class, mock_portfolio_first):
        self.mock_yf_data(mock_ticker_class)
        mock_portfolio_first.return_value = self.portfolio

        Holding.objects.create(
            portfolio=self.portfolio, instrument=self.instrument, quantity=2
        )

        response = self.client.post(
            reverse("sell_instrument", args=[self.instrument.symbol]),
            {"quantity": 5},
            follow=True
        )
        self.assertContains(response, "You don’t own that many shares")

    @patch("trading.views.yf.Ticker")
    def test_reset_portfolio(self, mock_ticker_class):
        self.mock_yf_data(mock_ticker_class)

        Holding.objects.create(
            portfolio=self.portfolio, instrument=self.instrument, quantity=10
        )
        Transaction.objects.create(
            instrument=self.instrument,
            portfolio=self.portfolio,
            type="BUY",
            quantity=10,
            price=Decimal("100")
        )

        # Use POST for reset
        response = self.client.post(reverse("reset_portfolio"), follow=True)
        self.portfolio.refresh_from_db()

        self.assertEqual(self.portfolio.cash_balance, Decimal("10000.00"))
        self.assertFalse(Holding.objects.exists())
        self.assertFalse(Transaction.objects.exists())

    def test_instrument_list_view(self):
        response = self.client.get(reverse("instrument_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.instrument.symbol)
