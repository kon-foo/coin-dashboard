# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import plotly.plotly as py
import sqlite3
from datetime import datetime
import coinmarketcap
import time
from sqlalchemy import create_engine

import db_operations
import plot_graphs

####### CSS / Styling ######
colors = {
    'text':"#7FDBFF",
    'left':"#E86361",
    'right':"#3A82B5"
}
####### ------------ ##########

###### Load Data #########

class DataCache():
    cmc_coins_and_symbols = plot_graphs.available_cmc_coins()
    historical_value_eur, historical_value_eur_rel, historical_prices_eur = None, None, None
    current_trend, aggregated = None, None

    def update_data(self):
        self.historical_value_eur, self.historical_value_eur_rel, self.historical_prices_eur = db_operations.historic_value_data()
        self.current_trend, self.aggregated = db_operations.current_trend()


##########################


##### Layout ##########

app = dash.Dash()
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

def render_layout():
    print('Rendering Layout')
    return html.Div(id="body",children=[
    html.Div(id="Title",
    children=[
        html.H1(children='Crypto Currency Dashboard'),
        html.Div(children='Crypto Currency Portfolio & current prices from coinmarketcap.'),
        html.Div(children='Donations: ERC20: 0x4961631A91f3497c9B5Bc57Fc98e5cC0e277E31E  -  NEP5: ARbaEVg1wiG4cqbDqkFeXrgR9oz2U9sRTY.')],
        style={
            'width': '100%',
            'textAlign':'center',
            'color': colors['text']
            }),
    html.Div(id="left-column",
    children=[
        html.Div([
                plot_graphs.generate_table(session_data.aggregated),
                plot_graphs.generate_table(session_data.current_trend)
                ],
                style={
                    'width': 'auto',
                    'margin': '15px',
                    "padding": "20px",
                    "backgroundColor": "rgba(255,255,255,0.5)",
                }),
    html.Div(['Add new purchase:',
        dcc.Dropdown(
            id='new_purchased_coin',
            options=session_data.cmc_coins_and_symbols,
            placeholder='Purchased Coin'
        ),
        dcc.Dropdown(
            id='bought_with',
            options=session_data.cmc_coins_and_symbols,
            placeholder="bought with"
        ),
        dcc.Input(id='new_purchased_ammount', type='text', value='Ammount'),
        dcc.Input(id='new_purchase_price', type='text', value='Price per Coin'),
        html.Button(id='purchase_submit-button', children='Submit'),
        html.Div(children='', id='new_purchase_status')
        ],
        style={
                    'margin':'15px',
                    "width": "auto",
                    "padding": "20px",
                    "backgroundColor": "rgba(255,255,255,0.5)"
        })
    ],
    style={
        "width":"50%",
        "height":"inherit",
        "float":"left",
        "backgroundColor": colors['left'],
    }),
    html.Div(id="right-column",
    children=[
        html.Div([
            html.Button(id='refresh-button', children='Refresh Data From Coinmarketcap'),
            html.Div(id="last-refresh")],
            style={
                'margin':'20px',
                'marginLeft': '30%'
            },
          ),
        html.Div(id="price_over_time", children=[
            dcc.Tabs(
                    tabs=[
                        {'label': col, 'value': session_data.historical_prices_eur.columns.get_loc(col)} for col in session_data.historical_prices_eur
                    ],
                    value=0,
                    id='tabs',
                    vertical=False
                ),
                html.Div(id='tab-output-div', children=[dcc.Graph(id="tab-output")])
            ], style={
                'width': "auto",
                'marginLeft': "15px",
                'marginRight': "15px",
                "marginBottom": "15px"
            }),
        html.Div(id="pie_bar_chart_div",children=[
            dcc.Graph(id="pie_chart",
                figure=plot_graphs.plot_pie_chart(session_data.current_trend),
                style={"width":"50%",
                        "float":"left"}
            )
            ,
            dcc.Graph(id="bar_chart",
                figure=plot_graphs.plot_bar_chart(session_data.current_trend),
                style={"width":"50%",
                        "float":"left"}
            )

        ],
        style={
                'width': "auto",
                'marginLeft': "15px",
                'marginRight': "15px",
                "marginBottom": "15px",
        }
        ),

    ],
    style={
        "display":"block",
        "width":"50%",
        "float":"left",
        "height": "inherit",
        "backgroundColor": "#3A82B5"
        }),
],
style={
    "backgroundColor": "gray",
	"height":"100%",
	"width":"100%",

})

