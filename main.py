#!/usr/bin/env python3

from module.order import websocket_connect

import webbrowser
import PySimpleGUI as sg

from datetime import datetime, timedelta
import pytz
from curses.ascii import isalpha
import re

# pattern for email validation
regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

# initialize DATA dictionary
usrdata = {}

# set default fonts
font12 = ('Segoe UI', 12)
font14 = ('Segoe UI', 14)
font_ul = ("Segoe UI", 16, "underline")


# VALIDATION
def is_email(window, input):
    if re.fullmatch(regex, input):
        return input
    else:
        window['OUT'].print('[ERROR] Invalid email address', text_color='red', font=font14)


def is_float(window, input):
    try:
        input = float(input)
        if input >= 0.05 and input <= 2999.99:
            return input
        else:
            window['OUT'].print('[ERROR] Type a valid value between 0.05 and 2999.99', text_color='red', font=font14)
    except ValueError:
        window['OUT'].print('[ERROR] Type only numbers, e.g. 2.55', text_color='red', font=font14)


def main():

    links = {
        "GitHub": "https://github.com/escomputers/BASD",
    }

    sg.theme('Default 1')

    left_column = [
        [sg.Text('BASD', font=('Segoe UI', 18, 'bold'), expand_x=True), sg.Push()],
        [sg.Text('API Key', font=font12), sg.Push(), sg.Input(k='APIKEY', enable_events=True, font=font12, tooltip='your Binance.com API KEY', password_char='*')],
        [sg.Text('API Secret', font=font12), sg.Push(), sg.Input(k='APISECRET', enable_events=True, font=font12, tooltip='your Binance.com API SECRET KEY', password_char='*')],
        [sg.Text('Timezone Continent', font=font12), sg.Push(), sg.Input(k='CONTINENT', enable_events=True, font=font12, tooltip='e.g. Europe')],
        [sg.Text('Timezone City', font=font12), sg.Push(), sg.Input(k='CITY', enable_events=True, font=font12, tooltip='e.g. Rome')],
        [sg.Text('Start Time', font=font12), sg.Push(), sg.Input(k='STARTTIME', enable_events=True, font=font12, tooltip='e.g. 23:45')],
        [sg.Text('Active Hours', font=font12), sg.Push(), sg.Input(k='WORKINGINTERVAL', enable_events=True, font=font12, tooltip='How many working HOURS you want. 24 equals to all day, e.g. 8')],
        [sg.Text('End Time', font=font12), sg.Push(), sg.Input(k='ENDTIME', disabled=True, enable_events=True, font=font12)],
        [sg.Checkbox('Email Alert', font=font12, default=False, k='EMAILCHOICE', enable_events=True)],
        [sg.Text('Gmail Sender Address', font=font12, k='SENDEREMAILTXT'), sg.Push(), sg.Input(k='SENDEREMAIL', enable_events=True, font=font12, tooltip='sender email address (GMAIL only)')],
        [sg.Text('Gmail App Password', font=font12, k='PASSWORDTXT'), sg.Push(), sg.Input(k='PASSWORD', enable_events=True, font=font12, tooltip='gmail app password', password_char='*')],
        [sg.Text('Receiver Address', font=font12, k='RECEIVEREMAILTXT'), sg.Push(), sg.Input(k='RECEIVEREMAIL', enable_events=True, font=font12, tooltip='receiver email address')],
    ]

    right_column = [
        [sg.Radio('Take Profit', group_id=1, font=font12, enable_events=True, k='TPCHOICE'), sg.Radio('Stop Loss', group_id=1, font=font12, enable_events=True, k='SLCHOICE'), sg.Radio('OCO', group_id=1, font=font12, enable_events=True, k='OCOCHOICE')],
        # OCO
        [sg.Text('Take Profit +%', font=font12, k='OCOTPTXT'), sg.Push(), sg.Input(k='OCOTP', enable_events=True, font=font12, tooltip='OCO Take Profit percentage, e.g. 5.20')],
        [sg.Text('Stop Loss -%', font=font12, k='OCOSLTXT'), sg.Push(), sg.Input(k='OCOSL', enable_events=True, font=font12, tooltip='should be LOWER than market price WHEN order will be placed, e.g. 1.20')],
        [sg.Text('Limit Loss -%', font=font12, k='OCOLLTXT'), sg.Push(), sg.Input(k='OCOLL', enable_events=True, font=font12, tooltip='should be HIGHER than market price WHEN order will be placed, e.g. 1.05')],
        # TAKE PROFIT
        [sg.Text('Stop Profit +%', font=font12, k='TPSLTXT'), sg.Push(), sg.Input(k='TPSL', enable_events=True, font=font12, tooltip='Take Profit Stop percentage, e.g. 5.25')],
        [sg.Text('Limit Profit +%', font=font12, k='TPLTXT'), sg.Push(), sg.Input(k='TPL', enable_events=True, font=font12, tooltip='Take Profit Limit percentage, e.g. 5.20')],
        # STOP LOSS
        [sg.Text('Stop Loss -%', font=font12, k='SLTXT'), sg.Push(), sg.Input(k='SL', enable_events=True, font=font12, tooltip='Stop Loss Stop percentage, e.g. 1.10')],
        [sg.Text('Limit Loss -``%', font=font12, k='SLLTXT'), sg.Push(), sg.Input(k='SLL', enable_events=True, font=font12, tooltip='Stop Loss Limit percentage, e.g. 1.15')],
        # OUTPUT
        [sg.MLine(size=(80, 10), autoscroll=True, reroute_stdout=True, write_only=True, reroute_cprint=True, k='OUT')],
        # BUTTON
        [sg.Push(), sg.Button('Validate', font=font12)],
        # CREDITS
        [sg.Push()] + [
            sg.Text('Star/Fork me on GitHub!', font=('Segoe UI', 9, 'italic'), expand_x=True, enable_events=True, key=key) for i, key in enumerate(links)]
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
    window = sg.Window('Binance Algorithmic Stop Daemon [INPUT]', icon='templates/icon.ico').Layout(layout)

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read(timeout=1000)

        # EMAIL SECTION hidden by default
        window['SENDEREMAILTXT'].update(visible=False)
        window['SENDEREMAIL'].update(visible=False)
        window['PASSWORDTXT'].update(visible=False)
        window['PASSWORD'].update(visible=False)
        window['RECEIVEREMAILTXT'].update(visible=False)
        window['RECEIVEREMAIL'].update(visible=False)
        # ORDER SECTION hidden by default
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

        # GLOBAL VARIABLES
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

        # show order fields according to radio buttons
        if tp_choice:
            usrdata.update({'tp_choice': tp_choice})
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
            usrdata.update({'sl_choice': sl_choice})
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
            usrdata.update({'oco_choice': oco_choice})
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

        # if email checked, show fields
        if email_choice:
            window['SENDEREMAILTXT'].update(visible=True)
            window['SENDEREMAIL'].update(visible=True)
            window['PASSWORDTXT'].update(visible=True)
            window['PASSWORD'].update(visible=True)
            window['RECEIVEREMAILTXT'].update(visible=True)
            window['RECEIVEREMAIL'].update(visible=True)

        if event == 'Validate':
            if api_key and api_secret and tz_cont and tz_city and inp_start_time and inp_working_ival and oco_choice or tp_choice or sl_choice:
                # API KEY
                if len(api_key) < 64 or ' ' in api_key:
                    window['OUT'].print('[ERROR- API KEY] at least 64 characters, no spaces', text_color='red', font=font14)
                else:
                    window['OUT'].print('[OK- API KEY]', text_color='green', font=font14)
                # API SECRET
                if len(api_secret) < 64 or ' ' in api_secret:
                    window['OUT'].print('[ERROR- API SECRET] at least 64 characters, no spaces', text_color='red', font=font14)
                else:
                    window['OUT'].print('[OK- API SECRET]', text_color='green', font=font14)

                # API KEYS
                if len(api_key) >= 64 and len(api_secret) >= 64:
                    if api_key == api_secret:
                        window['OUT'].print('[ERROR- API KEY and API SECRET] cannot be the same', text_color='red', font=font14)
                    else:
                        window['OUT'].print('[OK- API KEY and API SECRET]', text_color='green', font=font14)
                        usrdata.update({'api_key': api_key, 'api_secret': api_secret})

                # TIMEZONE
                if tz_cont.isalpha() and tz_city.isalpha():
                    usr_tz = tz_cont.capitalize() + '/' + tz_city.capitalize()
                    if usr_tz in pytz.all_timezones:
                        usrdata.update({'usr_tz': usr_tz})
                        window['OUT'].print('[OK- TIMEZONE valid]', text_color='green', font=font14)
                        window['CONTINENT'].update(tz_cont.capitalize())
                        window['CITY'].update(tz_city.capitalize())
                    else:
                        window['OUT'].print(
                                '[ERROR- TIMEZONE] ' + tz_cont.capitalize() + '/' + tz_city.capitalize() +
                                ' does not exist. \n ', text_color='red', font=font14
                            )
                else:
                    window['OUT'].print('[ERROR- TZ CONTINENT and/or TZ CITY] type only letters, no spaces', text_color='red', font=font14)

                # START TIME
                try:
                    inp_start_time = datetime.strptime(inp_start_time, '%H:%M')
                    start_time = inp_start_time.time()
                    user_start_time = datetime.strptime(str(start_time)[:-3], '%H:%M')  # used for end_time calc
                    usrdata.update({'user_start_time_def': start_time})
                    window['OUT'].print('[OK- START TIME]', text_color='green', font=font14)
                except ValueError:
                    window['OUT'].print('[ERROR- START TIME] no spaces, e.g. 15:30', text_color='red', font=font14)

                # WORKING INTERVAL
                try:
                    working_ival = int(inp_working_ival)
                    if working_ival >= 1 and working_ival <= 24:
                        usrdata.update({'working_ival': working_ival})
                    else:
                        window['OUT'].print('[ERROR- ACTIVE HOURS] Type a valid value between 1 and 24', text_color='red', font=font14)
                except ValueError:
                    window['OUT'].print('[ERROR- ACTIVE HOURS] Type only numbers', text_color='red', font=font14)

                # END TIME
                try:
                    if user_start_time and working_ival:
                        end_time = (user_start_time + timedelta(hours=working_ival)).time()
                        user_end_time = str(end_time)[:-3]  # remove seconds from string used only for displaying
                        window['ENDTIME'].update(user_end_time)
                except UnboundLocalError:
                    continue

                if email_choice:
                    # SENDER EMAIL
                    if is_email(window, sender_email):
                        valid_sender_email = is_email(window, sender_email)
                        if '@gmail.com' in valid_sender_email:
                            window['OUT'].print('[OK- GMAIL SENDER ADDRESS]', text_color='green', font=font14)
                            usrdata.update({'valid_sender_email': valid_sender_email})
                        else:
                            window['OUT'].print('[ERROR- GMAIL SENDER ADDRESS] Only Gmail accounts currently supported', text_color='red', font=font14)
                    # RECEIVER EMAIL
                    if is_email(window, receiver_email):
                        valid_receiver_email = is_email(window, receiver_email)
                        window['OUT'].print('[OK- RECEIVER ADDRESS]', text_color='green', font=font14)
                        usrdata.update({'valid_receiver_email': valid_receiver_email})
                    # PASSWORD
                    if len(password) >= 8 and ' ' not in password:
                        valid_password = password
                        usrdata.update({'password': valid_password})
                        window['OUT'].print('[OK- PASSWORD]', text_color='green', font=font14)
                    else:
                        window['OUT'].print('[ERROR- PASSWORD] at least 8 characters, no spaces', text_color='red', font=font14)

                # OCO FIELDS
                if oco_choice:
                    if is_float(window, inp_oco_profit_pct) and is_float(window, inp_oco_sl_pct) and is_float(window, inp_oco_lmt_pct):
                        oco_profit_pct = round((is_float(window, inp_oco_profit_pct)), 2)
                        oco_sl_pct = round((is_float(window, inp_oco_sl_pct)), 2)
                        oco_lmt_pct = round((is_float(window, inp_oco_lmt_pct)), 2)
                        window['OUT'].print('[OK- OCO TAKE PROFIT]', text_color='green', font=font14)
                        window['OUT'].print('[OK- OCO STOP LOSS]', text_color='green', font=font14)
                        window['OUT'].print('[OK- OCO STOP LOSS LIMIT]', text_color='green', font=font14)

                        # CLEAN UP DICTIONARY ARGS
                        try:
                            garbage = ['sl_choice', 'tp_choice', 'tp_stop_pct', 'tp_lmt_pct', 'sl_stop_pct', 'sl_lmt_pct']
                            if any(x in usrdata for x in garbage):
                                [usrdata.pop(key) for key in garbage]
                        except KeyError:
                            pass

                        # START WORKING
                        try:
                            if email_choice and valid_sender_email and valid_receiver_email and valid_password or not email_choice:
                                usrdata.update({'oco_choice': True, 'oco_profit_pct': oco_profit_pct, 'oco_sl_pct': oco_sl_pct, 'oco_lmt_pct': oco_lmt_pct})
                                websocket_connect(usrdata)
                            elif email_choice and not valid_sender_email or not valid_receiver_email or not valid_password:
                                window['OUT'].print('[ERROR- EMAIL] fill all required fields', text_color='red', font=font14)
                        except UnboundLocalError:
                            pass

                # TP FIELDS
                if tp_choice:
                    if is_float(window, inp_tp_stop_pct) and is_float(window, inp_tp_lmt_pct):
                        tp_stop_pct = round((is_float(window, inp_tp_stop_pct)), 2)
                        tp_lmt_pct = round((is_float(window, inp_tp_lmt_pct)), 2)
                        window['OUT'].print('[OK- TAKE PROFIT STOP]', text_color='green', font=font14)
                        window['OUT'].print('[OK- TAKE PROFIT LIMIT]', text_color='green', font=font14)

                        # CLEAN UP DICTIONARY ARGS
                        try:
                            garbage = ['sl_choice', 'oco_choice', 'oco_profit_pct', 'oco_sl_pct', 'oco_lmt_pct', 'sl_stop_pct', 'sl_lmt_pct']
                            if any(x in usrdata for x in garbage):
                                [usrdata.pop(key) for key in garbage]
                        except KeyError:
                            pass

                        # START WORKING
                        try:
                            if email_choice and valid_sender_email and valid_receiver_email and valid_password or not email_choice:
                                usrdata.update({'tp_choice': True, 'tp_stop_pct': tp_stop_pct, 'tp_lmt_pct': tp_lmt_pct})
                                websocket_connect(usrdata)
                            elif email_choice and not valid_sender_email or not valid_receiver_email or not valid_password:
                                window['OUT'].print('[ERROR- EMAIL] fill all required fields', text_color='red', font=font14)
                        except UnboundLocalError:
                            pass

                # SL FIELDS
                if sl_choice:
                    if is_float(window, inp_sl_stop_pct) and is_float(window, inp_sl_lmt_pct):
                        sl_stop_pct = round((is_float(window, inp_sl_stop_pct)), 2)
                        sl_lmt_pct = round((is_float(window, inp_sl_lmt_pct)), 2)
                        window['OUT'].print('[OK- STOP LOSS STOP]', text_color='green', font=font14)
                        window['OUT'].print('[OK- STOP LOSS LIMIT]', text_color='green', font=font14)

                        # CLEAN UP DICTIONARY ARGS
                        try:
                            garbage = ['tp_choice', 'oco_choice', 'oco_profit_pct', 'oco_sl_pct', 'oco_lmt_pct', 'tp_stop_pct', 'tp_lmt_pct']
                            if any(x in usrdata for x in garbage):
                                [usrdata.pop(key) for key in garbage]
                        except KeyError:
                            pass

                        # START WORKING
                        try:
                            if email_choice and valid_sender_email and valid_receiver_email and valid_password or not email_choice:
                                usrdata.update({'sl_choice': True, 'sl_stop_pct': sl_stop_pct, 'sl_lmt_pct': sl_lmt_pct})
                                websocket_connect(usrdata)
                            elif email_choice and not valid_sender_email or not valid_receiver_email or not valid_password:
                                window['OUT'].print('[ERROR- EMAIL] fill all required fields', text_color='red', font=font14)
                        except UnboundLocalError:
                            pass
            else:
                window['OUT'].print('[ERROR- GENERAL] fill all required fields', text_color='red', font=font14)

        for key in links:
            window[key].bind('<Enter>', '<Enter>')
            window[key].bind('<Leave>', '<Leave>')
            window[key].set_cursor('hand2')

        # if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break
        elif event.endswith('<Enter>'):
            element = window[event.split('<')[0]]
            element.update(font=font_ul)
        elif event.endswith('<Leave>'):
            element = window[event.split('<')[0]]
            element.update(font=font12)
        # if link has been clicked open URL
        if event in links:
            webbrowser.open(links[event])

    # Finish up by removing from the screen
    window.close()


if __name__ == '__main__':
    main()
