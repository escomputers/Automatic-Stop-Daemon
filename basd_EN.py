#!/usr/bin/env python3

# IMPORTS
from curses.ascii import isalpha
import logging
# import time
import pytz
import threading
import smtplib
import ssl
from datetime import datetime, time, timedelta

from binance.websocket.spot.websocket_client import SpotWebsocketClient
from binance.lib.utils import config_logging
from binance.spot import Spot as Client
from binance.error import ClientError

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError

from jinja2 import Environment, FileSystemLoader

import PySimpleGUI as sg

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
            # error_msg = logging.error()
            error_msg = None

        finally:
            if 'yes' in is_email.lower():
                oco_mail_body(
                    error_msg, msg, symbol, qty, profit_pr, profit_pct,
                    sl_lmt_pr_oco, sl_pr_oco, sl_lmt_oco_pct, last_pr
                )
            else:
                # log to file
                # logging.error()
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
            # error_msg = logging.error()
            error_msg = None

        finally:
            if 'yes' in is_email.lower():
                tp_mail_body(
                    error_msg, msg, symbol, qty,
                    lmt_profit_pr, stop_pr, lmt_profit_pct, last_pr
                )
            else:
                # log to file
                # logging.error()
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
            # error_msg = logging.error()
            error_msg = None

        finally:
            if 'yes' in is_email.lower():
                sl_mail_body(
                    error_msg, msg, symbol, qty,
                    lmt_loss_pr, sl_pr, lmt_loss_pct, last_pr
                )
            else:
                # log to file
                # logging.error()
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

            if order_status == 'CANCELED' and side == 'BUY':
                # get global variables

                # order_pr = float(message['p'])
                order_pr = 20763

                symbol = message['s']

                # qty = flot(message['q'])
                qty = 0.00052

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
    if now.time() >= user_start_time_def and now.time() <= user_end_time_def:
        # yes
        websocket_connect()
    else:
        # ws_client.stop()
        websocket_connect()


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


# VALIDATION
def is_hour(window, input):
    try:
        input = int(input)
        if input >= 1 and input <= 24:
            return input
        else:
            window['-TABLEDATA-'].print('[ERROR] Type a valid value between 1 and 24', background_color='black', text_color='red', font=("Helvetica", 14))
    except ValueError:
        window['-TABLEDATA-'].print('[ERROR] Type only numbers', background_color='black', text_color='red', font=("Helvetica", 14))


def is_valid_time(window, input):
    timeformat = "%H:%M"
    try:
        input = datetime.strptime(input, timeformat)
        window['-TABLEDATA-'].print('[OK] Start Time', background_color='black', text_color='green', font=("Helvetica", 14))
        return str(input.time())
    except ValueError:
        window['-TABLEDATA-'].print('[ERROR] Type a valid time format, e.g. 15:30', background_color='black', text_color='red', font=("Helvetica", 14))