def first_layout():
    return html.Div(id="body",children=[
    html.Div(id="Title",
    children=[
        html.H1(children='Crypto Currency Dashboard'),
        html.Div(children='Crypto Currency Portfolio & current prices from coinmarketcap.'),
        html.Div(children='Donations: ERC20: 0x4961631A91f3497c9B5Bc57Fc98e5cC0e277E31E  -  NEP5: ARbaEVg1wiG4cqbDqkFeXrgR9oz2U9sRTY.')],
        style={
            'width': '100%',
            'textAlign':'center',
            'color': colors['text']
            }),
    html.Div(id="left-column",
    children=[
    html.Div(['Add new purchase:',
        dcc.Dropdown(
            id='new_purchased_coin',
            options=session_data.cmc_coins_and_symbols,
            placeholder='Purchased Coin'
        ),
        dcc.Dropdown(
            id='bought_with',
            options=session_data.cmc_coins_and_symbols,
            placeholder="bought with"
        ),
        dcc.Input(id='new_purchased_ammount', type='text', value='Ammount'),
        dcc.Input(id='new_purchase_price', type='text', value='Price per Coin'),
        html.Button(id='purchase_submit-button', children='Submit'),
        html.Div(children='', id='new_purchase_status')
        ],
        style={
                    'margin':'15px',
                    "width": "auto",
                    "padding": "20px",
                    "backgroundColor": "rgba(255,255,255,0.5)"
        })
    ],
    style={
        "width":"50%",
        "height":"inherit",
        "float":"left",
        "backgroundColor": colors['left'],
        "height": "100vh"
    }),
    html.Div(id="right-column",
    children=html.Div('Graphs will be created after you entered your first purchase and restarted the server.',
        style={
        "backgroundColor":"rgba(255,255,255,0.5)",
        "fontSize": "20px",
        "padding": "5px",
        "margin": "15px"

        }),
    style={
        "display":"block",
        "width":"50%",
        "float":"left",
        "height": "inherit",
        "backgroundColor": "#3A82B5",
        "height": "100vh"
        }),
],
style={
    "backgroundColor": "gray",
	"height":"100%",
	"width":"100%",

})

######### Start ########
session_data = DataCache()
if db_operations.check_if_existing():
    session_data.update_data()
    app.layout = render_layout
else:
    app.layout = first_layout



####### Callbacks ##########
if db_operations.check_if_existing():
    @app.callback(Output('tab-output', 'figure'), [Input('tabs', 'value')])
    def display_price_value_tab(value):
        return plot_graphs.price_and_value_tabs(value, session_data.historical_prices_eur, session_data.historical_value_eur_rel)


    @app.callback(Output('last-refresh', 'children'),
                [Input('refresh-button', 'n_clicks')])
    def coinmarketcap_api_call(n_clicks):
        if n_clicks != None:
            db_operations.update_cmc_data()
            session_data.update_data()
            return 'Successfully updated. Please reload page.'
        else:
            updatetime = db_operations.last_updated()
            return 'Last Update: {} '.format(time.strftime('%a, %d %b %Y %H:%M:%S',time.localtime(updatetime)))

@app.callback(Output('new_purchase_status', 'children'),
                [Input('purchase_submit-button', 'n_clicks')],
                [State('new_purchased_coin', 'value'),
                State('bought_with', 'value'),
                State('new_purchase_price', 'value'),
                State('new_purchased_ammount', 'value')])
def new_purchase_submitted(n_clicks, new_purchased_coin, bought_with, new_purchase_price,new_purchased_ammount):
    if n_clicks == None:
        return ''
    name = next(item for item in session_data.cmc_coins_and_symbols if item["value"] == new_purchased_coin)['label']
    db_operations.new_purchase(new_purchased_coin, name, float(new_purchased_ammount), bought_with, float(new_purchase_price))
    session_data.update_data()
    return 'The purchase of {} {} for {} {}/{} has successfully been added to the database. Please reload the page.'.format(new_purchased_ammount,name,new_purchase_price, bought_with, name)



if __name__ == '__main__':
    #app.run_server(debug=True)
    app.run_server(debug=True)
