#!/usr/bin/env python3

from backend import websocket_connect

import PySimpleGUI as sg

from datetime import datetime, timedelta
import pytz
from curses.ascii import isalpha
import re

# pattern for email validation
regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

# initialize DATA dictionary
frontend_args = {}


# VALIDATION
def is_hour(window, input):
    try:
        input = int(input)
        if input >= 1 and input <= 24:
            return input
        else:
            window['TABLEDATA'].print('[ERROR] Type a valid value between 1 and 24', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
    except ValueError:
        window['TABLEDATA'].print('[ERROR] Type only numbers', text_color='red', font=('Helvetica', 14))
        window['Confirm'].update(disabled=True)


def is_valid_time(window, input):
    timeformat = '%H:%M'
    try:
        input = datetime.strptime(input, timeformat)
        window['TABLEDATA'].print('[OK] Start Time', text_color='green', font=('Helvetica', 14))
        window['Confirm'].update(disabled=False)
        return str(input.time())
    except ValueError:
        window['TABLEDATA'].print('[ERROR] Type a valid time format, e.g. 15:30', text_color='red', font=('Helvetica', 14))
        window['Confirm'].update(disabled=True)


def is_email(window, input):
    if re.fullmatch(regex, input):
        window['Confirm'].update(disabled=False)
        return input
    else:
        window['TABLEDATA'].print('[ERROR] Invalid email address', text_color='red', font=('Helvetica', 14))
        window['Confirm'].update(disabled=True)


def is_float(window, input):
    try:
        input = float(input)
        if input >= 0.05 and input <= 2999.99:
            window['Confirm'].update(disabled=False)
            return input
        else:
            window['TABLEDATA'].print('[ERROR] Type a valid value between 0.05 and 2999.99', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
    except ValueError:
        window['TABLEDATA'].print('[ERROR] Type only numbers ', text_color='red', font=('Helvetica', 14))
        window['Confirm'].update(disabled=True)


def main():
    sg.theme('Default 1')

    left_column = [
        [sg.Text('BASD', font=('Helvetica', 18, 'bold')), sg.Push()],
        [sg.Push(), sg.Text('Required fields', font=('Helvetica', 12, 'italic'))],
        [sg.Text('API Key', font=('Helvetica', 12)), sg.Push(), sg.Input(k='APIKEY', enable_events=True, font=('Helvetica', 12), tooltip='Type or paste your Binance.com API KEY', password_char='*')],
        [sg.Text('API Secret', font=('Helvetica', 12)), sg.Push(), sg.Input(k='APISECRET', enable_events=True, font=('Helvetica', 12), tooltip='Type or paste your Binance.com SECRET KEY', password_char='*')],
        [sg.Text('Timezone Continent', font=('Helvetica', 12)), sg.Push(), sg.Input(k='CONTINENT', enable_events=True, font=('Helvetica', 12), tooltip='Type your CONTINENT (IANA timezone format) e.g. Europe')],
        [sg.Text('Timezone City', font=('Helvetica', 12)), sg.Push(), sg.Input(k='CITY', enable_events=True, font=('Helvetica', 12), tooltip='Type your CITY (IANA timezone format) e.g. Rome')],
        [sg.Text('Start Time', font=('Helvetica', 12)), sg.Push(), sg.Input(k='STARTTIME', enable_events=True, font=('Helvetica', 12), tooltip='Type START TIME (1-24h)(0-59m) e.g. 23:45')],
        [sg.Text('Active Hours', font=('Helvetica', 12)), sg.Push(), sg.Input(k='WORKINGINTERVAL', enable_events=True, font=('Helvetica', 12), tooltip='Type how many working HOURS you want. 24 equals to all day, e.g. 8')],
        [sg.Text('End Time', font=('Helvetica', 12)), sg.Push(), sg.Input(k='ENDTIME', enable_events=True, font=('Helvetica', 12))],
        [sg.Checkbox('Email Notification', font=('Helvetica', 12), default=True, k='EMAILCHOICE', enable_events=True)],
        [sg.Text('Gmail Sender Address', font=('Helvetica', 12), k='SENDEREMAILTXT'), sg.Push(), sg.Input(k='SENDEREMAIL', enable_events=True, font=('Helvetica', 12), tooltip='Type sender email address (GMAIL only)')],
        [sg.Text('Gmail App Password', font=('Helvetica', 12), k='PASSWORDTXT'), sg.Push(), sg.Input(k='PASSWORD', enable_events=True, font=('Helvetica', 12), tooltip='Type or paste your gmail app password', password_char='*')],
        [sg.Text('Receiver Address', font=('Helvetica', 12), k='RECEIVEREMAILTXT'), sg.Push(), sg.Input(k='RECEIVEREMAIL', enable_events=True, font=('Helvetica', 12), tooltip='Type receiver email address')],
        # [sg.StatusBar('', size=(0, 1), key='STATUS')],
    ]

    right_column = [
        [sg.Radio('Take Profit', group_id=1, font=('Helvetica', 12), enable_events=True, k='TPCHOICE'), sg.Radio('Stop Loss', group_id=1, font=('Helvetica', 12), enable_events=True, k='SLCHOICE'), sg.Radio('OCO', group_id=1, font=('Helvetica', 12), enable_events=True, k='OCOCHOICE')],
        # OCO
        [sg.Text('Take Profit +%', font=('Helvetica', 12), k='OCOTPTXT'), sg.Push(), sg.Input(k='OCOTP', enable_events=True, font=('Helvetica', 12), tooltip='Type OCO Take Profit percentage, e.g. 5.20')],
        [sg.Text('Stop Loss -%', font=('Helvetica', 12), k='OCOSLTXT'), sg.Push(), sg.Input(k='OCOSL', enable_events=True, font=('Helvetica', 12), tooltip='Type OCO Stop Loss percentage. This should be LOWER than symbol market price WHEN order will be placed, e.g. 1.20')],
        [sg.Text('Limit Loss -%', font=('Helvetica', 12), k='OCOLLTXT'), sg.Push(), sg.Input(k='OCOLL', enable_events=True, font=('Helvetica', 12), tooltip='Type OCO Stop Loss Limit percentage. This should be HIGHER than symbol market price WHEN order will be placed, e.g. 1.05')],
        # TAKE PROFIT
        [sg.Text('Stop Profit +%', font=('Helvetica', 12), k='TPSLTXT'), sg.Push(), sg.Input(k='TPSL', enable_events=True, font=('Helvetica', 12), tooltip='Type Take Profit Stop percentage, e.g. 5.25')],
        [sg.Text('Limit Profit +%', font=('Helvetica', 12), k='TPLTXT'), sg.Push(), sg.Input(k='TPL', enable_events=True, font=('Helvetica', 12), tooltip='Type Take Profit Limit percentage, e.g. 5.20')],
        # STOP LOSS
        [sg.Text('Stop Loss -%', font=('Helvetica', 12), k='SLTXT'), sg.Push(), sg.Input(k='SL', enable_events=True, font=('Helvetica', 12), tooltip='Type Stop Loss Stop percentage, e.g. 1.10')],
        [sg.Text('Limit Loss -``%', font=('Helvetica', 12), k='SLLTXT'), sg.Push(), sg.Input(k='SLL', enable_events=True, font=('Helvetica', 12), tooltip='Type Stop Loss Limit percentage, e.g. 1.15')],
        # TABLEDATA
        [sg.Text('Output', font=('Helvetica', 12))],
        [sg.MLine(size=(80, 10), autoscroll=True, reroute_stdout=True, write_only=True, reroute_cprint=True, k='TABLEDATA')],
        # BUTTONS
        [sg.Push(), sg.Button('Confirm', font=('Helvetica', 12)), sg.Button('Edit', font=('Helvetica', 12)), sg.Button('Quit', font=('Helvetica', 12))],
        # SOFTWARE VERSION
        [sg.Push(), sg.Text('Powered by EScomputers v1.16.1', font=('Helvetica', 9, 'italic'))]
    ]

    # Full layout
    layout = [
        [
            sg.Column(left_column),
            sg.VSeperator(),
            sg.Column(right_column)
        ]
    ]

    # Create the window
    window = sg.Window('Binance Algorithmic Stop Daemon', layout)

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()

        # email section visible by default
        window['SENDEREMAILTXT'].update(visible=True)
        window['SENDEREMAIL'].update(visible=True)
        window['PASSWORDTXT'].update(visible=True)
        window['PASSWORD'].update(visible=True)
        window['RECEIVEREMAILTXT'].update(visible=True)
        window['RECEIVEREMAIL'].update(visible=True)

        # order section hidden by default
        window['OCOTPTXT'].update(visible=False)
        window['OCOTP'].update(visible=False)
        window['OCOSLTXT'].update(visible=False)
        window['OCOSL'].update(visible=False)
        window['OCOLLTXT'].update(visible=False)
        window['OCOLL'].update(visible=False)
        window['TPSLTXT'].update(visible=False)
        window['TPSL'].update(visible=False)
        window['TPLTXT'].update(visible=False)
        window['TPL'].update(visible=False)
        window['SLTXT'].update(visible=False)
        window['SL'].update(visible=False)
        window['SLLTXT'].update(visible=False)
        window['SLL'].update(visible=False)

        # define global variables
        api_key = values['APIKEY']
        api_secret = values['APISECRET']
        tz_cont = values['CONTINENT']
        tz_city = values['CITY']
        inp_start_time = values['STARTTIME']
        inp_working_ival = values['WORKINGINTERVAL']
        tp_choice = values['TPCHOICE']
        sl_choice = values['SLCHOICE']
        oco_choice = values['OCOCHOICE']
        email_choice = values['EMAILCHOICE']
        sender_email = values['SENDEREMAIL']
        password = values['PASSWORD']
        receiver_email = values['RECEIVEREMAIL']
        inp_oco_profit_pct = values['OCOTP']
        inp_oco_sl_pct = values['OCOSL']
        inp_oco_lmt_pct = values['OCOLL']
        inp_tp_stop_pct = values['TPSL']
        inp_tp_lmt_pct = values['TPL']
        inp_sl_stop_pct = values['SL']
        inp_sl_lmt_pct = values['SLL']

        # validate API KEY
        if api_key:
            if len(api_key) < 64:
                window['TABLEDATA'].print('[ERROR] Check your API Key, 64 characters minimum, no spaces', text_color='red', font=('Helvetica', 14))
                window['Confirm'].update(disabled=True)
            else:
                window['TABLEDATA'].print('[OK] API Key', text_color='green', font=('Helvetica', 14))
                window['Confirm'].update(disabled=False)

        # validate API SECRET KEY
        if api_secret:
            if len(api_secret) < 64:
                window['TABLEDATA'].print('[ERROR] Check your API Secret Key, 64 characters minimum, no spaces', text_color='red', font=('Helvetica', 14))
                window['Confirm'].update(disabled=True)
            else:
                window['TABLEDATA'].print('[OK] API Secret Key', text_color='green', font=('Helvetica', 14))
                window['Confirm'].update(disabled=False)

        # validate API SECRET KEY as required
        if api_key and not api_secret:
            window['TABLEDATA'].print('[ERROR] Api Secret Key cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # validate API KEY as required
        if api_secret and not api_key:
            window['TABLEDATA'].print('[ERROR] Api Key cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # validate API KEYS
        if len(api_key) >= 64 and len(api_secret) >= 64:
            if api_key == api_secret:
                window['TABLEDATA'].print('[ERROR] API Key and API Secret Key cannot be the same', text_color='red', font=('Helvetica', 14))
                window['Confirm'].update(disabled=True)
            else:
                window['TABLEDATA'].print('[OK] API Key and API Secret Key', text_color='green', font=('Helvetica', 14))
                window['Confirm'].update(disabled=False)
                frontend_args.update({'api_key': api_key, 'api_secret': api_secret})

        # validate TIMEZONE CONTINENT
        if tz_cont:
            if tz_cont.isalpha():
                window['TABLEDATA'].print('[OK] Timezone Continent format', text_color='green', font=('Helvetica', 14))
                window['Confirm'].update(disabled=False)
            else:
                window['TABLEDATA'].print('[ERROR] Type only letters', text_color='red', font=('Helvetica', 14))
                window['Confirm'].update(disabled=True)

        # validate TIMEZONE CITY
        if tz_city:
            if tz_city.isalpha():
                window['TABLEDATA'].print('[OK] Timezone City format', text_color='green', font=('Helvetica', 14))
                window['Confirm'].update(disabled=False)
            else:
                window['TABLEDATA'].print('[ERROR] Type only letters', text_color='red', font=('Helvetica', 14))
                window['Confirm'].update(disabled=True)

        # validate TIMEZONE CONTINENT as required
        if tz_city and not tz_cont:
            window['TABLEDATA'].print('[ERROR] Timezone Continent cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # validate TIMEZONE CITY as required
        if tz_cont and not tz_city:
            window['TABLEDATA'].print('[ERROR] Timezone City cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # validate TIMEZONE
        if tz_cont.isalpha() and tz_city.isalpha():
            usr_tz = tz_cont.capitalize() + '/' + tz_city.capitalize()
            if usr_tz in pytz.all_timezones:
                frontend_args.update({'usr_tz': usr_tz})
                window['TABLEDATA'].print('[OK] Timezone', text_color='green', font=('Helvetica', 14))
                window['CONTINENT'].update(tz_cont.capitalize())
                window['CITY'].update(tz_city.capitalize())
                window['Confirm'].update(disabled=False)
            else:
                window['TABLEDATA'].print(
                        '[ERROR] Timezone: ' + tz_cont.capitalize() + '/' + tz_city.capitalize() +
                        ' you entered is not valid. \n ', text_color='red', font=('Helvetica', 14)
                    )
                window['Confirm'].update(disabled=True)

        # validate START TIME
        if inp_start_time:
            if is_valid_time(window, inp_start_time):
                start_time = is_valid_time(window, inp_start_time)
                user_start_time = datetime.strptime(str(start_time)[:-3], '%H:%M')  # used for calc
                user_start_time_def = datetime.strptime(str(start_time)[:-3], '%H:%M').time()  # used for backend function

        # validate WORKING INTERVAL
        if inp_working_ival:
            if is_hour(window, inp_working_ival):
                working_ival = is_hour(window, inp_working_ival)

        # validate WORKING INTERVAL as required
        if inp_start_time and not inp_working_ival:
            window['TABLEDATA'].print('[ERROR] Active Hours cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # validate START TIME as required
        if inp_working_ival and not inp_start_time:
            window['TABLEDATA'].print('[ERROR] Start Time cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # construct USER END TIME
        try:
            if user_start_time and working_ival:
                end_time = (user_start_time + timedelta(hours=working_ival)).time()
                user_end_time = str(end_time)[:-3]  # remove seconds from string
                user_end_time_def = datetime.strptime(user_end_time, '%H:%M').time()
                window['ENDTIME'].update(user_end_time)
                window['Confirm'].update(disabled=False)
                frontend_args.update({'user_start_time_def': user_start_time_def, 'user_end_time_def': user_end_time_def})
        except UnboundLocalError:
            continue

        # show order inputs according to radio buttons
        if tp_choice:
            frontend_args.update({'tp_choice': tp_choice})
            window['TPSLTXT'].update(visible=True)
            window['TPSL'].update(visible=True)
            window['TPLTXT'].update(visible=True)
            window['TPL'].update(visible=True)
            window['OCOTPTXT'].update(visible=False)
            window['OCOTP'].update(visible=False)
            window['OCOSLTXT'].update(visible=False)
            window['OCOSL'].update(visible=False)
            window['OCOLLTXT'].update(visible=False)
            window['OCOLL'].update(visible=False)
            window['SLTXT'].update(visible=False)
            window['SL'].update(visible=False)
            window['SLLTXT'].update(visible=False)
            window['SLL'].update(visible=False)
        if sl_choice:
            window['SLTXT'].update(visible=True)
            window['SL'].update(visible=True)
            window['SLLTXT'].update(visible=True)
            window['SLL'].update(visible=True)
            window['TPSLTXT'].update(visible=False)
            window['TPSL'].update(visible=False)
            window['TPLTXT'].update(visible=False)
            window['TPL'].update(visible=False)
            window['OCOTPTXT'].update(visible=False)
            window['OCOTP'].update(visible=False)
            window['OCOSLTXT'].update(visible=False)
            window['OCOSL'].update(visible=False)
            window['OCOLLTXT'].update(visible=False)
            window['OCOLL'].update(visible=False)
        if oco_choice:
            frontend_args.update({'oco_choice': oco_choice})
            window['OCOTPTXT'].update(visible=True)
            window['OCOTP'].update(visible=True)
            window['OCOSLTXT'].update(visible=True)
            window['OCOSL'].update(visible=True)
            window['OCOLLTXT'].update(visible=True)
            window['OCOLL'].update(visible=True)
            window['SLTXT'].update(visible=False)
            window['SL'].update(visible=False)
            window['SLLTXT'].update(visible=False)
            window['SLL'].update(visible=False)
            window['TPSLTXT'].update(visible=False)
            window['TPSL'].update(visible=False)
            window['TPLTXT'].update(visible=False)
            window['TPL'].update(visible=False)

        # get EMAIL CHOICE
        if email_choice == False:
            window['SENDEREMAILTXT'].update(visible=False)
            window['SENDEREMAIL'].update(visible=False)
            window['PASSWORDTXT'].update(visible=False)
            window['PASSWORD'].update(visible=False)
            window['RECEIVEREMAILTXT'].update(visible=False)
            window['RECEIVEREMAIL'].update(visible=False)

        # validate SENDER MAIL as required field
        if email_choice and not sender_email:
            window['TABLEDATA'].print('[ERROR] Gmail Sender Address cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # validate SENDER EMAIL
        if sender_email:
            if is_email(window, sender_email):
                valid_sender_email = is_email(window, sender_email)
                if '@gmail.com' in valid_sender_email:
                    window['TABLEDATA'].print('[OK] Valid sender email address', text_color='green', font=('Helvetica', 14))
                    window['Confirm'].update(disabled=False)
                else:
                    window['TABLEDATA'].print('[ERROR] Only Gmail account currently supported', text_color='red', font=('Helvetica', 14))
                    window['Confirm'].update(disabled=True)

        # validate PASSWORD
        if sender_email and not password or receiver_email and not password:
            window['TABLEDATA'].print('[ERROR] Password cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
        if sender_email and password and receiver_email and password:
            window['TABLEDATA'].print('[OK] Password not empty', text_color='green', font=('Helvetica', 14))
            window['Confirm'].update(disabled=False)

        # validate RECEIVER EMAIL
        if receiver_email:
            if is_email(window, receiver_email):
                valid_receiver_email = is_email(window, receiver_email)
                window['TABLEDATA'].print('[OK] Valid receiver email address', text_color='green', font=('Helvetica', 14))
                frontend_args.update({'email_choice': email_choice, 'valid_sender_email': valid_sender_email, 'password': password, 'valid_receiver_email': valid_receiver_email})

        # validate RECEIVER EMAIL as required
        if sender_email and not receiver_email or password and not receiver_email:
            window['TABLEDATA'].print('[ERROR] Receiver Email Address cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # validate ORDER inputs
        # OCO
        if inp_oco_profit_pct:
            if is_float(window, inp_oco_profit_pct):
                oco_profit_pct = is_float(window, inp_oco_profit_pct)
                window['TABLEDATA'].print('[OK] Valid OCO Take Profit +%', text_color='green', font=('Helvetica', 14))
        if inp_oco_sl_pct:
            if is_float(window, inp_oco_sl_pct):
                oco_sl_pct = is_float(window, inp_oco_sl_pct)
                window['TABLEDATA'].print('[OK] Valid OCO Stop Loss -%', text_color='green', font=('Helvetica', 14))
        if inp_oco_lmt_pct:
            if is_float(window, inp_oco_lmt_pct):
                oco_lmt_pct = is_float(window, inp_oco_lmt_pct)
                window['TABLEDATA'].print('[OK] Valid OCO Stop Loss Limit -%', text_color='green', font=('Helvetica', 14))
                frontend_args.update({'oco_profit_pct': oco_profit_pct, 'oco_sl_pct': oco_sl_pct, 'oco_lmt_pct': oco_lmt_pct})

        # validate OCO fields ar required
        if oco_choice and not inp_oco_profit_pct or oco_choice and not inp_oco_sl_pct or oco_choice and not inp_oco_lmt_pct:
            window['TABLEDATA'].print('[ERROR] OCO fields cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
        if inp_oco_profit_pct and not inp_oco_sl_pct or inp_oco_profit_pct and not inp_oco_lmt_pct:
            window['TABLEDATA'].print('[ERROR] OCO Take Profit cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
        if inp_oco_sl_pct and not inp_oco_profit_pct or inp_oco_sl_pct and not inp_oco_lmt_pct:
            window['TABLEDATA'].print('[ERROR] OCO Stop Loss cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
        if inp_oco_lmt_pct and not inp_oco_sl_pct or inp_oco_lmt_pct and not inp_oco_profit_pct:
            window['TABLEDATA'].print('[ERROR] OCO Stop Loss Limit cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # TP
        if inp_tp_stop_pct:
            if is_float(window, inp_tp_stop_pct):
                tp_stop_pct = is_float(window, inp_tp_stop_pct)
                window['TABLEDATA'].print('[OK] Valid Take Profit Stop +%', text_color='green', font=('Helvetica', 14))
        if inp_tp_lmt_pct:
            if is_float(window, inp_tp_lmt_pct):
                tp_lmt_pct = is_float(window, inp_tp_lmt_pct)
                window['TABLEDATA'].print('[OK] Valid Take Profit Stop Limit +%', text_color='green', font=('Helvetica', 14))
                frontend_args.update({'tp_stop_pct': tp_stop_pct, 'tp_lmt_pct': tp_lmt_pct})

        # validate TP fields ar required
        if tp_choice and not inp_tp_stop_pct or tp_choice and not inp_tp_lmt_pct:
            window['TABLEDATA'].print('[ERROR] Take Profit fields cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
        if inp_tp_stop_pct and not inp_tp_lmt_pct:
            window['TABLEDATA'].print('[ERROR] Take Profit Stop cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
        if inp_tp_lmt_pct and not inp_tp_stop_pct:
            window['TABLEDATA'].print('[ERROR] Take Profit Limit cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        # SL
        if inp_sl_stop_pct:
            if is_float(window, inp_sl_stop_pct):
                sl_stop_pct = is_float(window, inp_sl_stop_pct)
                window['TABLEDATA'].print('[OK] Valid Stop Loss Stop -%', text_color='green', font=('Helvetica', 14))
        if inp_sl_lmt_pct:
            if is_float(window, inp_sl_lmt_pct):
                sl_lmt_pct = is_float(window, inp_sl_lmt_pct)
                window['TABLEDATA'].print('[OK] Valid Stop Loss Limit -%', text_color='green', font=('Helvetica', 14))
                frontend_args.update({'sl_stop_pct': sl_stop_pct, 'sl_lmt_pct': sl_lmt_pct})

        # validate SL fields ar required
        if sl_choice and not inp_sl_stop_pct or sl_choice and not inp_sl_lmt_pct:
            window['TABLEDATA'].print('[ERROR] Stop Loss fields cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
        if inp_sl_stop_pct and not inp_sl_lmt_pct:
            window['TABLEDATA'].print('[ERROR] Stop Loss Stop cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)
        if inp_sl_lmt_pct and not inp_sl_stop_pct:
            window['TABLEDATA'].print('[ERROR] Stop Loss Limit cannot be empty', text_color='red', font=('Helvetica', 14))
            window['Confirm'].update(disabled=True)

        if event == 'Confirm':
            if not api_key or not api_secret or not tz_cont or not tz_city or not start_time or not working_ival or not oco_choice and not tp_choice and not sl_choice:
                window['TABLEDATA'].print('[ERROR] Some required fields are missing', text_color='red', font=('Helvetica', 14))
                window['Confirm'].update(disabled=True)
            else:
                window['Confirm'].update(disabled=False)
                window['APIKEY'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                window['APISECRET'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                window['CONTINENT'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                window['CITY'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                window['STARTTIME'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                window['WORKINGINTERVAL'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                window['ENDTIME'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                if email_choice:
                    window['SENDEREMAIL'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                    window['PASSWORD'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                    window['RECEIVEREMAIL'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                if oco_choice:
                    window['OCOTP'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                    window['OCOSL'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                    window['OCOLL'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                if tp_choice:
                    window['TPSL'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                    window['TPL'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                if sl_choice:
                    window['SL'].update(background_color='#C4BFBE', text_color='green', disabled=True)
                    window['SLL'].update(background_color='#C4BFBE', text_color='green', disabled=True)

                # call backend
                websocket_connect(frontend_args)

        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

    # Finish up by removing from the screen
    window.close()

if __name__ == '__main__':
    main()
