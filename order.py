#!/usr/bin/env python3

# IMPORTS
import PySimpleGUI as sg

import io
import logging
import os

import pytz
from datetime import datetime
import time as tempo

from binance.websocket.spot.websocket_client import SpotWebsocketClient
from binance.spot import Spot as Client
from binance.error import ClientError

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

from jinja2 import Environment, FileSystemLoader

# load jinja2 template
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('mail.html')


# SET LOGGING STDOUT TO GUI
output = io.StringIO()
logging.basicConfig(stream=output, level=logging.DEBUG)


# OPTIONAL LOGGING STDOUT TO FILE
def logtofile():
    logging.getLogger('')
    logging.basicConfig(
        level=logging.DEBUG,
        filename=os.path.basename(__file__) + '.log',
        format='{asctime} [{levelname:8}] {process} {thread} {module}: {message}',
        style='{'
    )


# CONNECT TO BINANCE.COM
def websocket_connect(usrdata):

    # PLACE OCO ORDER
    def place_oco_order(window, symbol, qty, order_pr, last_pr):

        email_choice = usrdata['email_choice']

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
            'recvWindow': 6000,
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
                txt = 'Success! OCO sell order PLACED'
                log_response = output.getvalue()
                window['-OUTPUT-'].print(log_response, text_color='green', font=('Helvetica', 12))
            except ClientError as error:
                txt = 'Error! OCO sell order NOT PLACED'
                window['-OUTPUT-'].print(str(error), text_color='red', font=('Helvetica', 12))
            finally:
                if email_choice is True:
                    oco_mail_body(
                        txt, symbol, qty, profit_pr, oco_profit_pct,
                        sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr
                    )
                else:
                    logtofile()
                    pass

        else:
            txt = '[ERROR]Prices relationship for the orders not correct. \n' + \
                'OCO SELL rule = Limit Price > Last Price > Stop Price'
            window['-OUTPUT-'].print(txt, text_color='red', font=('Helvetica', 12))
            if email_choice is True:
                txt = 'Error! OCO sell order NOT PLACED'
                oco_mail_body(
                    txt, symbol, qty, profit_pr, oco_profit_pct,
                    sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr
                )

    # PLACE TAKE PROFIT ORDER
    def place_tp_order(window, symbol, qty, order_pr, last_pr):

        email_choice = usrdata['email_choice']

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
            'recvWindow': 6000,
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
                txt = 'Success! Take Profit sell order PLACED'
                log_response = output.getvalue()
                window['-OUTPUT-'].print(log_response, text_color='green', font=('Helvetica', 12))
            except ClientError as error:
                txt = 'Error! Take Profit sell order NOT PLACED'
                window['-OUTPUT-'].print(str(error), text_color='red', font=('Helvetica', 12))
            finally:
                if email_choice is True:
                    tp_mail_body(
                        txt, symbol, qty,
                        lmt_profit_pr, stop_pr, tp_lmt_pct, last_pr
                    )
                else:
                    logtofile()

                pass

    # STOP LOSS ORDER
    def place_sl_order(window, symbol, qty, order_pr, last_pr):

        email_choice = usrdata['email_choice']

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
            'recWindow': 6000,
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
                txt = 'Success! Stop Loss sell order PLACED'
                log_response = output.getvalue()
                window['-OUTPUT-'].print(log_response, text_color='green', font=('Helvetica', 12))
            except ClientError as error:
                txt = 'Error! Stop Loss sell order NOT PLACED'
                window['-OUTPUT-'].print(str(error), text_color='red', font=('Helvetica', 12))
            finally:
                if email_choice is True:
                    sl_mail_body(
                        txt, symbol, qty,
                        lmt_loss_pr, sl_pr, sl_lmt_pct, last_pr
                    )
                else:
                    logtofile()
                pass

    # OCO email body
    def oco_mail_body(txt, symbol, qty, profit_pr, oco_profit_pct, sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr):

        profit_order_value = round((float(qty * profit_pr)), 2)
        loss_order_value = round((float(qty * sl_lmt_pr_oco)), 2)

        html = template.render(
            title=txt,
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
        send_email(html)

    # Take Profit email body
    def tp_mail_body(txt, symbol, qty, lmt_profit_pr, stop_pr, tp_lmt_pct, last_pr):

        order_value = round((float(qty * lmt_profit_pr)), 2)

        html = template.render(
            title=txt,
            order_type='Take Profit',
            symbol=symbol,
            qty=qty,
            stop_Limit_Price=str(lmt_profit_pr),
            stop_Price=str(stop_pr),
            tp_lmt_pct=str(tp_lmt_pct),
            order_value=str(order_value),
            last_pr=str(last_pr)
        )
        send_email(html)

    # Stop Loss email body
    def sl_mail_body(txt, symbol, qty, lmt_loss_pr, sl_pr, sl_lmt_pct, last_pr):

        order_value = round((float(qty * lmt_loss_pr)), 2)

        html = template.render(
            title=txt,
            order_type='Stop Loss',
            symbol=symbol,
            qty=qty,
            stop_Limit_Price=str(lmt_loss_pr),
            stop_Price=str(sl_pr),
            sl_lmt_pct=str(sl_lmt_pct),
            order_value=str(order_value),
            last_pr=str(last_pr)
        )
        send_email(html)

    # SEND MAIL
    def send_email(html):

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

    # GET LAST PRICE VIA REST API
    def get_last_pr(symbol):

        client = Client(api_key, api_secret, base_url='https://api.binance.com')
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

                if order_status == 'CANCELED' and side == 'BUY':             # CHANGE ME!!!!!!!!!!!
                    # get global variables
                    # order_pr = float(message['p'])
                    order_pr = 20763

                    symbol = message['s']

                    # qty = flot(message['q'])
                    qty = 0.00052

                    # get LAST SYMBOL PRICE
                    last_pr = get_last_pr(symbol)

                    # OCO order
                    if 'oco_choice' in usrdata:
                        place_oco_order(window, symbol, qty, order_pr, last_pr)
                    # TAKE PROFIT order
                    if 'tp_choice' in usrdata:
                        place_tp_order(window, symbol, qty, order_pr, last_pr)
                    # STOP LOSS order
                    else:
                        place_sl_order(window, symbol, qty, order_pr, last_pr)
        except KeyError:
            pass

    # define global variables in order to be read properly as function arguments
    api_key = usrdata['api_key']
    api_secret = usrdata['api_secret']
    usr_tz = usrdata['usr_tz']
    user_starttime = usrdata['user_start_time_def']
    user_endtime = usrdata['user_end_time_def']
    try:
        if usrdata['email_choice'] is True:
            sender_email = usrdata['valid_sender_email']
            password = usrdata['password']
            receiver_email = usrdata['valid_receiver_email']
    except KeyError:
        pass
    if 'oco_choice' in usrdata:
        oco_profit_pct = usrdata['oco_profit_pct']
        oco_sl_pct = usrdata['oco_sl_pct']
        oco_lmt_pct = usrdata['oco_lmt_pct']
    elif 'tp_choice' in usrdata:
        tp_stop_pct = usrdata['tp_stop_pct']
        tp_lmt_pct = usrdata['tp_lmt_pct']
    else:
        sl_lmt_pct = usrdata['sl_lmt_pct']
        sl_stop_pct = usrdata['sl_stop_pct']

    # GUI INITIALIZATION
    sg.theme('Default 1')

    layout = [
            [sg.Text('BASD', font=("Helvetica", 18, 'bold')), sg.Push()],
            [sg.Text('Output', font=('Helvetica', 12)), sg.Push()],
            [sg.MLine(size=(80, 10), reroute_stdout=True, autoscroll=True, k='-OUTPUT-')],
            [sg.Button('Refresh', tooltip='Get latest data from Binance websocket'),
                sg.Button('Quit', tooltip='Closing program will stop listening to orders!')],
            ]

    # Create the window
    window = sg.Window('Binance Algorithmic Stop Daemon', layout)

    while True:
        event, values = window.read()

        # get time zone of specified location
        tmzone = pytz.timezone(usr_tz)

        # change current time accordingly
        now = (datetime.now(tmzone))

        # check if it's time to work or not
        if now.time() >= user_starttime and now.time() <= user_endtime:
            # yes
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

            # grab logging output
            log_response = output.getvalue()
            window['-OUTPUT-'].print(log_response, font=('Helvetica', 12))
        else:
            txt1 = 'It\'s not time to work!\nStart time: ' + str(user_starttime)
            txt2 = '\nEnd time: ' + str(user_endtime)
            txt3 = '\nTimezone is ' + usr_tz
            message = txt1 + txt2 + txt3
            window['-OUTPUT-'].print(message, font=('Helvetica', 12))
            tempo.sleep(2)
            pass

        if event == sg.WINDOW_CLOSED or event == 'Quit':
            try:
                ws_client.stop()
            except UnboundLocalError:
                break
            finally:
                break

    window.close()
