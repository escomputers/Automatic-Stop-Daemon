#!/usr/bin/env python3.9

from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
import unicorn_fy 
from unicorn_binance_rest_api.manager import BinanceRestApiManager

import time as tempo
from decimal import Decimal
import logging, pytz, threading, os, smtplib, ssl
from datetime import datetime, time, timedelta

from binance.spot import Spot as Client
from binance.error import ClientError

from getpass import getpass
from tabulate import tabulate

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, FileSystemLoader

# LOG FILE
logging.getLogger('unicorn_binance_websocket_api')
logging.basicConfig(level=logging.INFO,
                    filename=os.path.basename(__file__) + '.log',
                    format='{asctime} [{levelname:8}] {process} {thread} {module}: {message}',
                    style='{')

# reset all inputs
def reset_inputs():
    for element in dir():
        if element[0:2] != "__":
            del globals()[element]
    del element
     
# get LAST PRICE via rest api
def get_last_price(unicorn_fied_stream_data):
    ubra = BinanceRestApiManager(api_key, api_secret, exchange="binance.com")
    last_symbol_data = ubra.get_ticker(symbol=unicorn_fied_stream_data['symbol'])
    last_price = float(last_symbol_data['lastPrice'])
    return last_price

# PLACE ORDER
def place_new_order(unicorn_fied_stream_data):
    
    #order_price = float(unicorn_fied_stream_data['order_price'])
    order_price = 19556.02
    
    # OCO order
    if 'y' in is_oco.lower():

        # TAKE PROFIT price
        profit_price = round((order_price + round(((order_price / 100) * profit_percentage), 8)), 2) 

        # STOP LOSS price 
        stop_loss_price_oco = round((order_price - round(((order_price / 100) * stop_loss_oco_percentage), 8)), 2)

        # LIMIT PRICE    
        stop_loss_limit_price_oco = round((order_price - round(((order_price / 100) * stop_loss_limit_oco_percentage), 8)), 2)
        
        # new order
        params = {
            'symbol': unicorn_fied_stream_data['symbol'],
            'side': 'SELL',
            'stopLimitTimeInForce': 'GTC',                            
            #'quantity': unicorn_fied_stream_data['order_quantity'],   
            'quantity': 0.00119,
            'price': str(profit_price),
            'stopPrice': str(stop_loss_price_oco),                    
            'stopLimitPrice': str(stop_loss_limit_price_oco)           
            
        }
        
        client = Client(api_key, api_secret, base_url='https://api.binance.com')
        
        '''
        OCO SELL rule = Limit Price > Last Price > Stop Price
        OCO BUY rule  = Limit Price < Last Price < Stop Price
        '''
        
        # get LAST SYMBOL PRICE
        last_price = get_last_price(unicorn_fied_stream_data)
        
        # if stop and limit prices respect OCO rules, place orders
        if last_price > stop_loss_price_oco and last_price < stop_loss_limit_price_oco:
        
            try:
                response = client.new_oco_order(**params)                  
                logging.info(response)

            except ClientError as error:
                logging.info(response)
                logging.error(
                    'Found error. status: {}, error code: {}, error message: {}'.format(
                        error.status_code, error.error_code, error.error_message
                    )
                )
        else:
            print(' [ERROR] The relationship of the prices for the orders is not correct. \n You must follow this OCO SELL rule = Limit Price > Last Price > Stop Price')
            
        
    # non OCO orders
    else:
        # TAKE PROFIT order
        if 'n' in is_stop_loss_order:
        
            # LIMIT PROFIT price
            limit_profit_price = round((order_price + round(((order_price / 100) * limit_profit_percentage), 8)), 2) 
            
            # STOP PROFIT price
            stop_price = round((order_price + round(((order_price / 100) * stop_profit_percentage), 8)), 2) 
            
            # new order
            params = {
                'symbol': unicorn_fied_stream_data['symbol'],
                'side': 'SELL',
                'type': 'TAKE_PROFIT_LIMIT',                            
                'timeInForce': 'GTC',                                    
                #'quantity': unicorn_fied_stream_data['order_quantity'],   
                'quantity': 0.00119,
                'price': str(limit_profit_price),
                'stopPrice': str(stop_price),                     
                
            }
            
            client = Client(api_key, api_secret, base_url='https://api.binance.com')
             
            try:
                response = client.new_order(**params)               
                mail_notification(response)
                
            except ClientError as error:
                response = logging.error(
                    'Found error. status: {}, error code: {}, error message: {}'.format(
                        error.status_code, error.error_code, error.error_message
                    )
                )
                mail_notification(response)
                
        # STOP LOSS order
        else:
            
            # STOP LOSS LIMIT price
            limit_loss_price = round((order_price - round(((order_price / 100) * limit_loss_percentage), 8)), 2) 
            
            # STOP LOSS price
            stop_loss_price = round((order_price - round(((order_price / 100) * stop_loss_percentage), 8)), 2) 
            
            # new order
            params = {
                'symbol': unicorn_fied_stream_data['symbol'],
                'side': 'SELL',
                'type': 'STOP_LOSS_LIMIT',                            
                'timeInForce': 'GTC',                                    
                #'quantity': unicorn_fied_stream_data['order_quantity'],   
                'quantity': 0.00119,
                'price': str(limit_loss_price),
                'stopPrice': str(stop_loss_price),                     
                
            }
            
            client = Client(api_key, api_secret, base_url='https://api.binance.com')
             
            try:
                response = client.new_order(**params)               
                logging.info(response)

            except ClientError as error:
                logging.info(response)
                logging.error(
                    'Found error. status: {}, error code: {}, error message: {}'.format(
                        error.status_code, error.error_code, error.error_message
                    )
                )    
    
