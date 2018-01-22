import coinmarketcap
import csv
import numpy as np
import dash_html_components as html



def available_cmc_coins():
    market = coinmarketcap.Market()
    all_cmc_coins = market.ticker(limit=0)
    available_cmc_coins = []
    for coin in all_cmc_coins:
        available_cmc_coins.append({'label':coin['name'], 'value':coin['symbol']})
    available_cmc_coins.append({'label': 'Euro', 'value':'EUR'})
    return available_cmc_coins

def generate_table(dataframe, max_rows=100):
    rows = []
    for i in range(min(len(dataframe), max_rows)):
        row = []
        for col in dataframe.columns:
            value = dataframe.iloc[i][col]
            if col == '+/- %':
                row.append(html.Td('{:.2%}'.format(np.float64(value).item()), style={'backgroundColor': 'red' if value < 0 else 'green'}))
            elif col in ['Invested', 'Current Value', 'Purchase Value']:
                row.append(html.Td("{:.2f} €".format(np.float64(value).item())))
            else:
                row.append(html.Td(value))
        rows.append(html.Tr(row))
    return html.Div(html.Table([html.Tr([html.Th(col) for col in dataframe.columns])] + rows), style={"padding":"8px"})

def price_and_value_tabs(tabnum, prices, values):
    data = [{
            "x": values.index,
            "y": ['{:.2%}'.format(val) for val in values.iloc[:,tabnum]],
            'name': '% of Portfolio Value',
            'type': 'scatter',
            "mode": "lines",
            "line":dict(width=0.5,
              color='rgb(184, 247, 212)'),
            "fill": 'tonexty',
            },
            {
            'x': prices.index,
            'y': prices.iloc[:,tabnum],
            "mode": "lines",
            "yaxis":'y2',
            'name': 'Price €',
            'type': 'scatter'
            },
]
    figure={'data': data,
                 'layout': {
                     "paper_bgcolor":"rgba(255,255,255,0.5)",
                     "plot_bgcolor": "rgba(255,255,255,0)",
                     'title': ' Price € and Value % over time',
                     'margin': {'l': 60,'r': 60, 'b': 30, 't': 40 },
                         'xaxis':dict(
                         rangeselector=dict(
                         buttons=list([
                         dict(count=1,
                             label='1d',
                             step='day',
                             stepmode='backward'),
                         dict(count=6,
                             label='1m',
                             step='month',
                             stepmode='backward'),
                         dict(step='all')
                         ])),
                         rangeslider=dict(),
                         type='date'
                         ),
                         "showlegend": False,
                         "yaxis2": dict(title="Prices in €",
                                        overlaying='y',
                                        side='right',),
                         "yaxis":dict(title="Value in % of total Portfolio",
                                        range=[0,100],
                                        showgrid=False,
                                        )
                 }}
    return figure


def plot_bar_chart(shares):
    share_in_increase = []
    invest = sum(shares['Current Value'])-sum(shares['Purchase Value'])
    for coin in shares['Currency']:
        impact = np.float64(shares['Current Value'][(shares['Currency'] == coin)] - shares['Purchase Value'][(shares['Currency'] == coin)]).item()/invest
        if invest < 0:
            impact = impact * -1
        share_in_increase.append(impact)

    figure = {
      "data": [
        {
          "x": [coin for coin in shares['Currency']],
          "y": ['{:.2%}'.format(val) for val in share_in_increase],
          "text": ['Impact on Portfolio Value by {} in %'.format(coin) for coin in shares['Currency']],
          "name": "Impact on Portfolio",
          "type": "bar",
           "marker":dict(
                color='rgb(158,202,225)',
                line=dict(
                    color='rgb(8,48,107)',
                    width=1.5),
            ),
            "opacity":0.6

        },],
      "layout": {
            "title":"Impact on Portfolio",
            "paper_bgcolor":"rgba(255,255,255,0.5)",
            "plot_bgcolor":"rgba(255,255,255,0)",
            "xaxis":dict(showgrid=False),
            "yaxis":dict(showgrid=False, zeroline=False, autorange=True)
            }
    }
    return figure



def plot_pie_chart(shares):

    figure = {
      "data": [
        {
          "values": [value for value in shares['Current Value']],
          "labels": [coin for coin in shares['Currency']],
          "domain": {"x": [0, 1]},
          "name": "Share of Portfolio",
          "hoverinfo":"label+percent+name",
          "hole": .4,
          "type": "pie"
        },],
      "layout": {
            "paper_bgcolor":"rgba(255,255,255,0.5)",
            "plot_bgcolor": "rgba(255,255,255,0.5)",
            "title":"Share of Portfolio",
            "annotations": [
                {
                    "font": {
                        "size": 25
                    },
                    "showarrow": False,
                    "text": "%",
                    "x": 0.5,
                    "y": 0.5
                } ] } }
    return figure
