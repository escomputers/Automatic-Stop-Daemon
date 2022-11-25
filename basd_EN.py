#!/usr/bin/env python3

# IMPORTS
import logging
import pytz
import smtplib
import ssl
from datetime import datetime, time, timedelta

from binance.websocket.spot.websocket_client import SpotWebsocketClient
from binance.lib.utils import config_logging
from binance.spot import Spot as Client
from binance.error import ClientError

from getpass import getpass
from tabulate import tabulate

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError

from jinja2 import Environment, FileSystemLoader


# load jinja2 template
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('mail.html')

config_logging(logging, logging.DEBUG)


# RESET INPUTS
def reset_inputs():
    for element in dir():
        if element[0:2] != '__':
            del globals()[element]
    del element


# PLACE OCO ORDER
def place_oco_order(symbol, qty, order_pr, last_pr):

    # TAKE PROFIT price
    profit_pr = round(
        (order_pr + round(((order_pr / 100) * profit_pct), 8)), 2
    )

    # STOP LOSS price
    sl_pr_oco = round(
        (
            order_pr - round(
                ((order_pr / 100) * sl_oco_pct), 8
            )
        ), 2
    )

    # LIMIT PRICE
    sl_lmt_pr_oco = round(
        (
            order_pr - round(
                ((order_pr / 100) * sl_lmt_oco_pct), 8
            )
        ), 2
    )

    # new order
    params = {
        'symbol': symbol,
        'side': 'SELL',
        'stopLimitTimeInForce': 'GTC',
        'quantity': qty,
        'price': str(profit_pr),
        'stopPrice': str(sl_pr_oco),
        'stopLimitPrice': str(sl_lmt_pr_oco)
    }

    client = Client(
        api_key, api_secret, base_url='https://api.binance.com'
    )

    '''
    OCO SELL rule = Limit Price > Last Price > Stop Price
    OCO BUY rule  = Limit Price < Last Price < Stop Price
    '''

    # if stop and limit prices respect OCO rules, place orders
    if last_pr > sl_pr_oco and last_pr < sl_lmt_pr_oco:

        try:
            client.new_oco_order(**params)
            msg = 'Success! Sell order PLACED'
            error_msg = None

        except ClientError as error:
            msg = 'Error! Sell order NOT PLACED'
            # error_msg = logging.error("Found error. status: {}, error code: {}, error message: {}".format(error.status_code, error.error_code, error.error_message))
            error_msg = None

        finally:
            if 'yes' in is_email.lower():
                oco_mail_body(
                    error_msg, msg, symbol, qty, profit_pr, profit_pct,
                    sl_lmt_pr_oco, sl_pr_oco, sl_lmt_oco_pct, last_pr
                )
            else:
                # log to file
                # logging.error("Found error. status: {}, error code: {}, error message: {}".format(error.status_code, error.error_code, error.error_message))
                pass

    else:
        error_msg = '[ERROR]Prices relationship for the orders not correct. \n' + \
            'OCO SELL rule = Limit Price > Last Price > Stop Price'
        if 'yes' in is_email.lower():
            msg = 'Error! Sell order NOT PLACED'
            oco_mail_body(
                error_msg, msg, symbol, qty, profit_pr, profit_pct,
                sl_lmt_pr_oco, sl_pr_oco, sl_lmt_oco_pct, last_pr
            )


