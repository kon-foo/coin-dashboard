import pandas as pd
import sqlite3#
from sqlalchemy import create_engine, String, Float, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import exists
from sqlalchemy import func
import coinmarketcap
import time
from collections import OrderedDict

Base = declarative_base()
class Portfolio(Base):
    __tablename__= 'portfolio'
    short = Column(String, primary_key=True)
    name = Column(String)
    ammount = Column(Float)
    purchase_price = Column(Float)
    purchase_value = Column(Float)

class HistoricalData(Base):
    __tablename__= 'historical_prices'
    id = Column(Integer, primary_key=True)
    date = (Column(Float))
    short = Column(String, ForeignKey('portfolio.short'))
    price_eur = Column(Float)
    price_btc = Column(Float)
    price_usd = Column(Float)
    price_eth = Column(Float)
    h24_vol_eur = Column(Float)
    market_cap_eur = Column(Float)
    total_supply = Column(Float)
    last_updated = Column(Float)
    portfolio = relationship("Portfolio", back_populates="historical_prices")

class HistoricalAssets(Base):
    __tablename__= 'historical_assets'
    id = Column(Integer, primary_key=True)
    date = (Column(Float))
    short = Column(String, ForeignKey('portfolio.short'))
    ammount = Column(Float)
    value_eur = Column(Float)
    value_btc = Column(Float)
    value_eth = Column(Float)
    value_usd = Column(Float)
    portfolio = relationship("Portfolio", back_populates="historical_assets")


def check_if_existing():
    session = Session()
    if session.query(Portfolio).first() == None:
        session.commit()
        return False
    else:
        session.commit()
        return True



def historic_value_data():
    session=Session()
    unique_dates = []
    unique_coins = []
    for date in session.query(HistoricalAssets.date).distinct():
        unique_dates.append(date.date)
    for coin in session.query(HistoricalAssets.short).distinct():
        unique_coins.append(coin.short)
    df_assets = pd.DataFrame({'date':unique_dates})
    df_prices = pd.DataFrame({'date':unique_dates})
    df_assets.set_index('date',inplace=True)
    df_prices.set_index('date',inplace=True)
    df_assets.index = pd.to_datetime(df_assets.index,unit='s')
    df_prices.index = pd.to_datetime(df_assets.index,unit='s')
    for coin in unique_coins:
        coin_date_val = []
        coin_date_price = []
        for date in unique_dates:
            values = session.query(HistoricalAssets.value_eur).filter_by(date=date, short=coin).first()
            value = 0 if values == None else values[0]
            prices = session.query(HistoricalData.price_eur).filter_by(date=date, short=coin).first()
            price = 0 if prices == None else prices[0]
            coin_date_val.append(value)
            coin_date_price.append(price)
        df_assets[coin] = coin_date_val
        df_prices[coin] = coin_date_price
    rows = []
    for index, row in df_assets.iterrows():
        newrow = OrderedDict()
        newrow['date'] = index
        summedvalue = sum(row)
        for coin in unique_coins:
            value = row[coin]
            newrow[coin] = value/summedvalue
        rows.append(newrow)
    df_assets_rel = pd.DataFrame(rows)
    df_assets_rel.set_index('date',inplace=True)
    session.commit()
    return df_assets, df_assets_rel, df_prices

def last_updated():
    session=Session()
    last_update = session.query(func.max(HistoricalAssets.date)).first()
    session.commit()
    return last_update[0]


def current_trend():
    session=Session()
    latestprices = []
    for coin in session.query(Portfolio).all():
        if not coin.ammount == 0:
            short = coin.short
            ammount = coin.ammount
            purchase_value = coin.purchase_value
            subqry = session.query(func.max(HistoricalAssets.date)).filter(HistoricalAssets.short == short).one()
            assets_data = session.query(HistoricalAssets).filter(HistoricalAssets.short == short, HistoricalAssets.date == subqry[0]).one()
            current_value = assets_data.value_eur
            percent = current_value/purchase_value-1
            latestprices.append({'Currency':short, 'Ammount':ammount, 'Purchase Value':purchase_value, 'Current Value':current_value, '+/- %':percent})
    df = pd.DataFrame(latestprices)
    df = df [['Currency', 'Ammount', 'Purchase Value', 'Current Value', '+/- %']]
    df_agg = pd.DataFrame([{'+/- %': df['Current Value'].sum()/df['Purchase Value'].sum()-1,'Current Value': df['Current Value'].sum(),'Invested':df['Purchase Value'].sum() }])
    df_agg = df_agg[['Invested', 'Current Value', '+/- %']]
    session.commit()
    return df, df_agg

def update_cmc_data():
    session = Session()
    market = coinmarketcap.Market()
    updatetime = time.time()
    eth_data = market.ticker('Ethereum', convert='EUR')
    for coin in session.query(Portfolio.name, Portfolio.short, Portfolio.ammount).all():
        if coin[1] == 'ETH':
            data = eth_data
        else:
            data = market.ticker(coin[0], convert='EUR')
        new_data = HistoricalData(date=updatetime,
                                short=coin[1],
                                price_eur=float(data[0]['price_eur']),
                                price_btc=float(data[0]['price_btc']),
                                price_usd=float(data[0]['price_usd']),
                                price_eth=float(data[0]['price_btc'])/float(eth_data[0]['price_btc']),
                                h24_vol_eur=float(data[0]['24h_volume_eur']),
                                market_cap_eur=float(data[0]['market_cap_eur']),
                                total_supply=float(data[0]['total_supply']),
                                last_updated=float(data[0]['last_updated'])
                                )
        new_assets = HistoricalAssets(date=updatetime,
                                short=coin[1],
                                ammount = coin[2],
                                value_eur=float(data[0]['price_eur'])*coin[2],
                                value_btc=float(data[0]['price_btc'])*coin[2],
                                value_usd=float(data[0]['price_usd'])*coin[2],
                                value_eth=float(data[0]['price_btc'])/float(eth_data[0]['price_btc'])*coin[2]
                                )
        session.add(new_data)
        session.add(new_assets)
    session.commit()
    return


def new_purchase(short, name, ammount, purchase_currency, price):
    session = Session()
    if not purchase_currency == 'EUR':
        pc_data = session.query(Portfolio).filter_by(short=purchase_currency).first()
        pc_data.ammount = pc_data.ammount - ammount*price
        pc_data.purchase_value = pc_data.ammount*pc_data.purchase_price
        price = price*pc_data.purchase_price
    value = ammount*price
    if not session.query(exists().where(Portfolio.short == short)).scalar():
        new_purchase = Portfolio(short=short,
                        name=name,
                        purchase_value = value,
                        purchase_price = price,
                        ammount = ammount
                        )
        session.add(new_purchase)
        session.commit()
    else:
        coin_data = session.query(Portfolio).filter_by(short=short).first()
        coin_data.ammount += ammount
        coin_data.purchase_value += value
        coin_data.purchase_price = coin_data.purchase_value/coin_data.ammount
        session.commit()
    update_cmc_data()
    return

Portfolio.historical_assets = relationship("HistoricalAssets", order_by=HistoricalAssets.date, back_populates="portfolio")
Portfolio.historical_prices = relationship("HistoricalData", order_by=HistoricalData.date, back_populates="portfolio")

engine = create_engine('sqlite:///portfolio.sqlite')
Session = sessionmaker()
Session.configure(bind=engine)
Base.metadata.create_all(engine)
