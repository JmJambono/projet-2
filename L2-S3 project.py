import yfinance as yf
import pandas as pd
from dash import Dash, dcc, html
import plotly.graph_objs as go
from threading import Timer
import webbrowser
import time
import threading
from dash.dependencies import Output, Input

# Liste des actions représentatives des portefeuilles
STOCKS = {
    "AlphaTrader": ["AAPL", "MSFT", "TSLA"],
    "BetaInvestor": ["GOOGL", "AMZN", "NVDA"],
    "GammaFund": ["META", "NFLX", "PYPL"],
    "DeltaHedge": ["BRK-B", "JPM", "BAC"],
    "EpsilonAI": ["INTC", "AMD", "QCOM"]
}

# Fonction pour récupérer les données financières via yfinance
def fetch_portfolio_data():
    new_data = []

    for name, tickers in STOCKS.items():
        try:
            data = yf.download(tickers, period="1d", interval="1d", progress=False)
            if not data.empty:
                close_prices = data["Close"].iloc[-1]  # Dernier jour
                # Calculer la somme des valeurs
                total_value = close_prices.sum()
                change = 0  # Pas de changement calculable sans la valeur précédente

                # Récupérer les données du jour précédent pour calculer le changement
                historical_data = yf.download(tickers, period="5d", interval="1d", progress=False)
                if len(historical_data["Close"]) > 1:
                    prev_close_prices = historical_data["Close"].iloc[-2]  # Avant-dernier jour
                    change = ((total_value - prev_close_prices.sum()) / prev_close_prices.sum()) * 100

                new_data.append({"name": name, "value": total_value, "change": change, "tickers": tickers})
            else:
                new_data.append({"name": name, "value": 0, "change": 0, "tickers": tickers})
        except Exception as e:
            print(f"Erreur pour {name}: {e}")
            new_data.append({"name": name, "value": 0, "change": 0, "tickers": tickers})

    return new_data  # Renvoie les données mises à jour


# Initialisation de l'application Dash
app = Dash(__name__)

# Layout de l'application
app.layout = html.Div([
    html.Header([  
        html.H1("Brocoli-Sama", style={'textAlign': 'center', 'color': '#3498DB'}),
        html.P("Votre compagnon de copytrading automatisé.", style={'textAlign': 'center', 'color': '#F0F0F0', 'fontSize': '18px'}),
    ], style={'backgroundColor': '#1F1F1F', 'padding': '20px'}),

    html.Section([
        dcc.Store(id="portfolio-store"),  # Utilisation de dcc.Store pour stocker les données
        dcc.Graph(id="portfolio-graph"),
        dcc.Interval(id="update-interval", interval=600 * 1000, n_intervals=0),
    ], style={"padding": "20px", "backgroundColor": "#2C3E50", "color": "#F0F0F0"}),

    html.Footer([
        html.P("© 2025 Brocoli-Sama. Tous droits réservés.", style={'textAlign': 'center', 'color': '#F0F0F0'}),
    ], style={'backgroundColor': '#1F1F1F', 'padding': '10px'}),
])

# Callback pour récupérer les données et les stocker dans dcc.Store
@app.callback(
    Output("portfolio-store", "data"),
    [Input("update-interval", "n_intervals")]
)
def update_data(n):
    portfolio_data = fetch_portfolio_data()  # Récupérer les nouvelles données
    return portfolio_data  # Retourner les données dans dcc.Store


# Callback pour mettre à jour le graphique avec les données stockées dans dcc.Store
@app.callback(
    Output("portfolio-graph", "figure"),
    [Input("portfolio-store", "data")]
)
def update_graph(data):
    if not data:
        return {
            "data": [],
            "layout": go.Layout(
                title="Aucune donnée disponible",
                xaxis={"title": "Portefeuilles"},
                yaxis={"title": "Valeur d'une action (USD)"},
                plot_bgcolor="#2C3E50",
                paper_bgcolor="#2C3E50",
                font=dict(color="#F0F0F0"),
            )
        }

    portfolio_data = pd.DataFrame(data)
    top_portfolios = portfolio_data.nlargest(5, "value")

    return {
        "data": [
            go.Bar(
                x=[f"{row['name']}<br>Actions : {', '.join(row['tickers'])}" for _, row in top_portfolios.iterrows()],
                y=top_portfolios["value"],
                text=[f"Croissance (comparé à hier) : {row['change']:.2f}%" for _, row in top_portfolios.iterrows()],
                textposition="auto",
                marker={"color": "#E74C3C"},
            )
        ],
        "layout": go.Layout(
            title="Performance des meilleurs portefeuilles",
            xaxis={"title": "Portefeuilles"},
            yaxis={"title": "Valeur d'une action (USD)"},
            plot_bgcolor="#2C3E50",
            paper_bgcolor="#2C3E50",
            font=dict(color="#F0F0F0"),
        ),
    }


# Fonction pour ouvrir automatiquement le navigateur
def open_browser():
    time.sleep(1)  # Donne le temps au serveur de démarrer
    webbrowser.open("http://127.0.0.1:8050")

# Lancer l'application dans un thread séparé
if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run_server(debug=False)
