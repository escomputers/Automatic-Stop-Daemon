#!/usr/bin/env python3

from backend import *

import PySimpleGUI as sg

from datetime import datetime, timedelta
import pytz
from curses.ascii import isalpha
import re

# pattern for email validation
regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')


# VALIDATION
def is_hour(window, input):
    try:
        input = int(input)
        if input >= 1 and input <= 24:
            return input
        else:
            window['TABLEDATA'].print('[ERROR] Type a valid value between 1 and 24', text_color='red', font=('Helvetica', 14))
    except ValueError:
        window['TABLEDATA'].print('[ERROR] Type only numbers', text_color='red', font=('Helvetica', 14))


def is_valid_time(window, input):
    timeformat = '%H:%M'
    try:
        input = datetime.strptime(input, timeformat)
        window['TABLEDATA'].print('[OK] Start Time', text_color='green', font=('Helvetica', 14))
        return str(input.time())
    except ValueError:
        window['TABLEDATA'].print('[ERROR] Type a valid time format, e.g. 15:30', text_color='red', font=('Helvetica', 14))


def is_email(window, input):
    if re.fullmatch(regex, input):
        return input
    else:
        window['TABLEDATA'].print('[ERROR] Invalid email address', text_color='red', font=('Helvetica', 14))


def is_float(window, input):
    try:
        input = float(input)
        if input >= 0.05 and input <= 2999.99:
            return input
        else:
            window['TABLEDATA'].print('[ERROR] Type a valid value between 0.05 and 2999.99', text_color='red', font=('Helvetica', 14))
    except ValueError:
        window['TABLEDATA'].print('[ERROR] Type only numbers ', text_color='red', font=('Helvetica', 14))


