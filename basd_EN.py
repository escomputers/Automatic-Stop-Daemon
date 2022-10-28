#!/usr/bin/env python3

# IMPORTS
import logging
import time
import pytz
import threading
import smtplib
import ssl
from datetime import datetime, timedelta

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
    if now.time() >= user_start_time and now.time() <= user_end_time:
        # yes
        websocket_connect()
    else:
        # ws_client.stop()
        websocket_connect()


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


# WINDOW CONTENTS
THREAD_EVENT = '-THREAD-'
cp = sg.cprint


def the_thread(window):
    """
    The thread that communicates with the application through the window's events.

    Once a second wakes and sends a new event and associated value to the window
    """
    i = 0
    while True:
        time.sleep(1)
        window.write_event_value('-THREAD-', (threading.current_thread().name, i))      # Data sent is a tuple of thread name and counter
        cp('This is cheating from the thread', c='white on green')
        i += 1


def main():
    sg.theme('Default 1')
    # sg.theme('Dark Grey 2')

    layout = [
            [sg.Text('BASD', size=(30, 1), font=("Helvetica", 18, 'bold')), sg.Push()],
            [sg.Text('API Key', font=("Helvetica", 12)), sg.Input(k='-APIKEY-', font=("Helvetica", 12), tooltip='Type or paste your Binance.com API KEY', password_char='*')],
            [sg.Text('API Secret', font=("Helvetica", 12)), sg.Input(k='-APISECRET-', font=("Helvetica", 12), tooltip='Type or paste your Binance.com SECRET KEY', password_char='*')],
            [sg.Text('Timezone Continent', font=("Helvetica", 12)), sg.Input(k='-CONTINENT-', font=("Helvetica", 12), tooltip='Type your CONTINENT (IANA timezone format) e.g. Europe')],
            [sg.Text('Timezone City', font=("Helvetica", 12)), sg.Input(k='-CITY-', font=("Helvetica", 12), tooltip='Type your CITY (IANA timezone format) e.g. Rome')],
            [sg.Text('Start Hour', font=("Helvetica", 12)), sg.Input(k='-STARTHOUR-', font=("Helvetica", 12), tooltip='Type START HOUR (1-24) e.g. 23')],
            [sg.Text('Start Minutes', font=("Helvetica", 12)), sg.Input(k='-STARTMINUTES-', font=("Helvetica", 12), tooltip='Type START MINUTES (0-59). Leave it blank for 0 minutes, e.g. 30')],
            [sg.Text('Active Hours', font=("Helvetica", 12)), sg.Input(k='-WORKINGINTERVAL-', font=("Helvetica", 12), tooltip='Type how many working HOURS you want. 24 equals to all day, e.g. 8')],
            [sg.Checkbox('Email Notification', font=("Helvetica", 12), default=True, k='-EMAILCHOICE-')],
            [sg.Checkbox('Place OCO order', font=("Helvetica", 12), default=False, k='-OCOCHOICE-')],
            [sg.MLine(size=(80, 10), autoscroll=True, reroute_stdout=True, write_only=True, reroute_cprint=True, k='-TABLEDATA-')],
            # [sg.StatusBar("", size=(0, 1), key='-STATUS-')],
            [sg.Button('Confirm'), sg.Button('Quit')],
            ]

    # Create the window
    window = sg.Window('Binance Algorithmic Stop Daemon', layout, element_justification='r')

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()
        # cp(event, values)

        api_key = values['-APIKEY-']
        api_secret = values['-APISECRET-']
        if len(api_key) < 64:
            window['-TABLEDATA-'].print('[ERROR] Check your API Key, 64 characters minimum, no spaces', background_color='black', text_color='red', font=("Helvetica", 14))
        elif len(api_secret) < 64:
            window['-TABLEDATA-'].print('[ERROR] Check your API Secret Key, 64 characters minimum, no spaces', background_color='black', text_color='red', font=("Helvetica", 14))
        elif api_key == api_secret:
            window['-TABLEDATA-'].print('[ERROR] API Key and API Secret Key cannot be the same', background_color='black', text_color='red', font=("Helvetica", 14))
        else:
            window['-TABLEDATA-'].print('[OK]', background_color='black', text_color='green', font=("Helvetica", 14))

        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

        '''
        window['-STATUS-'].update(state)

        if event.startswith('Start'):
            threading.Thread(target=the_thread, args=(window,), daemon=True).start()
        if event == THREAD_EVENT:
            cp(f'Data from the thread ', colors='white on purple', end='')
            cp(f'{values[THREAD_EVENT]}', colors='white on red')
        '''

    # Finish up by removing from the screen
    window.close()


if __name__ == '__main__':
    main()