# CHECK FOR TRADES
def print_stream_data_from_stream_buffer(binance_websocket_api_manager):
    
    while True:
        if binance_websocket_api_manager.is_manager_stopping():
            exit(0)
        oldest_stream_data_from_stream_buffer = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()
        if oldest_stream_data_from_stream_buffer is False:
            tempo.sleep(0.01)
        else:
            
            #convert data stream to python dictionary
            unicornfy = unicorn_fy.UnicornFy()
            unicorn_fied_stream_data = unicornfy.binance_com_websocket(oldest_stream_data_from_stream_buffer)
            
            #dictionary
            try:
                order_status = unicorn_fied_stream_data['current_order_status']
                if order_status == 'CANCELED':
                        place_new_order(unicorn_fied_stream_data)
            except KeyError:
                continue
    
# CONNECT TO BINANCE.COM
def check_filled_orders():
    # create instances of BinanceWebSocketApiManager
    ubwa_com = BinanceWebSocketApiManager(exchange='binance.com')

    # create the userData streams
    user_stream_id = ubwa_com.create_stream('arr', '!userData', api_key=api_key, api_secret=api_secret)

    # start a worker process to move the received stream_data from the stream_buffer to a print function
    worker_thread = threading.Thread(target=print_stream_data_from_stream_buffer, args=(ubwa_com,))
      
    worker_thread.start()

    # monitor the streams
    while True:
        ubwa_com.print_stream_info(user_stream_id)

        #set here refresh interval
        tempo.sleep(refresh_interval) 

# CHECK TIME
def check_time():
    # every 5 secs
    threading.Timer(refresh_interval, check_time).start()

    # get time zone of specified location
    tmzone = pytz.timezone(user_timezone)

    # change current time accordingly
    now = (datetime.now(tmzone))
       
    # check if it's time to work or not
    if now.time() >= user_start_time and now.time() <= user_end_time:
        # yes
        check_filled_orders()
    else:
        check_filled_orders()

# VALIDATION 
def validate_working_interval(input):
    try:
        input = int(input)
        if input >= 1 and input <= 24:
            return input
        else:
            print(' [ERROR] insert a valid value between 1 and 24')
    except ValueError:
        print(' [ERROR] insert only numbers')
        
