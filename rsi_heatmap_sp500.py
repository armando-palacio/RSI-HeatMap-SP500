import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from io import StringIO

# Función para calcular RSI
def rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# URL de la página de Wikipedia del S&P 500
url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# Descargar el contenido de la página
response = requests.get(url)

# Convertir el contenido a un objeto StringIO
html_content = StringIO(response.text)

# Leer las tablas de la página
tables = pd.read_html(html_content)

# La tabla de los componentes del S&P 500 suele ser la primera
sp500_table = tables[0]

# Extraer los tickers
sp500_tickers = sp500_table["Symbol"].tolist()

# Descargar datos de los tickers
data = yf.download(sp500_tickers, period='3mo', interval='1d', group_by='ticker')

rsi_values = []
for ticker in sp500_tickers:
    try:
        # Calcular RSI para cada ticker
        close_prices = data[ticker]['Close']
        rsi_series = rsi(close_prices)
        latest_rsi = rsi_series.iloc[-1]  # RSI más reciente
        prev_rsi = rsi_series.iloc[-2]   # RSI del día anterior
        rsi_values.append({"Ticker": ticker, "RSI": latest_rsi, "Prev_RSI": prev_rsi})
    except Exception as e:
        print(f"Error procesando {ticker}: {e}")

# Crear DataFrame
rsi_df = pd.DataFrame(rsi_values)

# Calcular el RSI medio
average_rsi = rsi_df["RSI"].mean()

# Crear el gráfico
fig = go.Figure()

# Agregar fondo para las zonas de RSI
fig.add_shape(type="rect", x0=-0.5, x1=len(rsi_df)-0.5, y0=70, y1=100,
              fillcolor="rgba(255, 0, 0, 0.1)", line_width=0, layer="below", name="Overbought")
fig.add_shape(type="rect", x0=-0.5, x1=len(rsi_df)-0.5, y0=30, y1=70,
              fillcolor="rgba(0, 255, 0, 0.1)", line_width=0, layer="below", name="Neutral")
fig.add_shape(type="rect", x0=-0.5, x1=len(rsi_df)-0.5, y0=0, y1=30,
              fillcolor="rgba(0, 0, 255, 0.1)", line_width=0, layer="below", name="Oversold")

# Agregar puntos de RSI
fig.add_trace(go.Scatter(
    x=rsi_df["Ticker"],
    y=rsi_df["RSI"],
    mode="markers",
    marker=dict(size=10, color=100-rsi_df["RSI"], colorscale="RdYlGn"),
    name="RSI Actual"
))

# Agregar líneas verticales desde RSI previo hasta RSI actual
for i, row in rsi_df.iterrows():
    fig.add_trace(go.Scatter(
        x=[row["Ticker"], row["Ticker"]],
        y=[row["Prev_RSI"], row["RSI"]],
        mode="lines",
        line=dict(color="green" if row["Prev_RSI"] < row["RSI"] else "red" , width=1, dash="dash"),
        showlegend=False
    ))

# Agregar línea horizontal del RSI medio
fig.add_hline(y=average_rsi, line=dict(color="orange", width=2, dash="dash"), name="RSI Promedio", annotation_text=f"RSI Promedio: {average_rsi:.2f}")

# Configurar el gráfico
fig.update_layout(
    title="RSI Heatmap del S&P 500",
    xaxis_title="Tickers",
    yaxis_title="RSI",
    template="plotly_white",
    height=600,
    width=1200,
)

# Mostrar el gráfico
fig.show()
