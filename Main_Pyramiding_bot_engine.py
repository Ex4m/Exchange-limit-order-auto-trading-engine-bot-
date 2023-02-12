
from asyncore import loop
import mailbox
from textwrap import fill
import ccxt
import keyboard
import Gmail_agg as gma
import config as cfg
import sys, traceback
import test2 as tst2
import pandas as pd



bin = ccxt.binance({
    "enableRateLimit" :             cfg.my_binance_config["enableRateLimit"],
    "apiKey" :                      cfg.my_binance_config["apiKey"],
    "secret" :                      cfg.my_binance_config["secret"],
    })

class binFu(ccxt.binance): #Binance Futures subclass
    def __init__(self):
        super().__init__()
        self.urls['api'] = 'https://fapi.binance.com/fapi'

    def fetch_ticker(self, symbol):
        ticker = self.fetch_ticker_from_exchange(symbol)
        return self.parse_ticker(ticker, symbol)

    def fetch_ticker_from_exchange(self, symbol):
        ticker = self.fetch(self.urls['api'] + '/v1/ticker/24hr', {'symbol': symbol})
        return ticker

# Binance nemá rádo desync s word time
"""
#import ntplib
#import time
import subprocess
def sync_time():
    # Synchronize the time with the time server at time.windows.com
    subprocess.run(['w32tm', '/resync', '/rediscover', '/computer:time.windows.com'])
try:
    sync_time()
    if not Exception:
        print('System clock synchronized with time.windows.com')
except Exception as chyba:
    print(chyba)

client = ntplib.NTPClient()
time_server = "time.windows.com"
response = client.request(time_server)
system_time = time.time()
offset = response.offset

new_time = system_time + offset
time.clock_settime(time.CLOCK_REALTIME, new_time)
print('System clock synchronized with time.windows.com')"""

print(bin.fetch_balance())


def get_bid_ask():
    """get the actual first bid and first ask from the order book

    Returns:
        sym_bid: actual highest bid for the selected market
        sym_ask: actual lowest ask for the selected market
    """
    sym_bin_book = bin.fetch_order_book(gma.market)
    sym_bid = sym_bin_book["bids"][0][0]
    sym_ask = sym_bin_book["asks"][0][0]
    print(f"the best bid:{sym_bid} and the best ask:{sym_ask}")

    return sym_bid, sym_ask

sym_bid, sym_ask = get_bid_ask() # exctraction of the eth bid and ask from the definition function

def get_asks_book():
    """get the list of asks for selected market

    Returns:
        sym_asks: list of asks for the selected market
    """
    syms_bin_book = bin.fetch_order_book(gma.market)
    sym_asks = syms_bin_book["asks"]
    return sym_asks

def get_bids_book():
    """get the list of bids for selected market

    Returns:
        sym_bids: list of bids for the selected market
    """
    syms_bin_book = bin.fetch_order_book(gma.market)
    sym_bids = syms_bin_book["bids"]
    return sym_bids

#-------- Initialization --------------------------------
symbol = gma.market
pos_size = gma.contract_size #get_bid_ask () [0] #position size is in ETH,BTC etc 
market_info = bin.fetch_ticker(symbol)
min_inc = float(market_info["info"]["priceIncrement"]) #minimal size of increment or fissionablity of the coin/token
close_all = bin.cancel_all_orders(symbol)


# ------------ min_increase on asset calc ----------------

def sym_ask_min (min_inc,market):
    """check whenever is a space between sym_ask and sym_bid to place minimal order size by decrement.
    if so, round the order and lower it by min_inc

    Args:
        min_inc (float): minimum size we can decrease on the market
        market (str): market selection i.e. SOL_USDC

    Returns:
        float: returns minimal value which can be set as ask
    """
    sym_bin_book = bin.fetch_order_book(market)
    sym_ask = sym_bin_book["asks"][0][0]
    sym_bid = sym_bin_book["bids"][0][0]
    if (sym_ask - sym_bid) > min_inc:
        return round(float(sym_ask - min_inc),6)
    else:
        return round(float(sym_ask),6)

