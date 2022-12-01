from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.http import JsonResponse
from .models import JobError
from django.forms.models import model_to_dict
import json
import pytz
import os
import certifi
import time as tempo
from datetime import datetime, timedelta
from binance.websocket.spot.websocket_client import SpotWebsocketClient
from binance.spot import Spot as Client
from binance.error import ClientError

# create Mozilla root certificates
os.environ['SSL_CERT_FILE'] = certifi.where()


def error_list(request):
    errors = JobError.objects.all()
    return JsonResponse(list(map(lambda x: model_to_dict(x), errors)), safe=False)


def getData(request):
    # get ajax dict
    usrdata = json.loads(request.POST['data'])

    request.session['context'] = usrdata
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
            'recvWindow': 6000,
            'quantity': qty,
            'price': str(profit_pr),
            'stopPrice': str(sl_pr_oco),
            'stopLimitPrice': str(sl_lmt_pr_oco)
        }

        client = Client(
            api_key, api_secret, base_url='https://api.binance.com'
        )

        # OCO SELL rule = Limit Price > Last Price > Stop Price
        # OCO BUY rule  = Limit Price < Last Price < Stop Price

        profit_notional = qty * profit_pr
        loss_notional = qty * sl_lmt_pr_oco

        # check if stop and limit prices respect OCO rules, place orders
        if last_pr > sl_pr_oco and last_pr < sl_lmt_pr_oco:

            if profit_notional > 11 and loss_notional > 11:
                try:
                    client.new_oco_order(**params)
                    txt = 'Success! OCO sell order PLACED'
                except ClientError as error:
                    txt = 'Error! OCO sell order NOT PLACED'
                finally:
                    if sender_email_def:
                        oco_mail_body(
                            txt, symbol, qty, profit_pr, oco_profit_pct,
                            sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr
                        )
            else:
                txt = '[ERROR] Orders value must be higher than 11USD'
                if sender_email_def:
                    txt = 'Error! OCO sell order NOT PLACED'
                    oco_mail_body(
                        txt, symbol, qty, profit_pr, oco_profit_pct,
                        sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr
                    )
        else:
            txt = '[ERROR] Prices relationship for the orders not correct. \n' + \
                'OCO SELL rule = Limit Price > Last Price > Stop Price'
            if sender_email_def:
                txt = 'Error! OCO sell order NOT PLACED'
                oco_mail_body(
                    txt, symbol, qty, profit_pr, oco_profit_pct,
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
            api_key, api_secret, base_url='https://api.binance.com'
        )

        notional = qty * lmt_profit_pr

        if stop_pr > last_pr and notional > 11:
            try:
                client.new_order(**params)
                txt = 'Success! Take Profit sell order PLACED'
            except ClientError as error:
                txt = 'Error! Take Profit sell order NOT PLACED'
                print(error)
            finally:
                if sender_email_def:
                    tp_mail_body(
                        txt, symbol, qty,
                        lmt_profit_pr, stop_pr, tp_lmt_pct, last_pr
                    )
        else:
            txt = '[ERROR] Order value must be higher than 11USD'
            if sender_email_def:
                tp_mail_body(
                    txt, symbol, qty,
                    lmt_profit_pr, stop_pr, tp_lmt_pct, last_pr
                )

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
            except ClientError as error:
                txt = 'Error! Stop Loss sell order NOT PLACED'
            finally:
                if sender_email_def:
                    sl_mail_body(
                        txt, symbol, qty,
                        lmt_loss_pr, sl_pr, sl_lmt_pct, last_pr
                    )
        else:
            txt = '[ERROR] Order value must be higher than 11USD'
            if sender_email_def:
                txt = 'Error! Stop Loss sell order NOT PLACED'
                sl_mail_body(
                    txt, symbol, qty,
                    lmt_loss_pr, sl_pr, sl_lmt_pct, last_pr
                )

    # OCO email body
    def oco_mail_body(txt, symbol, qty, profit_pr, oco_profit_pct, sl_lmt_pr_oco, sl_pr_oco, oco_lmt_pct, last_pr):

        profit_order_value = round((float(qty * profit_pr)), 2)
        loss_order_value = round((float(qty * sl_lmt_pr_oco)), 2)

        context = {
            'title': txt,
            'order_type': 'OCO',
            'symbol': symbol,
            'qty': qty,
            'price': str(profit_pr),
            'stop_Limit_Price': str(sl_lmt_pr_oco),
            'stop_Price': str(sl_pr_oco),
            'oco_profit_pct': str(oco_profit_pct),
            'oco_lmt_pct': str(oco_lmt_pct),
            'profit_order_value': str(profit_order_value),
            'loss_order_value': str(loss_order_value),
            'last_pr': str(last_pr)
        }

        send_email(context)

    # Take Profit email body
    def tp_mail_body(txt, symbol, qty, lmt_profit_pr, stop_pr, tp_lmt_pct, last_pr):

        order_value = round((float(qty * lmt_profit_pr)), 2)

        context = {
            'title': txt,
            'order_type': 'Take Profit',
            'symbol': symbol,
            'qty': qty,
            'stop_Limit_Price': str(lmt_profit_pr),
            'stop_Price': str(stop_pr),
            'tp_lmt_pct': str(tp_lmt_pct),
            'order_value': str(order_value),
            'last_pr': str(last_pr)
        }

        send_email(context)

    # Stop Loss email body
    def sl_mail_body(txt, symbol, qty, lmt_loss_pr, sl_pr, sl_lmt_pct, last_pr):

        order_value = round((float(qty * lmt_loss_pr)), 2)

        context = {
            'title': txt,
            'order_type': 'Stop Loss',
            'symbol': symbol,
            'qty': qty,
            'stop_Limit_Price': str(lmt_loss_pr),
            'stop_Price': str(sl_pr),
            'sl_lmt_pct': str(sl_lmt_pct),
            'order_value': str(order_value),
            'last_pr': str(last_pr)
        }

        send_email(context)

    # SEND EMAIL
    def send_email(context):
        html_content = render_to_string('email.html', context)
        send_email.called = True
        email_subject = '[BASD] Binance Automatic Stop Daemon - Notification'
        msg = ''
        send_mail(subject=email_subject, message=msg, from_email=sender_email_def, recipient_list=[receiver_email_def], fail_silently=False, html_message=html_content, auth_user=sender_email_def, auth_password=password_def)

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
# #########################################################################################################
                if order_status == 'CANCELED' and side == 'BUY':  # CHANGE MEEEEEEEEEEEEEEEEEEEEEEEEE TO FILLED
                    # get global variables
                    # order_pr = float(message['p']) # #########################################################################################################
                    order_pr = 20763

                    symbol = message['s']

                    # qty = float(message['q']) # #########################################################################################################
                    qty = 0.00052

                    # get LAST SYMBOL PRICE
                    last_pr = get_last_pr(symbol)

                    # OCO order
                    if orderType == 'OCO':
                        place_oco_order(symbol, qty, order_pr, last_pr)
                    # TAKE PROFIT order
                    if orderType == 'tp':
                        place_tp_order(symbol, qty, order_pr, last_pr)
                    # STOP LOSS order
                    else:
                        place_sl_order(symbol, qty, order_pr, last_pr)
        except KeyError:
            pass

    job_error = JobError()
    # SET GLOBAL VARIABLES
    context = {}
    send_email.called = False
    api_key = usrdata['api_key']
    api_secret = usrdata['api_secret']
    uuid = usrdata['id']
    usr_tz = usrdata['tz']
    start_time = usrdata['start_time']
    working_ival = int(usrdata['active_hours'])
    orderType = usrdata['order_type']
    sender_email = dict((k, usrdata[k]) for k in ['sender_email'] if k in usrdata)
    sender_email_def = ' '.join(map(str, sender_email.values()))
    password = dict((k, usrdata[k]) for k in ['password'] if k in usrdata)
    password_def = ' '.join(map(str, password.values()))
    receiver_email = dict((k, usrdata[k]) for k in ['receiver_email'] if k in usrdata)
    receiver_email_def = ' '.join(map(str, receiver_email.values()))
    if orderType == 'oco':
        oco_profit_pct = float(usrdata['oco_tp'])
        oco_sl_pct = float(usrdata['oco_sl_s'])
        oco_lmt_pct = float(usrdata['oco_sl_l'])
        context.update({'order_type': 'OCO', 'oco_tp': oco_profit_pct, 'oco_sl_stop': oco_sl_pct, 'oco_sl_lmt': oco_lmt_pct})
    if orderType == 'tp':
        tp_stop_pct = float(usrdata['tp_s'])
        tp_lmt_pct = float(usrdata['tp_l'])
        context.update({'order_type': 'Take Profit', 'tp_stop': tp_stop_pct, 'tp_lmt': tp_lmt_pct})
    if orderType == 'sl':
        sl_stop_pct = float(usrdata['sl_s'])
        sl_lmt_pct = float(usrdata['sl_l'])
        context.update({'order_type': 'Stop Loss', 'sl_stop': sl_stop_pct, 'sl_lmt': sl_lmt_pct})

    # get time zone of specified location
    tmzone = pytz.timezone(usr_tz)

    # change current time accordingly
    now = (datetime.now(tmzone))

    # construct user end time
    converted_start_time = datetime.strptime(start_time, '%H:%M')
    usr_start_time = now.replace(hour=converted_start_time.hour, minute=converted_start_time.minute)
    usr_end_time = (usr_start_time + timedelta(hours=working_ival))

    # check if it's time to work or not
    if now >= usr_start_time and now <= usr_end_time:  # yes
        try:
            job = ' JOB ' + uuid
            nowstr = str(now.time())[:8]

            client = Client(api_key, base_url='https://api.binance.com')
            response = client.new_listen_key()

            ws_client = SpotWebsocketClient(stream_url='wss://stream.binance.com:9443')
            ws_client.start()

            ws_client.user_data(
                listen_key=response['listenKey'],
                id=1,
                callback=listen_to_filled_orders,
            )

            title = 'Success! ' + job + 'started at ' + nowstr
        except ClientError:
            title = 'Error! API-keys format invalid, check your keys!' + job + ' NOT started at ' + nowstr
            job_error.error = uuid
            job_error.save()
            # tempo.sleep(10)
            # job_error.delete()
        finally:
            if sender_email_def and not send_email.called:
                context.update({'first_email': True, 'title': title})
                send_email(context)
    else:
        txt1 = 'It\'s not time to work!\nStart time: ' + (str(usr_start_time))[:16]
        txt2 = '\nEnd time: ' + (str(usr_end_time))[:16]
        txt3 = '\nTimezone is ' + usr_tz
        title = txt1 + txt2 + txt3
        if sender_email_def and not send_email.called:
            context.update({'first_email': True, 'title': title})
            send_email(context)
            pass

        pass

    # ws_client.stop()

    return render(request, 'index.html')