def main():
    sg.theme('Default 1')

    left_column = [
        [sg.Text('BASD', size=(30, 1), font=('Helvetica', 18, 'bold')), sg.Push()],
        [sg.Push(), sg.Text('Required fields', font=('Helvetica', 12))],
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
        [sg.MLine(size=(80, 10), autoscroll=True, reroute_stdout=True, write_only=True, reroute_cprint=True, k='TABLEDATA')],
        # BUTTONS
        [sg.Push(), sg.Button('Confirm'), sg.Button('Quit')],
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
            else:
                window['TABLEDATA'].print('[OK] API Key', text_color='green', font=('Helvetica', 14))

        # validate API SECRET KEY
        if api_secret:
            if len(api_secret) < 64:
                window['TABLEDATA'].print('[ERROR] Check your API Secret Key, 64 characters minimum, no spaces', text_color='red', font=('Helvetica', 14))
            else:
                window['TABLEDATA'].print('[OK] API Secret Key', text_color='green', font=('Helvetica', 14))

        # validate API KEYS
        if api_key and api_secret and len(api_key) >= 64 and len(api_secret) >= 64:
            if api_key == api_secret:
                window['TABLEDATA'].print('[ERROR] API Key and API Secret Key cannot be the same', text_color='red', font=('Helvetica', 14))
            else:
                window['TABLEDATA'].print('[OK] API Key and API Secret Key', text_color='green', font=('Helvetica', 14))
                window['APIKEY'].update('', background_color='#C4BFBE', text_color='green')
                window['APISECRET'].update('', background_color='#C4BFBE', text_color='green')

        # validate TIMEZONE CONTINENT
        if tz_cont:
            if tz_cont.isalpha():
                window['TABLEDATA'].print('[OK] Timezone Continent format', text_color='green', font=('Helvetica', 14))
            else:
                window['TABLEDATA'].print('[ERROR] Type only letters', text_color='red', font=('Helvetica', 14))

        # validate TIMEZONE CITY
        if tz_city:
            if tz_city.isalpha():
                window['TABLEDATA'].print('[OK] Timezone City format', text_color='green', font=('Helvetica', 14))
            else:
                window['TABLEDATA'].print('[ERROR] Type only letters', text_color='red', font=('Helvetica', 14))

        # validate TIMEZONE
        if tz_cont.isalpha() and tz_city.isalpha():
            usr_tz = tz_cont.capitalize() + '/' + tz_city.capitalize()
            if usr_tz in pytz.all_timezones:
                window['TABLEDATA'].print('[OK] Timezone', text_color='green', font=('Helvetica', 14))
                window['CONTINENT'].update(tz_cont.capitalize(), background_color='#C4BFBE', text_color='green')
                window['CITY'].update(tz_city.capitalize(), background_color='#C4BFBE', text_color='green')
            else:
                window['TABLEDATA'].print(
                        '[ERROR] Timezone: ' + tz_cont.capitalize() + '/' + tz_city.capitalize() +
                        ' you entered is not valid. \n ', text_color='red', font=('Helvetica', 14)
                    )

        # validate START TIME
        if inp_start_time:
            if is_valid_time(window, inp_start_time):
                start_time = is_valid_time(window, inp_start_time)
                user_start_time = datetime.strptime(start_time, '%H:%M:%S')
                user_start_time_def = str(user_start_time.time())[:-3]  # remove seconds from string

        # validate WORKING INTERVAL
        if inp_working_ival:
            if is_hour(window, inp_working_ival):
                working_ival = is_hour(window, inp_working_ival)
                window['WORKINGINTERVAL'].update(working_ival, background_color='#C4BFBE', text_color='green')

        # construct USER END TIME
        try:
            if user_start_time and working_ival:
                end_time = (user_start_time + timedelta(hours=working_ival)).time()
                user_end_time = str(end_time)[:-3]  # remove seconds from string
                user_end_time_def = datetime.strptime(user_end_time, '%H:%M')
                window['ENDTIME'].update(user_end_time, background_color='#C4BFBE', text_color='green')
        except UnboundLocalError:
            continue

        # show order inputs according to radio buttons
        if tp_choice:
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

        # validate SENDER EMAIL
        if sender_email:
            if is_email(window, sender_email):
                valid_sender_email = is_email(window, sender_email)
                if '@gmail.com' in valid_sender_email:
                    window['TABLEDATA'].print('[OK] Valid sender email address', text_color='green', font=('Helvetica', 14))
                    window['SENDEREMAIL'].update(valid_sender_email, background_color='#C4BFBE', text_color='green')
                else:
                    window['TABLEDATA'].print('[ERROR] Only Gmail account currently supported', text_color='red', font=('Helvetica', 14))

        # validate RECEIVER EMAIL
        if receiver_email:
            if is_email(window, receiver_email):
                valid_receiver_email = is_email(window, receiver_email)
                window['TABLEDATA'].print('[OK] Valid receiver email address', text_color='green', font=('Helvetica', 14))

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
        # TP
        if inp_tp_stop_pct:
            if is_float(window, inp_tp_stop_pct):
                tp_stop_pct = is_float(window, inp_tp_stop_pct)
                window['TABLEDATA'].print('[OK] Valid Take Profit Stop +%', text_color='green', font=('Helvetica', 14))
        if inp_tp_lmt_pct:
            if is_float(window, inp_tp_lmt_pct):
                tp_lmt_pct = is_float(window, inp_tp_lmt_pct)
                window['TABLEDATA'].print('[OK] Valid Take Profit Stop Limit +%', text_color='green', font=('Helvetica', 14))
        # SL
        if inp_sl_stop_pct:
            if is_float(window, inp_sl_stop_pct):
                sl_stop_pct = is_float(window, inp_sl_stop_pct)
                window['TABLEDATA'].print('[OK] Valid Stop Loss Stop -%', text_color='green', font=('Helvetica', 14))
        if inp_sl_lmt_pct:
            if is_float(window, inp_sl_lmt_pct):
                sl_lmt_pct = is_float(window, inp_sl_lmt_pct)
                window['TABLEDATA'].print('[OK] Valid Stop Loss Limit -%', text_color='green', font=('Helvetica', 14))

        if event == 'Confirm':
            check_time(usr_tz, user_start_time_def, user_end_time_def)

        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

    # Finish up by removing from the screen
    window.close()

if __name__ == '__main__':
    main()
