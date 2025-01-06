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
    "EpsilonAI": ["INTC", "AMD", "QCOM"],
    "TechGrowth": ["GOOGL", "MSFT", "NVDA", "TSLA", "AAPL"],
    "BlueChipInvestor": ["BRK-B", "VZ", "KO", "PG", "PEP"],
    "DividendFocused": ["XOM", "CVX", "T", "VZ", "JNJ"],
    "GrowthOpportunities": ["AMZN", "META", "PYPL", "NFLX", "GOOGL"],
    "GlobalEquity": ["VTI", "VXUS", "VEA", "VWO", "SCHB"],
    "EmergingMarkets": ["TCEHY", "BABA", "VWO", "MCHI", "FM"],
    "RenewableEnergy": ["NEE", "TSLA", "ENPH", "SEDG", "VWS"],
    "ConsumerStaples": ["KO", "PEP", "PG", "COST", "WMT"],
    "HealthcareFocus": ["JNJ", "PFE", "MRK", "AMGN", "ABBV"]
}

# Données fictives pour le profil utilisateur
USER_PROFILE = {
    "balance": 50000,  # Solde total
    "stocks": [
        {"ticker": "AAPL", "quantity": 10, "current_value": 175, "profit": 15},
        {"ticker": "TSLA", "quantity": 5, "current_value": 200, "profit": -10},
        {"ticker": "GOOGL", "quantity": 8, "current_value": 140, "profit": 20},
        {"ticker": "NVDA", "quantity": 3, "current_value": 500, "profit": 50},
    ],
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

def get_best_and_worst_profit(profile):
    stocks = profile["stocks"]
    if not stocks:
        return None, None

    best = max(stocks, key=lambda x: x["profit"])
    worst = min(stocks, key=lambda x: x["profit"])
    return best, worst


# Initialisation de l'application Dash
app = Dash(__name__)

# Layout de l'application
app.layout = html.Div([
    # En-tête
    html.Header([
        html.H1("Brocoli-Sama", style={'textAlign': 'center', 'color': '#3498DB'}),
        html.P("Votre compagnon de copytrading automatisé.", style={'textAlign': 'center', 'color': '#F0F0F0', 'fontSize': '18px'}),
    ], style={'backgroundColor': '#1F1F1F', 'padding': '20px'}),

    # Profil utilisateur
    html.Section([
        html.H2("Profil de l'utilisateur", style={"color": "#000000", "textAlign": "center"}),
        html.Div([
            html.Div(f"Solde total : ${USER_PROFILE['balance']:,}", style={"color": "#2ECC71", "fontSize": "24px"}),
            html.H4("Actions possédées :", style={"color": "#F0F0F0"}),
            html.Ul([
                html.Li(f"{stock['ticker']} - Quantité : {stock['quantity']} - Valeur actuelle : ${stock['current_value']} - Profit : {stock['profit']}%",
                        style={"color": "#3498DB" if stock["profit"] >= 0 else "#E74C3C"})
                for stock in USER_PROFILE["stocks"]
            ]),
            html.Div([
                html.H4("Action avec le meilleur profit :", style={"color": "#F0F0F0"}),
                html.P(f"{get_best_and_worst_profit(USER_PROFILE)[0]['ticker']} avec {get_best_and_worst_profit(USER_PROFILE)[0]['profit']}%", style={"color": "#2ECC71"}),
                html.H4("Action avec le pire profit :", style={"color": "#F0F0F0"}),
                html.P(f"{get_best_and_worst_profit(USER_PROFILE)[1]['ticker']} avec {get_best_and_worst_profit(USER_PROFILE)[1]['profit']}%", style={"color": "#E74C3C"}),
            ]),
        ], style={"padding": "20px", "backgroundColor": "#34495E", "borderRadius": "8px", "marginBottom": "20px"}),
    ]),

    # Sélection des portefeuilles
    html.Section([
        html.Label("Sélectionnez les portefeuilles à afficher :", style={"color": "#F0F0F0"}),
        dcc.Checklist(
            id="portfolio-selection",
            options=[{"label": name, "value": name} for name in STOCKS.keys()],
            value=[],
            inline=True,
            style={"marginBottom": "20px", "color": "#F0F0F0"}
        ),
        dcc.Store(id="portfolio-store"),
        dcc.Graph(id="portfolio-graph"),
        dcc.Interval(id="update-interval", interval=600 * 1000, n_intervals=0),
    ], style={"padding": "20px", "backgroundColor": "#2C3E50", "color": "#F0F0F0"}),

    # Footer
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
    [Input("portfolio-selection", "value"), Input("portfolio-store", "data")]
)
def update_graph(selected_portfolios, data):
    if not selected_portfolios or not data:
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

    # Filtrer les données pour inclure uniquement les portefeuilles sélectionnés
    filtered_data = [item for item in data if item["name"] in selected_portfolios]
    portfolio_data = pd.DataFrame(filtered_data)
    top_portfolios = portfolio_data.nlargest(5, "change")  # Trier par taux de croissance pour prendre les meilleurs

    return {
        "data": [
            go.Bar(
                x=[f"{row['name']}<br>Actions : {', '.join(row['tickers'])}" for _, row in top_portfolios.iterrows()],
                y=top_portfolios["change"],
                text=[f"Valeur totale : {row['value']:.2f} USD" for _, row in top_portfolios.iterrows()],
                textposition="auto",
                marker={"color": "#2ECC71"},  # Couleur verte pour indiquer la croissance
            )
        ],
        "layout": go.Layout(
            title="Portefeuilles ayant la plus forte croissance (%)",
            xaxis={"title": "Portefeuilles"},
            yaxis={"title": "Croissance (%)"},
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