def validate_minutes(input):
    if not input:
        return '00'
    else:
        try:
            input = int(input)
            if input >= 1 and input <= 59:
                return input
            else:
                print(' [ERROR] insert a valid value between 1 and 59')
        except ValueError:
            print(' [ERROR] insert only numbers')
        
def validate_hours(input):
    try:
        input = int(input)
        if input >= 1 and input <= 24:
            return input
        else:
            print(' [ERROR] insert a valid value between 1 and 24')
    except ValueError:
        print(' [ERROR] insert only numbers')
        
def validate_integers(input):
    try:
        input = int(input)
        if input >= 1 and input <= 86400:
            return input
        else:
            print(' [ERROR] insert a valid value between 1 and 86400')
    except ValueError:
        print(' [ERROR] insert only numbers')

def validate_floats(input):
    try:
        input = float(input)
        if input >= 0.05 and input <= 2999.99:
            return input
        else:
            print(' [ERROR] insert a valid value between 0.05 and 2999.99')
    except ValueError:
        print(' [ERROR] insert only numbers')

# MAIL 
def mail_notification(response):
    sender_email = "emilianos13@gmail.com"
    receiver_email = "emilianos13@gmail.com"
    password = ""

    message = MIMEMultipart("alternative")
    message["Subject"] = "[BASD] Binance Algorithmic Stop Notification"
    message["From"] = sender_email
    message["To"] = receiver_email
    
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('mail.html')

    if 'error' in response.keys() or 'error' in response.values():
        title = 'Caution!: order NOT PLACED'
    else:
        title = 'Success!: order PLACED'
            
    html = template.render(title=title, msg=response)
    
    part = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )
    
# CONSTRUCT USER TIME
def construct_user_time(start_hour, start_minutes, working_interval):
    # construct user start working time                                                                               
    user_start_time_str = str(start_hour) + ':' + str(start_minutes)
    user_start_time = datetime.strptime(user_start_time_str, '%H:%M').time()
    # construct user end working time
    user_end_time = (datetime.strptime(user_start_time_str, '%H:%M') + timedelta(hours=working_interval)).time()
    return user_start_time, user_end_time
    
