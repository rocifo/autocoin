import time
import pyupbit
import datetime
import requests

access = "tx0ocsdq7fkd4e5G2Zs38D4gE04IuCJhQ2hjV8vL"
secret = "xKyoFu3jk1wWh5M3uiUtfR4JFKhNR20VauUcGde5"
myToken = "xoxb-2524485957717-2527505140082-HZqrZDVQx4AeLn71KVShWFPh"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_lowlimit_price(ticker, l):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    lowlimit_price = df.iloc[0]['close']-(df.iloc[0]['close']*l)
    return lowlimit_price


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

ma_days = 15

def get_ma(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count= ma_days)
    ma = df['close'].rolling(ma_days).mean().iloc[-1]
    return ma

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
post_message(myToken,"#bitcointrade", "autotrade start")

coin=["BTC", "ETH", "SAND"]
#coin=["BTC"]
coinsort=3
bestk=0

target_price=[0,0,0,0,0]
ma=[0,0,0,0,0]
current_price=[0,0,0,0,0]
lowlimit_price=[0,0,0,0,0]
lowlimit_check=[0,0,0,0,0]

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-"+coin[0])
        end_time = start_time + datetime.timedelta(days=1)
           
        for i in range(coinsort): #loop for number of coin sorts

            if start_time < now < end_time - datetime.timedelta(seconds=10):
                target_price[i] = get_target_price("KRW-"+coin[i], bestk)
                ma[i] = get_ma("KRW-"+coin[i])
                current_price[i] = get_current_price("KRW-"+coin[i])
                lowlimit_price[i] = get_lowlimit_price("KRW-"+coin[i], 0.05) #5percent lowlimit
              #  lowlimit_price[i] = target_price[i]-(target_price[i]*0.05)

                if now.minute==0 and now.second<coinsort*4:
                    post_message(myToken,"#bitcointrade", str(now.hour)+" : " +str(now.minute)+" : " +  str(now.second) +" coin name "+ coin[i] + "\ncurrent price ->" + str(current_price[i])  + "\n"+str(ma_days) + " ma price ->" + str(ma[i]) +  "\ntarget price ->" + str(target_price[i])+ "\nlowlimit price ->" + str(lowlimit_price[i])  )




                if target_price[i] < current_price[i] and ma[i] < current_price[i] and lowlimit_check[i] == 0 : #15 days average line
              # if target_price[i] < current_price[i]: # without 15 days average line
                    krw = get_balance("KRW")
                    if krw > 5000:
                        currentsort=0
                        btc = get_balance(coin[i])
                        if btc*current_price[i] < 5000:


                            for j in range(coinsort): #check my holding coin sorts
                                btc = get_balance(coin[j])
                                current_price[j] = get_current_price("KRW-"+coin[j])
                                if btc*current_price[j] > 5000:
                                    currentsort=currentsort+1
                            buy_result = upbit.buy_market_order("KRW-"+coin[i], krw/(coinsort-currentsort)*0.9995) #balance/max coin sorts-current own coin sorts
                            currentsort=currentsort+1
                            post_message(myToken,"#bitcointrade", "BTC buy : " +str(buy_result)+ " current coin sort : "+ str(currentsort))

                if current_price[i] < lowlimit_price[i]:
                    btc = get_balance(coin[i])
                    if btc*current_price[i] > 5000:
                        lowlimit_check[i] = 1;
                        sell_result = upbit.sell_market_order("KRW-"+coin[i], btc*0.9995)
                        post_message(myToken,"#bitcointrade", "BTC Lowlimit sell : " + str(lowlimit_price[i]) + "\n" + str(sell_result))

            else:
                ma[i] = get_ma("KRW-"+coin[i])
                current_price[i] = get_current_price("KRW-"+coin[i])
                btc = get_balance(coin[i])
                lowlimit_check[i] = 0;
            
                if btc*current_price[i] > 5000 and ma[i] > current_price[i] :
               # if btc*current_price[i] > 5000:
                    post_message(myToken,"#bitcointrade", "selling process!!" + "\n"+ coin[i] +" price : " + str(btc*current_price[i])+"\n"+ str(ma_days)+ "ma : " + str( ma[i]) +"\n"+ "current price : " +str(current_price[i])   )
                    sell_result = upbit.sell_market_order("KRW-"+coin[i], btc*0.9995)
                    post_message(myToken,"#bitcointrade", coin[i] + " Sell : " +str(sell_result))
            time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#bitcointrade", e)
        time.sleep(1)