# PLACE TAKE PROFIT ORDER
def place_tp_order(symbol, qty, order_pr, last_pr):

    # LIMIT PROFIT price
    lmt_profit_pr = round(
        (order_pr + round(((order_pr / 100) * lmt_profit_pct), 8)), 2
    )

    # STOP PROFIT price
    stop_pr = round(
        (order_pr + round(((order_pr / 100) * stop_profit_pct), 8)), 2
    )

    # new order
    params = {
        'symbol': symbol,
        'side': 'SELL',
        'type': 'TAKE_PROFIT_LIMIT',
        'timeInForce': 'GTC',
        'quantity': qty,
        'price': str(lmt_profit_pr),
        'stopPrice': str(stop_pr),
    }

    client = Client(
        api_key, api_secret, base_url='https://api.binance.com'
    )

    notional = qty * lmt_profit_pr

    if stop_pr > last_pr and notional > 11:
        try:
            client.new_order(**params)
            msg = 'Success! Sell order PLACED'
            error_msg = None

        except ClientError as error:
            msg = 'Error! Sell order NOT PLACED'
            # error_msg = logging.error("Found error. status: {}, error code: {}, error message: {}".format(error.status_code, error.error_code, error.error_message))
            error_msg = None

        finally:
            if 'yes' in is_email.lower():
                tp_mail_body(
                    error_msg, msg, symbol, qty,
                    lmt_profit_pr, stop_pr, lmt_profit_pct, last_pr
                )
            else:
                # log to file
                # logging.error("Found error. status: {}, error code: {}, error message: {}".format(error.status_code, error.error_code, error.error_message))
                pass


# STOP LOSS ORDER
def place_sl_order(symbol, qty, order_pr, last_pr):

    # STOP LOSS LIMIT price
    lmt_loss_pr = round(
        (order_pr - round(((order_pr / 100) * lmt_loss_pct), 8)), 2
    )

    # STOP LOSS price
    sl_pr = round(
        (order_pr - round(((order_pr / 100) * sl_pct), 8)), 2
    )

    # new order
    params = {
        'symbol': symbol,
        'side': 'SELL',
        'type': 'STOP_LOSS_LIMIT',
        'timeInForce': 'GTC',
        'quantity': qty,
        'price': str(lmt_loss_pr),
        'stopPrice': str(sl_pr),

    }

    client = Client(
        api_key, api_secret, base_url='https://api.binance.com'
    )

    notional = qty * lmt_loss_pr

    if sl_pr < last_pr and notional > 11:
        try:
            client.new_order(**params)
            msg = 'Success! Sell order PLACED'
            error_msg = None

        except ClientError as error:
            msg = 'Error! Sell order NOT PLACED'
            # error_msg = logging.error("Found error. status: {}, error code: {}, error message: {}".format(error.status_code, error.error_code, error.error_message))
            error_msg = None

        finally:
            if 'yes' in is_email.lower():
                sl_mail_body(
                    error_msg, msg, symbol, qty,
                    lmt_loss_pr, sl_pr, lmt_loss_pct, last_pr
                )
            else:
                # log to file
                # logging.error("Found error. status: {}, error code: {}, error message: {}".format(error.status_code, error.error_code, error.error_message))
                pass


# GET LAST PRICE VIA REST API
def get_last_pr(symbol):
    client = Client(
        api_key, api_secret, base_url='https://api.binance.com'
    )
    response = client.ticker_price(symbol)
    last_pr = round((float(response['price'])), 2)
    return last_pr


# CHECK FOR FILLED BUY ORDERS
def listen_to_filled_orders(message):
    try:
        # get order type
        order_type = message['e']

        # if order was executed
        if order_type == 'executionReport':
            order_status = message['X']
            side = message['S']

            if order_status == 'FILLED' and side == 'BUY':
                # get global variables

                order_pr = float(message['p'])
                # order_pr = 20763

                symbol = message['s']

                qty = float(message['q'])
                # qty = 0.00052

                # get LAST SYMBOL PRICE
                last_pr = get_last_pr(symbol)

                # OCO order
                if 'yes' in is_oco.lower():
                    place_oco_order(symbol, qty, order_pr, last_pr)
                # TAKE PROFIT order
                elif 'no' in is_sl_order.lower():
                    place_tp_order(symbol, qty, order_pr, last_pr)
                # STOP LOSS order
                else:
                    place_sl_order(symbol, qty, order_pr, last_pr)

    except KeyError:
        pass