def sym_bid_min (min_inc, market):
    """check whenever is a space between sym_bid and sym_ask to place minimal order size by increment.
    if so, round the order and lower it by min_inc

    Args:
        min_inc (float): minimum size we can increase on the market
        market (str): market selection i.e. SOL_USDC

    Returns:
        float: returns maximum value which can be set as bud
    """
    sym_bin_book = bin.fetch_order_book(market)
    sym_bid = sym_bin_book["bids"][0][0]
    sym_ask = sym_bin_book["asks"][0][0]
    if (sym_ask - sym_bid) > min_inc:
        return round(float((sym_bid + min_inc)),6)
    else:
        return round(float(sym_bid),6)


def nakupni_cena_oo (input_cena, co_vratit):
    """_summary_

    Args:
        input_cena (float): 
        co_vratit (str): func. works with short or long variant

    Returns:
        _type_: _description_
    """
    try:
        if input_cena:
            return float(bin.fetch_open_orders()[0]["info"][co_vratit])
    except:
        pass
    if co_vratit == "short":
        return 0
    elif co_vratit == "long":
        return 1000000
    else:
        return 0

def bin_OO():
    side = bin.fetch_open_orders()[0]["info"]["side"]
    size = bin.fetch_open_orders()[0]["info"]["size"]
    return side, size

def nakupni_cena (input_cena, co_vratit):
    if input_cena:
        return float(bin.fetch_positions()[0]["info"][co_vratit])
    else:
        return 0

testing_coef = 0.5


column_names = ['id', 'clientOrderId', 'datetime', 'timestamp', 'lastTradeTimestamp', 'status',
                'symbol', 'type', 'timeInForce', 'side', 'price', 'average', 'amount', 'filled',
                'remaining', 'cost', 'trades', 'fee', 'info']
df = pd.DataFrame(column_names)





#------------ OPen SHORT ------------------------------------------------


"""def new_open_short(market,contract_size,df):
    loop = 0

    while True:
        loop += 1
        print("loop counter : " + str(loop))
        try:
            get_open_position = bin.fetch_positions()
            mam_short_pozici = float(get_open_position[0]["info"]["netSize"])  
            myShortbid = float(contract_size*testing_coef)
            if nakupni_cena_oo(bin.fetch_open_orders(),"price") < sym_ask_min(min_inc,market): # aktuální nakupní/prodejní cena open orderu < nejmenší možný příhoz  
                bin.cancel_all_orders(market)# zahoď obj.
                new_order = bin.create_order(market,"limit","sell", amount = myShortbid, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})# get recently opened order a appendi jeho hodnotu a value do np.listu
                # neotvírej další pozici v případě, že máš v listu více než 3 hodnoty
                df = df.append(new_order, ignore_index=True)
            elif mam_short_pozici < 0 and (mam_short_pozici > (-(myShortbid))) and (mam_short_pozici > sym_ask_min(-min_inc,market)):
                mypartial_bid = mam_short_pozici + myShortbid
                print("dohazuji partial : "+ str(mypartial_bid))
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","sell", amount = mypartial_bid, price = (sym_ask_min(min_inc,market)), params={'postOnly': True}) # mam short pozici < 0 a tata je menší než nejmenší možná příhoz
                df = df.append(new_order, ignore_index=True)
        except:
            print("Something went wrong")
        return df"""


