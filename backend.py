#!/usr/bin/env python3

# IMPORTS
import logging
import pytz
import smtplib
import ssl
from datetime import datetime, timedelta

from binance.websocket.spot.websocket_client import SpotWebsocketClient
from binance.lib.utils import config_logging
from binance.spot import Spot as Client
from binance.error import ClientError

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, FileSystemLoader

# load jinja2 template
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('mail.html')

config_logging(logging, logging.DEBUG)


# PLACE OCO ORDER
def place_oco_order(symbol, qty, order_pr, last_pr):

    # TAKE PROFIT price
    profit_pr = round(
        (order_pr + round(((order_pr / 100) * oco_profit_pct), 8)), 2
    )

    # STOP LOSS price
    sl_pr_oco = round(
        (
            order_pr - round(
                ((order_pr / 100) * oco_sl_pct), 8
            )
        ), 2
    )

    # LIMIT PRICE
    sl_lmt_pr_oco = round(
        (
            order_pr - round(
                ((order_pr / 100) * oco_lmt_pct), 8
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
        backend_args['api_key'], backend_args['api_secret'], base_url='https://api.binance.com'
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
            if backend_args['email_choice']:
                oco_mail_body(
                    error_msg, msg, symbol, qty, profit_pr, oco_profit_pct,
                    sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr
                )
            else:
                # log to file
                # logging.error()
                pass

    else:
        error_msg = '[ERROR]Prices relationship for the orders not correct. \n' + \
            'OCO SELL rule = Limit Price > Last Price > Stop Price'
        if backend_args['email_choice']:
            msg = 'Error! Sell order NOT PLACED'
            oco_mail_body(
                error_msg, msg, symbol, qty, profit_pr, oco_profit_pct,
                sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr
            )


# PLACE TAKE PROFIT ORDER
def place_tp_order(symbol, qty, order_pr, last_pr):

    # LIMIT PROFIT price
    lmt_profit_pr = round(
        (order_pr + round(((order_pr / 100) * tp_lmt_pct), 8)), 2
    )

    # STOP PROFIT price
    stop_pr = round(
        (order_pr + round(((order_pr / 100) * tp_stop_pct), 8)), 2
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
        backend_args['api_key'], backend_args['api_secret'], base_url='https://api.binance.com'
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
            if backend_args['email_choice']:
                tp_mail_body(
                    error_msg, msg, symbol, qty,
                    lmt_profit_pr, stop_pr, tp_lmt_pct, last_pr
                )
            else:
                # log to file
                # logging.error()
                pass


# STOP LOSS ORDER
def place_sl_order(symbol, qty, order_pr, last_pr):

    # STOP LOSS LIMIT price
    lmt_loss_pr = round(
        (order_pr - round(((order_pr / 100) * sl_lmt_pct), 8)), 2
    )

    # STOP LOSS price
    sl_pr = round(
        (order_pr - round(((order_pr / 100) * sl_stop_pct), 8)), 2
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
        backend_args['api_key'], backend_args['api_secret'], base_url='https://api.binance.com'
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
            if backend_args['email_choice']:
                sl_mail_body(
                    error_msg, msg, symbol, qty,
                    lmt_loss_pr, sl_pr, sl_lmt_pct, last_pr
                )
            else:
                # log to file
                # logging.error()
                pass


# OCO mail body
def oco_mail_body(error_msg, msg, symbol, qty, profit_pr, oco_profit_pct, sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr):
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
        oco_profit_pct=str(oco_profit_pct),
        oco_lmt_pct=str(oco_lmt_pct),
        profit_order_value=str(profit_order_value),
        loss_order_value=str(loss_order_value),
        last_pr=str(last_pr)
    )
    send_mail(html)


# Take Profit order mail body
def tp_mail_body(error_msg, msg, symbol, qty, lmt_profit_pr, stop_pr, tp_lmt_pct, last_pr):
    order_value = round((float(qty * lmt_profit_pr)), 2)
    html = template.render(
        error_msg=error_msg,
        title=msg,
        order_type='Take Profit',
        symbol=symbol,
        qty=qty,
        stop_Limit_Price=str(lmt_profit_pr),
        stop_Price=str(stop_pr),
        tp_lmt_pct=str(tp_lmt_pct),
        order_value=str(order_value),
        last_pr=str(last_pr)
    )
    send_mail(html)


# Stop Loss order mail body
def sl_mail_body(error_msg, msg, symbol, qty, lmt_loss_pr, sl_pr, sl_lmt_pct, last_pr):
    order_value = round((float(qty * lmt_loss_pr)), 2)
    html = template.render(
        error_msg=error_msg,
        title=msg,
        order_type='Stop Loss',
        symbol=symbol,
        qty=qty,
        stop_Limit_Price=str(lmt_loss_pr),
        stop_Price=str(sl_pr),
        sl_lmt_pct=str(sl_lmt_pct),
        order_value=str(order_value),
        last_pr=str(last_pr)
    )
    send_mail(html)


# SEND MAIL
def send_mail(html):
    message = MIMEMultipart('alternative')
    message['Subject'] = '[BASD] Binance Algorithmic Stop Daemon - Notification'
    message['From'] = backend_args['valid_sender_email']
    message['To'] = backend_args['valid_receiver_email']

    part = MIMEText(html, 'html')

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(backend_args['valid_sender_email'], backend_args['password'])
        server.sendmail(
            backend_args['valid_sender_email'], backend_args['valid_receiver_email'], message.as_string()
        )


# GET LAST PRICE VIA REST API
def get_last_pr(symbol):
    client = Client(
        backend_args['api_key'], backend_args['api_secret'], base_url='https://api.binance.com'
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
                if backend_args['oco_choice']:
                    place_oco_order(symbol, qty, order_pr, last_pr)
                # TAKE PROFIT order
                if backend_args['tp_choice']:
                    place_tp_order(symbol, qty, order_pr, last_pr)
                # STOP LOSS order
                else:
                    place_sl_order(symbol, qty, order_pr, last_pr)

    except KeyError:
        pass


# CONNECT TO BINANCE.COM
def websocket_connect():
    client = Client(backend_args['api_key'], base_url='https://api.binance.com')
    response = client.new_listen_key()

    logging.info('Receving listen key : {}'.format(response['listenKey']))

    ws_client = SpotWebsocketClient(stream_url='wss://stream.binance.com:9443')
    ws_client.start()

    ws_client.user_data(
        listen_key=response['listenKey'],
        id=1,
        callback=listen_to_filled_orders,
    )


def check_time(backend_args):
    # define email variables in order to be read properly as function arguments
    oco_profit_pct = backend_args['oco_profit_pct']
    oco_sl_pct = backend_args['oco_sl_pct']
    oco_lmt_pct = backend_args['oco_lmt_pct']
    tp_lmt_pct = backend_args['tp_lmt_pct']
    tp_stop_pct = backend_args['tp_stop_pct']
    sl_lmt_pct = backend_args['sl_lmt_pct']
    sl_stop_pct = backend_args['sl_stop_pct']

    # get time zone of specified location
    tmzone = pytz.timezone(backend_args['usr_tz'])

    # change current time accordingly
    now = (datetime.now(tmzone))

    # check if it's time to work or not
    if now.time() >= backend_args['user_start_time_def'] and now.time() <= backend_args['user_end_time_def']:
        # yes
        websocket_connect()
    else:
        # ws_client.stop()
        websocket_connect()