# CONNECT TO BINANCE.COM
def websocket_connect():
    client = Client(api_key, base_url='https://api.binance.com')
    response = client.new_listen_key()

    logging.info('Receving listen key : {}'.format(response['listenKey']))

    ws_client = SpotWebsocketClient(stream_url='wss://stream.binance.com:9443')
    ws_client.start()

    ws_client.user_data(
        listen_key=response['listenKey'],
        id=1,
        callback=listen_to_filled_orders,
    )


# CHECK TIME
def check_time():
    # get time zone of specified location
    tmzone = pytz.timezone(usr_tz)

    # change current time accordingly
    now = (datetime.now(tmzone))

    # check if it's time to work or not
    if now.time() >= user_start_time and now.time() <= user_end_time:
        # yes
        websocket_connect()
    else:
        # ws_client.stop()
        websocket_connect()


# VALIDATION
def is_mins(input):
    if not input:
        return '00'
    else:
        try:
            input = int(input)
            if input >= 1 and input <= 59:
                return input
            else:
                print(' [ERROR] Type a valid value between 1 and 59')
        except ValueError:
            print(' [ERROR] Type only numbers')


def is_hour(input):
    try:
        input = int(input)
        if input >= 1 and input <= 24:
            return input
        else:
            print(' [ERROR] Type a valid value between 1 and 24')
    except ValueError:
        print(' [ERROR] Type only numbers')


def is_float(input):
    try:
        input = float(input)
        if input >= 0.05 and input <= 2999.99:
            return input
        else:
            print(' [ERROR] Type a valid value between 0.05 and 2999.99')
    except ValueError:
        print(' [ERROR] Type only numbers')


# CONSTRUCT USER TIME
def construct_user_time(start_hour, start_mins, working_ival):
    # construct user start working time
    user_start_time_str = str(start_hour) + ':' + str(start_mins)
    user_start_time = datetime.strptime(user_start_time_str, '%H:%M').time()
    # construct user end working time
    user_end_time = (
        datetime.strptime(user_start_time_str, '%H:%M') +
        timedelta(hours=working_ival)
    ).time()
    return user_start_time, user_end_time


# OCO mail body
def oco_mail_body(error_msg, msg, symbol, qty, profit_pr, profit_pct, sl_lmt_pr_oco, sl_pr_oco, sl_lmt_oco_pct, last_pr):
    profit_order_value = round((float(qty * profit_pr)), 2)
    loss_order_value = round((float(qty * sl_lmt_pr_oco)), 2)
    html = template.render(
        error_msg=error_msg,
        title=msg,
        order_type='OCO',
        symbol=symbol,
        qty=qty,
        price=str(profit_pr),
        stop_Limit_Price=str(sl_lmt_pr_oco),
        stop_Price=str(sl_pr_oco),
        profit_pct=str(profit_pct),
        sl_lmt_oco_pct=str(sl_lmt_oco_pct),
        profit_order_value=str(profit_order_value),
        loss_order_value=str(loss_order_value),
        last_pr=str(last_pr)
    )
    send_mail(html)


# Take Profit order mail body
def tp_mail_body(error_msg, msg, symbol, qty, lmt_profit_pr, stop_pr, lmt_profit_pct, last_pr):
    order_value = round((float(qty * lmt_profit_pr)), 2)
    html = template.render(
        error_msg=error_msg,
        title=msg,
        order_type='Take Profit',
        symbol=symbol,
        qty=qty,
        stop_Limit_Price=str(lmt_profit_pr),
        stop_Price=str(stop_pr),
        lmt_profit_pct=str(lmt_profit_pct),
        order_value=str(order_value),
        last_pr=str(last_pr)
    )
    send_mail(html)


# Stop Loss order mail body
def sl_mail_body(error_msg, msg, symbol, qty, lmt_loss_pr, sl_pr, lmt_loss_pct, last_pr):
    order_value = round((float(qty * lmt_loss_pr)), 2)
    html = template.render(
        error_msg=error_msg,
        title=msg,
        order_type='Stop Loss',
        symbol=symbol,
        qty=qty,
        stop_Limit_Price=str(lmt_loss_pr),
        stop_Price=str(sl_pr),
        lmt_loss_pct=str(lmt_loss_pct),
        order_value=str(order_value),
        last_pr=str(last_pr)
    )
    send_mail(html)