def open_short(market,contract_size,short_counter):
    loop = 0
    pomocna_pozice = float(bin.fetch_positions()[0]["info"]["netSize"]) 
   
    while True:
        loop += 1
        print("loop counter : " + str(loop))
        try:
            mam_short_pozici = float(bin.fetch_positions()[0]["info"]["netSize"]) 
            myShortbid = contract_size*testing_coef
            mam_druhou_pozici = mam_short_pozici - pomocna_pozice
            print(f"velikost mojí short pozice je: {mam_short_pozici} a short_counter je : {short_counter}")
            
            
           
            if  nakupni_cena_oo(bin.fetch_open_orders(),"price") < sym_ask_min(min_inc,market) and (mam_short_pozici == 0 and  short_counter < 1) or (mam_druhou_pozici == 0 and short_counter <2):
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","sell", amount = myShortbid, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})
                print(str(nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " < " + str(round(float((sym_ask_min(min_inc,market))),4)))
                print("nový bid, přehazuji na: " + str(sym_ask_min(min_inc,market)))       
            elif mam_short_pozici < 0 and (mam_short_pozici > (-(myShortbid))) and (mam_short_pozici > sym_ask_min(-min_inc,market)):
                mypartial_bid = mam_short_pozici + myShortbid
                print("dohazuji partial : "+ str(mypartial_bid))
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","sell", amount = mypartial_bid, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})
            #občas se stane že tam zůstane viset obj a toto by ji mělo chytit a shodit aby se bot nezasekl
            """
            elif loop > 7 and mam_short_pozici < 0:
                bin.cancel_all_orders(market)
                loop = 0
                print("shazuji případnou zaseklou obj.")
            """
            
            
        except Exception as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            print (chyba)
            print("Line number", line_number)
            pass
        
        
        if mam_short_pozici < 0.0 and short_counter == 0 :
            bin.cancel_all_orders(market)
            print("skáču ven a short by měl být otevřen")
            short_counter +=1
            print(f"velikost mojí short pozice je: {mam_short_pozici} a short_counter je : {short_counter}")
            return short_counter
        
        if mam_druhou_pozici < 0 and short_counter == 1:
            bin.cancel_all_orders(market)
            print("skáču ven a 2.short by měl být otevřen")
            short_counter +=1
            print(f"velikost mojí short pozice je: {mam_short_pozici} a short_counter je : {short_counter}")
            return short_counter 
        
        if short_counter == 2:
            bin.cancel_all_orders(market)
            print("Neotvírám další Short, mám cap 2")
            return short_counter 
        
        if mam_short_pozici > 0:
            print("něco je blbě mám otevřený long")
            bin.cancel_all_orders(market)
            return short_counter

#------------ Close SHORT Code ------------------------------------------------  

def close_short(market,short_counter):
    loop = 0
    try:
        bin.create_order(market,"limit","buy", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_bid_min(min_inc,market), params={'reduceOnly': True})
    except:
        print("nešlo zredukovat SHORT")
    while True:
        loop +=1
        print("loop counter : " + str(loop))
        otevrene_pozice = bin.fetch_positions()
        mam_short_pozici = float(otevrene_pozice[0]["info"]["netSize"])
        print("velikost mojí short pozice je: " + str(mam_short_pozici))
        try:
            if  nakupni_cena_oo(bin.fetch_open_orders(),"price") < (sym_bid_min(min_inc,market)) and mam_short_pozici < 0:
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","buy", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_bid_min(min_inc,market), params={'reduceOnly': True})
                print(str( nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " je nákupka a nový bid, přehazuji na: " + str(sym_bid_min(min_inc,market)))  
            elif mam_short_pozici > 0:
                print("close měl být na long")
                return short_counter
            #občas se stane že tam zůstane viset obj a toto by ji mělo chytit a shodit aby se bot nezasekl
            """
            elif loop > 7 and mam_short_pozici < 0 :
                bin.cancel_all_orders(market)
                loop = 0
                print("shazuji případnou zaseklou obj.")
            """
        except Exception as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            print (chyba)
            print("Line number", line_number)
            return short_counter
        if mam_short_pozici == 0.0:
            bin.cancel_all_orders(market)
            print("skáču ven a short by měl být zavřen")
            short_counter = 0
            return short_counter
            break

#------------ Open LONG Code ----------------------------------------------------------------     
#     
def open_long(market, contract_size,long_counter):
    loop = 0
    pomocna_pozice = float(bin.fetch_positions()[0]["info"]["netSize"]) 
    while True:
        loop += 1
        print("loop counter : " + str(loop))
        try:
            get_open_position = bin.fetch_positions()
            mam_long_pozici = float(get_open_position[0]["info"]["netSize"]) 
            myLongbid = contract_size*testing_coef
            mam_druhou_pozici = mam_long_pozici - pomocna_pozice
            print(f"velikost mojí long pozice je: {mam_long_pozici} a long_counter je : {long_counter}")
            
            if  nakupni_cena_oo(bin.fetch_open_orders(),"price") < sym_bid_min(min_inc,market) and (mam_long_pozici == 0 and  long_counter < 1) or (mam_druhou_pozici == 0 and long_counter <2):
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","buy", amount = myLongbid, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})
                print(str(nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " < " + str(round(float((sym_bid_min(min_inc,market))),4)))
                print("nový bid, přehazuji na: " + str(sym_bid_min(min_inc,market)))       
            elif mam_long_pozici > 0 and (mam_long_pozici < myLongbid) and (mam_long_pozici > sym_bid_min(min_inc,market)):
                mypartial_bid = myLongbid - mam_long_pozici
                print("dohazuji partial : "+ str(mypartial_bid))
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","buy", amount = mypartial_bid, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})
            #občas se stane že tam zůstane viset obj a toto by ji mělo chytit a shodit aby se bot nezasekl
            """elif loop > 7 and mam_long_pozici == 0:
                bin.cancel_all_orders(market)
                loop = 0
                print("shazuji případnou zaseklou obj.")
            """
        except Exception as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info()
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            print (chyba)
            print("Line number", line_number)
            return long_counter
           
        if mam_long_pozici > 0.0 and long_counter == 0 :
            bin.cancel_all_orders(market)
            print("skáču ven a long by měl být otevřen")
            long_counter +=1
            print(f"velikost mojí long pozice je: {mam_long_pozici} a long_counter je : {long_counter}")
            return long_counter
        
        if mam_druhou_pozici > 0 and long_counter == 1:
            bin.cancel_all_orders(market)
            print("skáču ven a 2.long by měl být otevřen")
            long_counter +=1
            print(f"velikost mojí long pozice je: {mam_long_pozici} a long_counter je : {long_counter}")
            return long_counter 
        
        if long_counter == 2:
            bin.cancel_all_orders(market)
            print("Neotvírám další long, mám cap 2")
            return long_counter  
        
        if mam_long_pozici < 0:
            print("něco je blbě mám otevřený short")
            bin.cancel_all_orders(market)
            return long_counter

#------------ Close LONG Code -------------------------------------------------------------      
def close_long(market, long_counter):
    loop = 0
    try:
        bin.create_order(market,"limit","sell", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_ask_min(min_inc,market), params={'reduceOnly': True})
    except:
        print("nešlo zredukovat LONG")
    while True:
        loop +=1
        print("loop counter : " + str(loop))
        otevrene_pozice = bin.fetch_positions()
        mam_long_pozici = float(otevrene_pozice[0]["info"]["netSize"])
        print("velikost mojí long pozice je: " + str(mam_long_pozici))
        try:
            
            if  nakupni_cena_oo(bin.fetch_open_orders(),"price") > sym_ask_min(min_inc,market) and mam_long_pozici > 0:
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","sell", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_ask_min(min_inc,market), params={'reduceOnly': True})
                print(str( nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " je nákupka a nový bid, přehazuji na: " + str(sym_ask_min(min_inc,market)))  
            elif mam_long_pozici < 0:
                print("close měl být na short")
                return long_counter
            #občas se stane že tam zůstane viset obj a toto by ji mělo chytit a shodit aby se bot nezasekl
            """
            elif loop > 7 and mam_long_pozici > 0:
                bin.cancel_all_orders(market)
                loop = 0
                print("shazuji případnou zaseklou obj.")
            """
            

        except Exception as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            print (chyba)
            print("Line number", line_number)
            pass
        
        if mam_long_pozici == 0.0:
            bin.cancel_all_orders(market)
            long_counter = 0
            print("skáču ven a long by měl být zavřen")
            return long_counter
            break

long_counter = 0
short_counter = 0
           
#-------------------------------------------- ENGINE -----------------------------------------------     
def automated_bot_engine():
    long_counter = 0
    short_counter = 0
    print(f"Long counter : {long_counter} a Short counter: {short_counter}")
    while True:
        try:
            print(" inicializace automatického bota")
            vstup = "vstup je nothing"    
            to_do, market, contract_size, bylo_eof = gma.signal_awaiter_system()
            vstup = to_do
            print(f"Long counter : {long_counter} a Short counter: {short_counter}")
            print(vstup)    
                    
            if vstup == "ENTER-LONG":
                try:
                    long_counter = open_long(market, contract_size,long_counter)
                    print("Vstupuji do LONG pozice")
                    print(f"Long counter : {long_counter} a Short counter: {short_counter}") 
                except Exception as chyba_v_longu:
                    print(chyba_v_longu)

            elif vstup == "EXIT-LONG":
                try:
                    if float(bin.fetch_positions()[0]["info"]["netSize"]) > 0:
                        long_counter = close_long(market,long_counter)
                        print("vystupuji z Long pozicí")
                        print(f"Long counter : {long_counter} a Short counter: {short_counter}")                  

                except Exception as chyba_v_longu:
                    print(chyba_v_longu)
                    break


            elif vstup == "ENTER-SHORT" :
                try:
                    short_counter = open_short(market, contract_size,short_counter)
                    print("Vstupuji do SHORT pozice")
                    print(f"Long counter : {long_counter} a Short counter: {short_counter}")
                except Exception as chyba_v_shortu:
                    print(chyba_v_shortu)

            elif vstup == "EXIT-SHORT":
                try:
                    if float(bin.fetch_positions()[0]["info"]["netSize"]) < 0:
                        short_counter = close_short(market,short_counter)
                        print("vystupuji z SHORT pozicí")
                        print(f"Long counter : {long_counter} a Short counter: {short_counter}")                  
                except Exception as chyba_v_shortu:
                    print(chyba_v_shortu)
                    break

            # Zresetuje se long_short counter a pozavírají se pozice protože countery nekorespondují s pozicemi            
            elif bin.fetch_positions()[0]["info"]["netSize"] == 0 and (long_counter or short_counter != 0) :
                try:
                    bin.create_order(market,"limit","buy", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_bid_min(min_inc,market), params={'reduceOnly': True})
                    bin.create_order(market,"limit","sell", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_bid_min(min_inc,market), params={'reduceOnly': True})
                    long_counter = 0
                    short_counter = 0
                    print("countery zresetovány")
                except:
                    pass

            elif chyba_v_longu or chyba_v_shortu:
                print("chyba v longu nebo shortu, vyskakuji ven")
                bin.cancel_all_orders(market)
                close_long(market)
                close_short(market)
                break
            elif keyboard.on_press_key('alt+p'):  # if key 'q' is pressed 
                print('Vyskakuji manuálně do main menu')
                break  # finishing the loop
        except Exception or OSError or EOFError as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            print(exception_type)
            print(exception_object)
            print("problém se vyskytl v MOTORU")
            print (chyba)
            print("Line number", line_number)
            automated_bot_engine()
            break 


#--------------------------------------- BOT v.2 bez counteru, pouze LONG --> SELL a vice versa-----------------------------------------------------------

def automated_bot_engine2():
    velikost_pozice = float(bin.fetch_positions()[0]["info"]["netSize"])
    while True:
        print(" inicializace automatického bota")
        vstup = "vstup je nothing"    
        to_do, market, contract_size, bylo_eof = gma.signal_awaiter_system()
        vstup = to_do
        print(vstup)   
        try:
            if vstup == "ENTER-LONG":
                while velikost_pozice <= 0:
                    if  nakupni_cena_oo(bin.fetch_open_orders(),"price") < (sym_bid_min(min_inc,market)):
                        bin.cancel_all_orders(market)
                        bin.create_order(market,"limit","buy", amount = contract_size, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})
                        print(str(nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " < " + str(sym_bid_min(min_inc,market)))
                        print("nový bid, přehazuji na: " + str(sym_bid_min(min_inc,market)))       
                    elif velikost_pozice > 0 and (velikost_pozice < contract_size) and (velikost_pozice > sym_bid_min(min_inc,market)):
                        mypartial_bid = contract_size - velikost_pozice
                        print("dohazuji partial : "+ str(mypartial_bid))
                        bin.cancel_all_orders(market)
                        bin.create_order(market,"limit","buy", amount = mypartial_bid, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})
            
            elif vstup == "EXIT-LONG":
                try:
                    bin.create_order(market,"limit","sell", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_ask_min(min_inc,market), params={'reduceOnly': True})
                except:
                    print("nešlo zredukovat LONG")
                while velikost_pozice != 0:
                    if  nakupni_cena_oo(bin.fetch_open_orders(),"price") > sym_ask_min(min_inc,market) :
                        bin.cancel_all_orders(market)
                        bin.create_order(market,"limit","sell", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_ask_min(min_inc,market), params={'reduceOnly': True})
                        print(str( nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " je nákupka a nový bid, přehazuji na: " + str(sym_ask_min(min_inc,market)))  
                    elif velikost_pozice < 0:
                        print("close měl být na short")
                        vstup = "EXIT-SHORT"
                        return vstup
            
            elif vstup == "ENTER-SHORT" :
                while velikost_pozice >= 0:
                    if  nakupni_cena_oo(bin.fetch_open_orders(),"price") < round(float((sym_ask_min(min_inc,market))),4) :
                        bin.cancel_all_orders(market)
                        bin.create_order(market,"limit","sell", amount = contract_size, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})
                        print(str(nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " < " + str(sym_ask_min(min_inc,market)))
                        print("nový bid, přehazuji na: " + str(sym_ask_min(min_inc,market)))       
                    elif velikost_pozice < 0 and (velikost_pozice > (-(contract_size))) and (velikost_pozice > sym_ask_min(-min_inc,market)):
                        mypartial_bid = velikost_pozice + contract_size
                        print("dohazuji partial : "+ str(mypartial_bid))
                        bin.cancel_all_orders(market)
                        bin.create_order(market,"limit","sell", amount = mypartial_bid, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})
            
            elif vstup == "EXIT-SHORT":
                try:
                    bin.create_order(market,"limit","buy", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_bid_min(min_inc,market), params={'reduceOnly': True})
                except:
                    print("nešlo zredukovat SHORT")
                while velikost_pozice != 0:
                    if  nakupni_cena_oo(bin.fetch_open_orders(),"price") < sym_bid_min(min_inc,market):
                        bin.cancel_all_orders(market)
                        bin.create_order(market,"limit","buy", amount = nakupni_cena(bin.fetch_positions(),"size"), price = sym_bid_min(min_inc,market), params={'reduceOnly': True})
                        print(str( nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " je nákupka a nový bid, přehazuji na: " + str(sym_bid_min(min_inc,market)))  
                    elif velikost_pozice > 0:
                        print("close měl být na long")
                        vstup = "EXIT-LONG"
                        return vstup
 
        except Exception or OSError or EOFError as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            print(exception_type)
            print(exception_object)
            print("problém se vyskytl v MOTORU")
            print (chyba)
            print("Line number", line_number)
            break 

#----------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------- BOT v.3 bez counteru a EXITU, LONG to short-----------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------

def open_switch_order(market, type ,side, amount):
    #v tomto případě se nedá hýbat s params ( na reduce only např.) a se samotnou cenou
    #plná verze ... bin.create_order(market,"limit","buy", amount = contract_size, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})
    test_amount = amount * testing_coef
    if side == "buy":
        order_id = bin.create_order(market ,type ,side , test_amount, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})["info"]["id"]
        return order_id
    elif side == "sell":
        order_id = bin.create_order(market ,type ,side , test_amount, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})["info"]["id"]
        return order_id

def close_switch_order(id):
    # pokud si dotáhnu z create orderu ID tak jej můžu i přímo ukončit
    id = bin.fetch_order(id) 
    if id != "closed":
        bin.cancel_order(id)

def open_order_check(co_vratit):
    # Pokud není žádný order tak vrátí 0. Pokud bych chtěl vrátit třeba "není order" tak to spadne na porovnání str a float
    try:
        order_info = bin.fetch_open_orders()[0]["info"][co_vratit]
        float(order_info)
        return order_info
    except:
        return 0.0000

def opened_position_size():
    #Vrací aktuální otevřenou LONG/SHORT velikost pozice 
    net_size = float(bin.fetch_positions()[0]["info"]["netSize"])
    return net_size

def open_switch_long(market,contract_size):
    filled_size = bin.create_order(market,"limit","buy", amount = contract_size, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})["info"]["filledSize"]
    loop = 0
    while True:
        try:
            loop +=1
            print(loop)
            print(str(nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " < " + str(sym_bid_min(min_inc,market)) +" ?")
            if opened_position_size() > 0.0:
                velikost_pozice = opened_position_size()
                print(f"Přeskočil jsem z Shortu do Longu: {velikost_pozice} > 0" )
                bin.cancel_all_orders(market)
                break 

            elif  nakupni_cena_oo(bin.fetch_open_orders(),"price") <= sym_bid_min(min_inc,market):
                #musí být <= protože 0 je zde zastoupena jako "Nemám žádný open order"
                bin.cancel_all_orders(market)
                filled_size = bin.create_order(market,"limit","buy", amount = contract_size, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})["info"]["filledSize"]
                #open_switch_order(market,"limit","buy",contract_size)
                print(str(nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " < " + str(sym_bid_min(min_inc,market)))
                print("nový bid, přehazuji na: " + str(sym_bid_min(min_inc,market)))    

            elif loop > 10:
                bin.cancel_all_orders()
                loop = 0
                print("shazuji všechny obj.")    
                open_switch_long(market,contract_size)

            elif (contract_size - filled_size) != 0 :
                bin.cancel_all_orders()
                rem_size = contract_size - filled_size
                filled_size = bin.create_order(market,"limit","buy", amount = rem_size, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})["info"]["filledSize"]
                # možná bude stále tahat špatná data. Pak je nutné si SAVEnout ID a přes něj se pak zeptat třeba za sekundu na Filled/remainingSize ... 
                # nebo si natáhnout poslední filled obj ?
                #bin.fetch_my_trades()
            """
            elif velikost_pozice > 0 and (velikost_pozice < contract_size) and (velikost_pozice > sym_bid_min(min_inc,market)):
                mypartial_bid = contract_size - velikost_pozice
                print("dohazuji partial : "+ str(mypartial_bid))
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","buy", amount = mypartial_bid, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})
            """
        except Exception as chyba:
            print(chyba)
            pass
    bin.cancel_all_orders()


def open_switch_short(market,contract_size):
    filled_size = bin.create_order(market,"limit","sell", amount = contract_size, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})["info"]["filledSize"]
    loop = 0
    while True:
        try:
            loop += 1
            print(loop)
            print(str(nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " <= " + str(sym_ask_min(min_inc,market))+" ?")
            if opened_position_size() < 0.0 :
                velikost_pozice = opened_position_size()
                print(f"Přeskočil jsem z Longu do Shortu: {velikost_pozice} < 0" )
                bin.cancel_all_orders(market)
                break  
            elif  nakupni_cena_oo(bin.fetch_open_orders(),"price") <= sym_ask_min(min_inc,market):
                bin.cancel_all_orders(market)
                filled_size = bin.create_order(market,"limit","sell", amount = contract_size, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})["info"]["filledSize"]
                print(str(nakupni_cena_oo(bin.fetch_open_orders(),"price")) + " < " + str(sym_ask_min(min_inc,market)))
                print("nový bid, přehazuji na: " + str(sym_ask_min(min_inc,market))) 

            elif loop > 10:
                bin.cancel_all_orders()
                loop = 0
                print("shazuji všechny obj.")    
                open_switch_long(market,contract_size)  

            elif (contract_size - filled_size) != 0 :
                bin.cancel_all_orders()
                rem_size = contract_size - filled_size
                filled_size = bin.create_order(market,"limit","buy", amount = rem_size, price = (sym_bid_min(min_inc,market)), params={'postOnly': True})["info"]["filledSize"]
            """         
            elif velikost_pozice < 0 and (velikost_pozice > (-(contract_size))) and (velikost_pozice > sym_ask_min(-min_inc,market)):
                mypartial_bid = velikost_pozice + contract_size
                print("dohazuji partial : "+ str(mypartial_bid))
                bin.cancel_all_orders(market)
                bin.create_order(market,"limit","sell", amount = mypartial_bid, price = (sym_ask_min(min_inc,market)), params={'postOnly': True})
            """
        except Exception as chyba:
            print(chyba)
            pass
    bin.cancel_all_orders()



