from alice_blue import AliceBlue as ab, LiveFeedType as lft, TransactionType, OrderType, ProductType
from pprint import pprint
from math import ceil
import os
from bs4 import BeautifulSoup as bs
import operator as ope
import requests as rq
from datetime import date,datetime,time
import pandas as pd
from time import sleep

Username="Your Username"
Password="Your Password"
Api_Secret="Your Api Secret"
at = ab.login_and_get_access_token(username=Username, password=Password, twoFA="0",
                                   api_secret=Api_Secret)
a = ab(username=Username, password=Password, access_token=at)
socket_opened = False
buy=[0]

def roundup(x):
    if x % 100 == 0:
        return int(x)
    else:
        t1=100 - x % 100
        t2=x % 100
        if t1<t2:
            return int(x+t1)
        else:
            return int(x-t2)

def da(d):
    if 200<=d["best_ask_price"]<=1000 and d["ltp"]<=ceil(d["best_ask_price"]):
       f="log_call_put.xlsx"
       if not os.path.exists(os.getcwd() + r"\{}".format(f)):
          pd.DataFrame({}).to_excel(f)
       tbs=pd.DataFrame({})
       if len(buy) > 1:
          df = pd.read_excel(f)
          if not df.empty:
             tbs=df[df["Instrument"]==d["instrument"].symbol]
             if not tbs.empty:
               if tbs["Date"][tbs["Date"].index[-1]]==date.today():
                 if d["ltp"]>=tbs["Entry Price"][tbs["Entry Price"].index[-1]] and tbs["Status"][tbs["Status"].index[-1]]=="Pending":
                     df.at[tbs["Status"].index[-1],"Status"]="Executed"
                     df.at[tbs["Status"].index[-1],"Entry Time"]=datetime.now().time()
                     tbs = df[df["Instrument"] == d["instrument"].symbol]
                 sl = ope.ge
                 so = ope.le
                 if tbs["Entry Time"][tbs["Entry Time"].index[-1]]!=" ":
                   if sl(tbs["Stop Loss"][tbs["Stop Loss"].index[-1]],d["ltp"]) and tbs["Stop loss Time"][tbs["Stop loss Time"].index[-1]]==" " and tbs["Square off Time"][tbs["Square off Time"].index[-1]]==" ":
                      df.at[tbs["Stop Loss"].index[-1],"Stop loss Time"]=datetime.now().time()
                      df.at[tbs["Net Stop loss"].index[-1],"Net Stop loss"]=(tbs["Stop Loss"][tbs["Stop Loss"].index[-1]]-tbs["Entry Price"][tbs["Entry Price"].index[-1]])*int(d["instrument"].lot_size)
                   elif so(tbs["Square off"][tbs["Square off"].index[-1]],d["ltp"]) and tbs["Square off Time"][tbs["Square off Time"].index[-1]]==" " and tbs["Stop loss Time"][tbs["Stop loss Time"].index[-1]]==" ":
                      df.at[tbs["Square off"].index[-1],"Square off Time"]=datetime.now().time()
                      df.at[tbs["Net Square off"].index[-1],"Net Square off"]=(tbs["Square off"][tbs["Square off"].index[-1]]-tbs["Entry Price"][tbs["Entry Price"].index[-1]])*int(d["instrument"].lot_size)
                      a.cancel_order(tbs["Order ID"][tbs["Order ID"].index[-1]])
                      seo=a.place_order(transaction_type=TransactionType.Sell,
                                        instrument=d["instrument"],
                                        quantity=1,
                                        price=float(ceil(d["ltp"])),
                                        product_type=ProductType.Intraday,
                                        order_type=OrderType.Limit)
                   tbs = df[df["Instrument"] == d["instrument"].symbol]
                 if tbs["Stop loss Time"][tbs["Stop loss Time"].index[-1]]!=" " or tbs["Square off Time"][tbs["Square off Time"].index[-1]]!=" ":
                   if d["ltp"]>d["open"]:
                       buy.pop(buy.index(d["instrument"].symbol))
                       df.at[tbs["Stop Loss"].index[-1], "Can Place Repeat Order"] = "Yes"
                   tbs = df[df["Instrument"] == d["instrument"].symbol]
                 df.to_excel(f, index=False)
       if d["instrument"].symbol not in buy and time(9,15,0)<=datetime.now().time()<=time(9,20,0) and (d["open"]+10 and ceil(d["best_ask_price"])+15)>d["high"]:
         if (d["ltp"] > d["open"] + 2 and d["open"] - d["low"] < 1 and d["open"] < d["close"] and d["open"] != 0) or (10 < d["ltp"] - d["open"] < 110):
           if 10 < d["ltp"] - d["open"] < 110:
             cn="10 < LTP - Open < 110"
           else:
             cn = "(LTP > Open + 2) & (Open - Low < 1) & (Open < Close)"
           m = {"Buy/Sell":"Buy","Instrument": d["instrument"].symbol, "Low": d["low"], "LTP": d["ltp"],
                 "PClose": d["close"], "ATP": d["atp"], "High": d["high"],
                 "Open": d["open"], "Entry Price": ceil(d["best_ask_price"]),"Status":"Pending","Entry Time":" ","Square off Time": " ",
                 "Stop loss Time": " ",
                 "Square off": ceil(d["best_ask_price"])+15, "Stop Loss": ceil(d["best_ask_price"])-50,
                 "Token": d["instrument"].token,
                 "Condition Match Time": datetime.now().time(),
                 "Date":date.today(),
                 "Condition": cn,
                 "LTQ": d["ltq"], "Volume": d["volume"], "Ask Price": d["best_ask_price"],
                 "Bid Price": d["best_bid_price"],"Can Place Repeat Order":"No",
                 "Net Square off":" ","Net Stop loss":" ","MTOM":" "}
           if "CE" in d["instrument"].symbol:
             m["CE/PE"]="CE"
           else:
             m["CE/PE"]="PE"
           buy.append(d["instrument"].symbol)
           order=a.place_order(transaction_type=TransactionType.Buy,
                            instrument=d["instrument"],
                            quantity=1,
                            order_type=OrderType.StopLossLimit,
                            product_type=ProductType.Intraday,
                            price=float(m["Entry Price"]),
                            trigger_price=float(m["Stop Loss"]))
           m["Order ID"] = order["data"]["oms_order_id"]
           lbe=pd.read_excel(f)
           df = pd.DataFrame(m, index=[0])
           lbe=lbe.append(df,ignore_index=True)
           lbe.to_excel(f,index=False)
           pprint(m)
           print("\n")


def open_callback():
     global socket_opened
     socket_opened = True


a.start_websocket(subscribe_callback=da,
                  socket_open_callback=open_callback,
                  run_in_background=True)
while (socket_opened == False):
     pass

r=rq.get("https://in.investing.com/indices/bank-nifty-futures",
         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"})
b=bs(r.content,"html.parser")
op=roundup(float(b.find_all("dd",class_="common-data-details")[3].text.replace("\n","").replace(",","")))
ins=[]
for j in [date(2021,7,8)]:
     for i in range(op-300,op+500,100):
        ins.append(a.get_instrument_for_fno(symbol="BANKNIFTY",expiry_date=j,is_fut=False,strike=i,is_CE=True))
        ins.append(a.get_instrument_for_fno(symbol="BANKNIFTY", expiry_date=j, is_fut=False, strike=i, is_CE=False))
a.subscribe(ins,lft.MARKET_DATA)
sleep(350000)