# SEND MAIL
def send_mail(html):
    message = MIMEMultipart('alternative')
    message['Subject'] = '[BASD] Binance Algorithmic Stop Daemon - Notification'
    message['From'] = sender_email
    message['To'] = receiver_email

    part = MIMEText(html, 'html')

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


# COLLECT USER PREFERENCES
while True:
    print()
    print(
        '[INFO] Welcome to BASD - Binance Algorithmic Stop Daemon...' +
        '\n' + '[INFO] DISCLAIMER' +
        '\n' + '[WARN] This software comes with no guarantees.' +
        '\n' + '[WARN] Use it at your own risk'
    )
    print()

# ###################################GET COMMON INPUTS     ###################
    # get api key
    api_key = getpass(prompt='Type or paste your Binance.com API KEY: ')
    if len(api_key) < 64:
        print(
            ' [ERROR] Check your API KEY, 64 characters minimum, no spaces'
        )
    else:
        # get api secret key
        api_secret = getpass(
            prompt='Type or paste your Binance.com SECRET KEY: '
        )
        if len(api_secret) < 64:
            print(
                ' [ERROR] Check your API SECRET KEY, 64 characters minimum, no spaces'
            )
        elif api_key == api_secret:
            print(
                '[ERROR] API Key and API Secret Key cannot be the same'
            )
        else:
            # initialize tabledata for resume
            tabledata = []

            # get timezone continet
            tz_cont = input(
                'Type your CONTINENT (IANA timezone format) e.g. Europe: '
            )
            if tz_cont.isalpha():

                # get timezone city
                tz_city = input(
                    'Type your CITY (IANA timezone format) e.g. Rome: '
                )
                if tz_city.isalpha():
                    usr_tz = tz_cont.capitalize() + '/' + tz_city.capitalize()

                    # validate timezone
                    if usr_tz in pytz.all_timezones:

                        # append item to tabledata for resume
                        tabledata.append(['Timezone', usr_tz])

                        # get start hour
                        inp_start_hour = input(
                            'Type START HOUR (1-24) e.g. 23: '
                        )
                        if is_hour(inp_start_hour):
                            start_hour = is_hour(inp_start_hour)

                            # get start minutes
                            inp_start_mins = input(
                                'Type START MINUTES (0-59). ' +
                                'Leave it blank for 0 minutes, e.g. 30: '
                            )
                            if is_mins(inp_start_mins):
                                start_mins = is_mins(inp_start_mins)

                                # get working interval
                                inp_working_ival = input(
                                    'Type how many working HOURS you want. ' +
                                    '24 equals to all day, e.g. 8: '
                                )
                                if is_hour(inp_working_ival):
                                    working_ival = is_hour(inp_working_ival)

                                    # get email notification choice
                                    is_email = input(
                                        'Do you want email notifications? ' +
                                        'Type yes or no: '
                                    )

# ##################################    EMAIL NOTIFICATION     ###############
                                    if 'yes' in is_email.lower():
                                        sender_email = input(
                                            'Type sender email address (GMAIL only): '
                                        )

                                        try:
                                            validate_email(sender_email)
                                            if '@gmail.com' in sender_email:
                                                receiver_email = input(
                                                    'Type receiver email address: '
                                                )
                                                try:
                                                    validate_email(receiver_email)
                                                    password = getpass(
                                                        prompt='Type or paste your gmail app password: '
                                                    )

                                                    # append item to tabledata for resume
                                                    tabledata.append(['Email Notification', 'YES'])
                                                    tabledata.append(['Sender Email', sender_email])
                                                    tabledata.append(['Receiver Email', receiver_email])

                                                except EmailNotValidError:
                                                    print('[ERROR] Invalid receiver email address')
                                                    # restart from the beginning
                                                    continue
                                                    reset_inputs()
                                            # not Gmail address
                                            else:
                                                print('[ERROR] Only Gmail account currently supported')
                                                # restart from the beginning
                                                continue
                                                reset_inputs()
                                        except EmailNotValidError:
                                            print('[ERROR] Invalid sender email address')
                                            # restart from the beginning
                                            continue
                                            reset_inputs()

                                    # get user time
                                    user_start_time, user_end_time = construct_user_time(
                                        start_hour, start_mins, working_ival
                                    )

                                    # append item to tabledata for resume
                                    tabledata.append(['Start Time', 'everyday at: ' + str(user_start_time)])
                                    tabledata.append(['End Time', 'everyday at: ' + str(user_end_time)])

                                    # get OCO choice
                                    is_oco = input(
                                        'Do you want OCO orders? ' +
                                        'Type yes or no: '
                                    )