def automated_bot_engine3():
    
        test_contract_size = input("Initial contract size is: ")
        test_contract_size = float(test_contract_size) * testing_coef 
        vstup2 = input("Which side to open LONG or SHORT ? ")
        if vstup2 == "long":
            open_switch_long(symbol,test_contract_size)

        elif vstup2 == "short" :
            open_switch_short(symbol,test_contract_size)
        else:
            print("špatně zadané, spouštím znova")
            automated_bot_engine3()

        while True:
            try:
                print(" inicializace automatického bota bez EXITU v 3.0")
                vstup = "vstup je nothing"    
                to_do, market, contract_size, bylo_eof = gma.signal_awaiter_system()
                test2_contract_size = contract_size * testing_coef
                vstup = to_do
                opened_position_size()
                print(vstup) 

                if vstup == "ENTER-LONG":
                    open_switch_long(market,test2_contract_size)     
                
                elif vstup == "ENTER-SHORT":
                    open_switch_short(market,test2_contract_size)

                elif keyboard.is_pressed('alt+p'):  # if key 'ctrl+q' is pressed 
                    print('Vyskakuji manuálně do main menu')
                    break  # finishing the loop

            except Exception or OSError or EOFError as chyba:
                exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
                #filename = exception_traceback.tb_frame.f_code.co_filename
                line_number = exception_traceback.tb_lineno
                print(exception_type)
                print(exception_object)
                print("problém se vyskytl v MOTORU")
                print (chyba)
                print("Line number", line_number)
                break
            
                
