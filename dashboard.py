# dashboard.py
import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import asyncpg
import asyncio
import os

app = dash.Dash(__name__)

async def get_data():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    rows = await conn.fetch("SELECT nickname, COUNT(*) as top1s FROM new_records WHERE rank = 1 GROUP BY nickname;")
    await conn.close()
    return pd.DataFrame(rows, columns=["nickname", "top1s"])

@app.server.route("/health")
def health_check():
    return "OK"

@app.callback(
    dash.Output("leaderboard", "figure"),
    dash.Input("interval", "n_intervals")
)
def update_leaderboard(n):
    df = asyncio.run(get_data())
    fig = px.bar(df, x="nickname", y="top1s", title="Top Players by # of WRs")
    return fig

app.layout = html.Div([
    html.H1("Trackmania Leaderboard Dashboard"),
    dcc.Graph(id="leaderboard"),
    dcc.Interval(id="interval", interval=5*60*1000)  # refresh every 5 min
])
server = app.server


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8080)