# #########################################     OCO     ######################
                                    if 'yes' in is_oco.lower():

                                        # append item to tabledata for resume
                                        tabledata.append(['OCO order', 'YES'])

                                        # get PROFIT percentage
                                        inp_profit_pct = input(
                                            'Type PROFIT percentage, ' +
                                            'e.g. 5.20: '
                                        )
                                        if is_float(inp_profit_pct):
                                            profit_pct = is_float(inp_profit_pct)

                                            # append item to tabledata for resume
                                            tabledata.append(
                                                ['Take Profit Percentage', '+' + str(profit_pct) + '%']
                                            )

                                            # get STOP LOSS percentage
                                            inp_sl_oco_pct = input(
                                                'Type STOP LOSS ' +
                                                'percentage. This ' +
                                                'should be LOWER ' +
                                                'than symbol market ' +
                                                'price WHEN order ' +
                                                'will be placed, ' +
                                                'e.g. 1.20: '
                                            )
                                            if is_float(inp_sl_oco_pct):
                                                sl_oco_pct = is_float(inp_sl_oco_pct)

                                                # append item to tabledata for resume
                                                tabledata.append(
                                                    ['Stop Loss Percentage', '-' + str(sl_oco_pct) + '%']
                                                )

                                                # get SL LIMIT percentage
                                                inp_sl_lmt_oco_pct = input(
                                                    'Type STOP LOSS ' +
                                                    'LIMIT percentage. ' +
                                                    'This should be ' +
                                                    'HIGHER than ' +
                                                    'symbol market ' +
                                                    'price WHEN order ' +
                                                    'will be placed, ' +
                                                    'e.g. 1.00: '
                                                )
                                                if is_float(inp_sl_lmt_oco_pct):
                                                    sl_lmt_oco_pct = is_float(inp_sl_lmt_oco_pct)

                                                    # append item to tabledata for resume
                                                    tabledata.append(
                                                        ['Stop Loss Limit Percentage', '-' + str(sl_lmt_oco_pct) + '%']
                                                    )

                                                    print()
                                                    print('DATA RESUME')
                                                    print()
                                                    print(tabulate(tabledata, headers=['Key', 'Value']))

                                                    # get data confirmation
                                                    confirm = input(
                                                        'Type yes to confirm all data above is correct: '
                                                    )
                                                    if 'yes' in confirm.lower():
                                                        # end data collection
                                                        check_time()
                                                    elif 'no' in confirm.lower():
                                                        # restart from the beginning
                                                        continue
                                                        reset_inputs()
                                                    else:
                                                        # restart from the beginning
                                                        print(' [ERROR] Type entire word, e.g. yes')
                                                        continue
                                                        reset_inputs()