#----------------------------------------------------------- MAIN MENU ------------------------------------------------------------------------                   
#----------------------------------------------------------------------------------------------------------------------------------------------
while True:  
    print("Main menu initialized")
    vstup2 = input()
    if vstup2 == "search":
        automated_bot_engine()
    
    elif vstup2 =="search2":   
        automated_bot_engine2()
        
    elif vstup2 =="search3":   
        automated_bot_engine3()

    elif vstup2 =="open switch short":
        contract = input("Zadej size of the deal: ")
        contract = float(contract)
        open_switch_short(symbol,contract)
    
    elif vstup2 =="open switch long":
        contract = input("Zadej size of the deal: ")
        contract = float(contract)
        open_switch_long(symbol,contract)

    elif vstup2 == "open short" :
        short_counter = open_short(gma.market, gma.contract_size, short_counter)        

    elif vstup2 == "close short":
        short_counter = close_short(gma.market,short_counter)
        
    elif vstup2 == "open long":
        long_counter = open_long(gma.market, gma.contract_size,long_counter)
   
    elif vstup2 == "close long":
        long_counter = close_long(gma.market,long_counter)

    elif vstup2 == "counters":
        try:
            print(f"Long counter je: {long_counter} a Short counter je: {short_counter}")
        except:
            pass
    elif vstup2 == "test":
        print(nakupni_cena_oo(bin.fetch_open_orders(),"price",))
    elif vstup2 == "test2":
        print(nakupni_cena_oo(bin.fetch_open_orders(),"long",))
    elif vstup2 == "test3":
        print(nakupni_cena_oo(bin.fetch_open_orders(),"short",))

    elif vstup2 == "open orders":
        try:
            print(bin.fetch_open_orders())# [0]["info"]["price"])
        except:
            pass

    elif vstup2 == "open positions":
        try:
            print(bin.fetch_positions())# [0]["info"]["side"])
        except Exception as chyba:
            print(chyba)
            pass
    

    elif vstup2 == "end":
        print("vypínám bota")
        break

    elif vstup2 == "bids":
        print(get_bids_book())

    elif vstup2 == "asks":
        print(get_asks_book())    
   
    elif vstup2 == "mail":
        print(gma.get_alert())
    
    elif vstup2 == "market info":
        print(bin.fetch_ticker(symbol)["info"])#["priceIncrement"])
        
    elif vstup2 == "test2":
        try:
            print(sym_ask_min(min_inc,symbol))
        except Exception as chyba:
            print(chyba)
    
    elif vstup2 == "testing":
        gma.signal_awaiter_system()
        
    elif vstup2 == "trady":
        print(bin.fetch_trades(symbol))

    elif vstup2 == "pozice":
        velikost_pozice = float(bin.fetch_positions()[0]["info"]["netSize"])
        print(velikost_pozice)
    elif vstup2 == "signal":
        print(str(gma.messages))
        
    
    elif vstup2 == "conn check":
        print(gma.login("Inbox"))
        

    elif vstup2 == "test check":
        print(tst2.avreg(cfg.my_mail_config["user"],cfg.my_mail_config["password"]))

    else:
        print ("pravděpodobně moc orderu nebo jiná chyba")
        pass
  

    


            



"""    
#------------ LONG/SHORT UNI Code ----------------    
def open_close_long_short(open_close, side, parameters ):
    loop = 0

    while True:
        loop +=1
        print("loop counter : " + str(loop))
        get_open_position = bin.fetch_positions()
        mam_pozici = float(get_open_position[0]["info"]["netSize"])
        nakupni_cena_openOrderu = nakupni_cena_oo(bin.fetch_open_orders())
        my_bid = gma.contract_size * 0.1
        get_ob = bin.fetch_order_book(market)
        sym_ask = float(get_ob["asks"][0][0]) 
        sym_bid = float(get_ob["bids"][0][0]) 
        print("velikost mojí pozice je: " + str(mam_pozici))
        try:
            if nakupni_cena_openOrderu < round(float((sym_ask)),4):
                if vstup == "open short" and mam_pozici == 0:
                    close_all()
                    bin.create_order(market,"limit",side, amount = my_bid, price = (sym_ask-min_inc), params=parameters)
                    print(str(nakupni_cena_openOrderu) + " < " + str(round(float((sym_ask-min_inc)),4)))
                    print("nový bid, přehazuji na: " + str(sym_ask-min_inc))  
        except Exception as chyba:
            print(chyba)
"""