# WINDOW CONTENTS
def main():
    sg.theme('Default 1')

    layout = [
            [sg.Text('BASD', size=(30, 1), font=("Helvetica", 18, 'bold')), sg.Push()],
            [sg.Text('API Key', font=("Helvetica", 12)), sg.Input(k='-APIKEY-', enable_events=True, font=("Helvetica", 12), tooltip='Type or paste your Binance.com API KEY', password_char='*')],
            [sg.Text('API Secret', font=("Helvetica", 12)), sg.Input(k='-APISECRET-', enable_events=True, font=("Helvetica", 12), tooltip='Type or paste your Binance.com SECRET KEY', password_char='*')],
            [sg.Text('Timezone Continent', font=("Helvetica", 12)), sg.Input(k='-CONTINENT-', enable_events=True, font=("Helvetica", 12), tooltip='Type your CONTINENT (IANA timezone format) e.g. Europe')],
            [sg.Text('Timezone City', font=("Helvetica", 12)), sg.Input(k='-CITY-', enable_events=True, font=("Helvetica", 12), tooltip='Type your CITY (IANA timezone format) e.g. Rome')],
            [sg.Text('Start Time', font=("Helvetica", 12)), sg.Input(k='-STARTTIME-', enable_events=True, font=("Helvetica", 12), tooltip='Type START TIME (1-24h)(0-59m) e.g. 23:45')],
            [sg.Text('Active Hours', font=("Helvetica", 12)), sg.Input(k='-WORKINGINTERVAL-', enable_events=True, font=("Helvetica", 12), tooltip='Type how many working HOURS you want. 24 equals to all day, e.g. 8')],
            [sg.Text('End Time', font=("Helvetica", 12)), sg.Input(k='-ENDTIME-', enable_events=True, font=("Helvetica", 12))],
            [sg.Checkbox('Email Notification', font=("Helvetica", 12), default=True, k='-EMAILCHOICE-')],
            [sg.Checkbox('Place OCO order', font=("Helvetica", 12), default=False, k='-OCOCHOICE-')],
            [sg.MLine(size=(80, 10), autoscroll=True, reroute_stdout=True, write_only=True, reroute_cprint=True, k='-TABLEDATA-')],
            # [sg.StatusBar('', size=(0, 1), key='-STATUS-')],
            [sg.Button('Confirm'), sg.Button('Quit')],
            ]

    # Create the window
    window = sg.Window('Binance Algorithmic Stop Daemon', layout, element_justification='r')    

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()

        # define global variables
        api_key = values['-APIKEY-']
        api_secret = values['-APISECRET-']
        tz_cont = values['-CONTINENT-']
        tz_city = values['-CITY-']
        inp_start_time = values['-STARTTIME-']
        inp_working_ival = values['-WORKINGINTERVAL-']

        # validate API KEY
        if event == '-APIKEY-' and api_key:
            if len(api_key) < 64:
                window['-TABLEDATA-'].print('[ERROR] Check your API Key, 64 characters minimum, no spaces', background_color='black', text_color='red', font=("Helvetica", 14))
            else:
                window['-TABLEDATA-'].print('[OK] API Key', background_color='black', text_color='green', font=("Helvetica", 14))

        # validate API SECRET KEY
        if event == '-APISECRET-' and api_secret:
            if len(api_secret) < 64:
                window['-TABLEDATA-'].print('[ERROR] Check your API Secret Key, 64 characters minimum, no spaces', background_color='black', text_color='red', font=("Helvetica", 14))
            else:
                window['-TABLEDATA-'].print('[OK] API Secret Key', background_color='black', text_color='green', font=("Helvetica", 14))

        # validate API KEYS
        if api_key and api_secret and len(api_key) >= 64 and len(api_secret) >= 64:
            if api_key == api_secret:
                window['-TABLEDATA-'].print('[ERROR] API Key and API Secret Key cannot be the same', background_color='black', text_color='red', font=("Helvetica", 14))
            else:
                window['-TABLEDATA-'].print('[OK] API Key and API Secret Key', background_color='black', text_color='green', font=("Helvetica", 14))
                window['-APIKEY-'].update('', background_color='black', text_color='green')
                window['-APISECRET-'].update('', background_color='black', text_color='green')

        # validate TIMEZONE CONTINENT
        if event == '-CONTINENT-' and tz_cont:
            if tz_cont.isalpha():
                window['-TABLEDATA-'].print('[OK] Timezone Continent format', background_color='black', text_color='green', font=("Helvetica", 14))
            else:
                window['-TABLEDATA-'].print('[ERROR] Type only letters', background_color='black', text_color='red', font=("Helvetica", 14))

        # validate TIMEZONE CITY
        if event == '-CITY-' and tz_city:
            if tz_city.isalpha():
                window['-TABLEDATA-'].print('[OK] Timezone City format', background_color='black', text_color='green', font=("Helvetica", 14))
            else:
                window['-TABLEDATA-'].print('[ERROR] Type only letters', background_color='black', text_color='red', font=("Helvetica", 14))

        # validate TIMEZONE
        if tz_cont.isalpha() and tz_city.isalpha():
            usr_tz = tz_cont.capitalize() + '/' + tz_city.capitalize()
            if usr_tz in pytz.all_timezones:
                window['-TABLEDATA-'].print('[OK] Timezone', background_color='black', text_color='green', font=("Helvetica", 14))
                window['-CONTINENT-'].update(tz_cont.capitalize(), background_color='black', text_color='green')
                window['-CITY-'].update(tz_city.capitalize(), background_color='black', text_color='green')
            else:
                window['-TABLEDATA-'].print(
                        '[ERROR] Timezone: ' + tz_cont.capitalize() + '/' + tz_city.capitalize() +
                        ' you entered is not valid. \n ' +
                        'Check it at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List.', background_color='black', text_color='red', font=("Helvetica", 14)
                    )

        # validate START TIME
        if event == '-STARTTIME-' and values['-STARTTIME-']:
            if is_valid_time(window, inp_start_time):
                start_time = is_valid_time(window, inp_start_time)
                user_start_time = datetime.strptime(start_time, '%H:%M:%S')
                user_start_time_def = str(user_start_time.time())[:-3]  # remove seconds from string

        # validate WORKING INTERVAL
        if event == '-WORKINGINTERVAL-' and values['-WORKINGINTERVAL-']:
            if is_hour(window, inp_working_ival):
                working_ival = is_hour(window, inp_working_ival)
                window['-WORKINGINTERVAL-'].update(working_ival, background_color='black', text_color='green')

        # construct USER END TIME
        try:
            if user_start_time and working_ival:
                end_time = (user_start_time + timedelta(hours=working_ival)).time()
                user_end_time = str(end_time)[:-3]  # remove seconds from string
                user_end_time_def = datetime.strptime(user_end_time, '%H:%M')
                window['-ENDTIME-'].update(user_end_time, background_color='black', text_color='green')
        except UnboundLocalError:
            continue



        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

    # Finish up by removing from the screen
    window.close()


if __name__ == '__main__':
    main()