# ######################################     NON OCO TAKE PROFIT    ##########
                                    elif 'no' in is_oco.lower():

                                        # append item to tabledata for resume
                                        tabledata.append(['OCO order', 'NO'])

                                        # get order choice, SL or TP
                                        is_sl_order = input(
                                            'Do you want a STOP LOSS order? ' +
                                            'If not, a take profit order ' +
                                            'will be placed. Type yes or no: '
                                        )

                                        # TAKE PROFIT order
                                        if 'no' in is_sl_order.lower():

                                            # append item to tabledata for resume
                                            tabledata.append(['Take Profit order', 'YES'])

                                            # get LIMIT PROFIT percentage
                                            inp_lmt_profit_pct = input(
                                                'Type LIMIT PROFIT percentage, e.g. 5.20: '
                                            )
                                            if is_float(inp_lmt_profit_pct):
                                                lmt_profit_pct = is_float(inp_lmt_profit_pct)

                                                # append item to tabledata for resume
                                                tabledata.append(
                                                    ['Take Profit Limit Percentage', '+' + str(lmt_profit_pct) + '%']
                                                )

                                                # get STOP PROFIT percentage
                                                inp_stop_profit_pct = input(
                                                    'Type STOP PROFIT percentage, e.g. 5.25: '
                                                )
                                                if is_float(inp_stop_profit_pct):
                                                    stop_profit_pct = is_float(inp_stop_profit_pct)

                                                    # append item to tabledata for resume
                                                    tabledata.append(
                                                        ['Stop Profit Percentage', '+' + str(stop_profit_pct) + '%']
                                                    )

                                                    print()
                                                    print('DATA RESUME')
                                                    print()
                                                    print(tabulate(tabledata, headers=['Key', 'Value']))

                                                    # get data confirmation
                                                    confirm = input(
                                                        'Type yes to confirm all data above is correct: '
                                                    )
                                                    if 'yes' in confirm.lower():
                                                        # end data collection
                                                        check_time()
                                                    elif 'no' in confirm.lower():
                                                        # restart from the beginning
                                                        continue
                                                        reset_inputs()
                                                    else:
                                                        # restart from the beginning
                                                        print(' [ERROR] Type entire word, e.g. yes')
                                                        continue
                                                        reset_inputs()

# #########################################    NON OCO STOP LOSS #############
                                        elif 'yes' in is_sl_order.lower():

                                            # append item to tabledata for resume
                                            tabledata.append(['Stop Loss order', 'YES'])

                                            # get LIMIT LOSS percentage
                                            inp_lmt_loss_pct = input(
                                                'Type LIMIT LOSS percentage, e.g. 1.15: '
                                            )
                                            if is_float(inp_lmt_loss_pct):
                                                lmt_loss_pct = is_float(inp_lmt_loss_pct)

                                                # append item to tabledata for resume
                                                tabledata.append(
                                                    ['Limit Loss Percentage', '-' + str(lmt_loss_pct) + '%']
                                                )

                                                # get STOP LOSS percentage
                                                inp_sl_pct = input(
                                                    'Type STOP LOSS percentage, e.g. 1.10: '
                                                )
                                                if is_float(inp_sl_pct):
                                                    sl_pct = is_float(inp_sl_pct)

                                                    # append item to tabledata for resume
                                                    tabledata.append(
                                                        ['Stop Loss Percentage', '-' + str(sl_pct) + '%']
                                                    )

                                                    print()
                                                    print('DATA RESUME')
                                                    print()
                                                    print(tabulate(tabledata, headers=['Key', 'Value']))

                                                    # get data confirmation
                                                    confirm = input(
                                                        'Type yes to confirm all data above is correct: '
                                                    )
                                                    if 'yes' in confirm.lower():
                                                        # end data collection
                                                        check_time()
                                                    elif 'no' in confirm.lower():
                                                        # restart from the beginning
                                                        continue
                                                        reset_inputs()
                                                    else:
                                                        # restart from the beginning
                                                        print(' [ERROR] Type entire word, e.g. yes')
                                                        continue
                                                        reset_inputs()
                                        else:
                                            print(' [ERROR] Type entire word, e.g. yes')
                                    else:
                                        print(' [ERROR] Type entire word, e.g. yes')
                    else:
                        print(
                            ' [ERROR] Timezone: ' + tz_cont.capitalize() + '/' + tz_city.capitalize() +
                            ' you entered is not valid. \n ' +
                            'Check it at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List.'
                        )
                else:
                    print(' [ERROR] Type only letters')
            else:
                print(' [ERROR] Type only letters')