# MAIN 
while True:        
    # COLLECT INPUTS FROM USER
    print()
    tempo.sleep(1)
    print(' [INFO] Welcome to BASD, acronym for Binance Algorithmic Stop Daemon... \n [INFO] DISCLAIMER \n [WARN] This software comes with no warranty. \n [WARN] You have the whole responsability for profits or losses that might occur' )
    print()
    
    # get api key
    api_key = getpass(prompt='Insert or paste your Binance.com API KEY: ')
    if len(api_key) < 64:
        print(' [ERROR] Check your API KEY lenght, it should contains 64 characters at least, without spaces')
    else:
        # get api secret key
        api_secret = getpass(prompt='Insert or paste your Binance.com SECRET KEY: ')
        if len(api_secret) < 64:
            print(' [ERROR] Check your API SECRET KEY lenght, it should contains 64 characters at least, without spaces')
        else:
            # get timezone continet
            timezone_continent = input('Insert your CONTINENT (IANA tz database format), e.g. Europe: ')
            if timezone_continent.isalpha():
            
                # get timezone city
                timezone_city = input('Insert your nearest CITY (IANA tz database format), e.g. Rome: ')
                if timezone_city.isalpha():
                    user_timezone = timezone_continent.capitalize() + '/' + timezone_city.capitalize()
                    
                    #validate timezone
                    if user_timezone in pytz.all_timezones:
                    
                        # get start hour
                        input_start_hour = input('Insert which HOUR (24h time format) program starts working, e.g. 23: ')
                        if validate_hours(input_start_hour):
                            start_hour = validate_hours(input_start_hour)
                            
                            # get start minutes
                            input_start_minutes = input('Insert which MINUTES program starts working. Leave it blank for 0 minutes, e.g. 30: ')
                            if validate_minutes(input_start_minutes):
                                start_minutes = validate_minutes(input_start_minutes)
                                
                                # get working interval
                                input_working_interval = input('Insert how many HOURS you want program keeps working, 24 equals to all day, e.g. 8: ')
                                if validate_working_interval(input_working_interval):
                                    working_interval = validate_working_interval(input_working_interval)
                                    
                                    # get refresh_interval
                                    input_refresh_interval = input('Insert how much time in SECONDS should pass before controlling again, e.g. 3: ')
                                    if validate_integers(input_refresh_interval):
                                        refresh_interval = validate_integers(input_refresh_interval)
                                        
                                        # get OCO choice
                                        is_oco = input('Do you want OCO orders? Type yes or no: ')
                                        
                                        # OCO orders
                                        if 'yes' in is_oco.lower():
                                            
                                            # get PROFIT percentage
                                            input_profit_percentage = input('Insert PROFIT percentage, e.g. 5.20: ')
                                            if validate_floats(input_profit_percentage):
                                                profit_percentage = validate_floats(input_profit_percentage)
                                                
                                                # get STOP LOSS percentage
                                                input_stop_loss_oco_percentage = input('Insert STOP LOSS percentage. To successfully have order executed, this price should be LOWER than symbol market price WHEN order will be filled. e.g. 1.20: ')
                                                if validate_floats(input_stop_loss_oco_percentage):
                                                    stop_loss_oco_percentage = validate_floats(input_stop_loss_oco_percentage)
                                                    
                                                    # get STOP LOSS LIMIT percentage
                                                    input_stop_loss_limit_oco_percentage = input('Insert STOP LOSS LIMIT percentage. To successfully have order executed, this price should be HIGHER than symbol market price WHEN order will be filled, e.g. 1.00: ')
                                                    if validate_floats(input_stop_loss_limit_oco_percentage):
                                                        stop_loss_limit_oco_percentage = validate_floats(input_stop_loss_limit_oco_percentage)
                                                        
                                                        # get user time preferences form construct_user_time()
                                                        user_start_time, user_end_time = construct_user_time(start_hour, start_minutes, working_interval)

                                                        tabledata = [['Timezone', user_timezone], ['Start Time', 'everyday at: ' + str(user_start_time)], 
                                                                    ['End Time', 'everyday at: ' + str(user_end_time)], ['Refresh Interval', str(refresh_interval) + 'secs'], 
                                                                    ['OCO order', 'YES'], ['Take Profit Percentage', '+' + str(profit_percentage) + '%'], 
                                                                    ['Stop Loss Percentage', '-' + str(stop_loss_oco_percentage) + '%'], 
                                                                    ['Stop Loss Limit Percentage', '-' + str(stop_loss_limit_oco_percentage) + '%']
                                                                    ]
                                                        print(tabulate(tabledata, headers=['Key', 'Value']))
                                                        
                                                        # get data confirmation
                                                        confirm = input('Type yes to confirm all data above is correct: ')
                                                        if 'yes' in confirm.lower():
                                                            # end data collection
                                                            check_time() 
                                                        elif 'no' in confirm.lower():
                                                            # restart from the beginning  
                                                            continue
                                                            reset_inputs()
                                                        else:
                                                            # restart from the beginning 
                                                            print(" [ERROR] Type entire word, e.g. yes")
                                                            continue
                                                            reset_inputs()
                                                            
                                        # non OCO orders
                                        elif 'no' in is_oco.lower():
                                        
                                            # get order choice, SL or TP
                                            is_stop_loss_order = input('Do you want a STOP LOSS order? If not, a take profit order will be placed. Type yes or no: ')
                                            
                                            # TAKE PROFIT order
                                            if 'no' in is_stop_loss_order.lower():
                                            
                                                # get LIMIT PROFIT percentage
                                                input_limit_profit_percentage = input('Insert LIMIT PROFIT percentage, e.g. 5.20: ')
                                                if validate_floats(input_limit_profit_percentage):
                                                    limit_profit_percentage = validate_floats(input_limit_profit_percentage)
                                                    
                                                    # get STOP PROFIT percentage
                                                    input_stop_profit_percentage = input('Insert STOP PROFIT percentage, e.g. 5.25: ')
                                                    if validate_floats(input_stop_profit_percentage):
                                                        stop_profit_percentage = validate_floats(input_stop_profit_percentage)
                                                        
                                                        # get user time preferences form construct_user_time()
                                                        user_start_time, user_end_time = construct_user_time(start_hour, start_minutes, working_interval)
                                                        
                                                        print('DATA RESUME')
                                                        print()
                                                        tabledata = [['Timezone', user_timezone], ['Start Time', 'everyday at: ' + str(user_start_time)],
                                                                    ['End Time', 'everyday at: ' + str(user_end_time)], ['Refresh Interval', str(refresh_interval) + 'secs'], 
                                                                    ['OCO order', 'NO'], ['Take Profit order', 'YES'],
                                                                    ['Stop Profit Percentage', '+' + str(stop_profit_percentage) + '%'], 
                                                                    ['Take Profit Limit Percentage', '+' + str(limit_profit_percentage) + '%']
                                                                    ]
                                                        print(tabulate(tabledata, headers=['Key', 'Value']))                                                                         
                                                        
                                                        # get data confirmation
                                                        confirm = input('Type yes to confirm all data above is correct: ')
                                                        if 'yes' in confirm.lower():
                                                            # end data collection
                                                            check_time() 
                                                        elif 'no' in confirm.lower():
                                                            # restart from the beginning  
                                                            continue
                                                            reset_inputs()
                                                        else:
                                                            # restart from the beginning 
                                                            print(" [ERROR] Type entire word, e.g. yes")
                                                            continue
                                                            reset_inputs()
                                                    
                                            # STOP LOSS order
                                            elif 'yes' in is_stop_loss_order.lower():
                                                
                                                # get LIMIT LOSS percentage
                                                input_limit_loss_percentage = input('Insert limit loss percentage, e.g. 1.15: ')
                                                if validate_floats(input_limit_loss_percentage):
                                                    limit_loss_percentage = validate_floats(input_limit_loss_percentage)
                                                    
                                                    # get STOP LOSS percentage
                                                    input_stop_loss_percentage = input('Insert stop loss percentage, e.g. 1.10: ')
                                                    if  validate_floats(input_stop_loss_percentage):
                                                        stop_loss_percentage = validate_floats(input_stop_loss_percentage)
                                                        
                                                        # get user time preferences form construct_user_time()
                                                        user_start_time, user_end_time = construct_user_time(start_hour, start_minutes, working_interval)
  
                                                        print('DATA RESUME')
                                                        print()
                                                        tabledata = [['Timezone', user_timezone], ['Start Time', 'everyday at: ' + str(user_start_time)], 
                                                                    ['End Time', 'everyday at: ' + str(user_end_time)], ['Refresh Interval', str(refresh_interval) + 'secs'], 
                                                                    ['OCO order', 'NO'], ['Stop Loss order', 'YES'], 
                                                                    ['Stop Loss Percentage', '-' + str(stop_loss_percentage) + '%'], 
                                                                    ['Limit Loss Percentage', '-' + str(limit_loss_percentage) + '%']
                                                                    ]
                                                        print(tabulate(tabledata, headers=['Key', 'Value'])) 

                                                        # get data confirmation
                                                        confirm = input('Type yes to confirm all data above is correct: ')
                                                        if 'yes' in confirm.lower():
                                                            # end data collection
                                                            check_time() 
                                                        elif 'no' in confirm.lower():
                                                            # restart from the beginning  
                                                            continue
                                                            reset_inputs()
                                                        else:
                                                            # restart from the beginning 
                                                            print(" [ERROR] Type entire word, e.g. yes")
                                                            continue
                                                            reset_inputs()
                                            else:
                                                print(" [ERROR] Type entire word, e.g. yes")
                                        else:
                                            print(" [ERROR] Type entire word, e.g. yes")
                    else:
                        print(' [ERROR] Timezone: '+ timezone_continent.capitalize() + '/' + timezone_city.capitalize() + ' you entered is not valid. \n Check it at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List.')
                else:
                    print(" [ERROR] Insert only letters")
            else:
                print(" [ERROR] Insert only letters")
