# https://twitchapps.com/tmi/
# create an app, User version
# create switcherino.ini

import configparser
import time
import requests
import re

import irc.bot

import pynput.keyboard as kb
import pynput.mouse as ms


class PhoneController:

    def _clear_capture(self):
        self.coords.clear()
        self.captured = False

    def _on_press(self, key):
        if self.captured:
            print('Capture already done, clear to recapture')
            return False

        if key == kb.Key.left:
            # print('Quit capturing phone coords!')
            # print('Request capture from Twitch chat')
            # self._clear_capture()
            # return False
            print('Restarting capture...')
            self._clear_capture()
            return True

        if key == kb.Key.right:
            if len(self.coords) == 0:
                print('Captured [Make a call] coord [1 / 2]')
                print('Next capture [Address Bar]...')
                self.coords.append(self.mouseController.position)
                return True
            print('Captured [Address Bar] coord [2 / 2]')
            print('Capture finished!')
            self.coords.append(self.mouseController.position)
            self.captured = True
            return False

    def capture_coords(self):
        print('Capturing (-> to capture, <- to restart)...')
        print('First capture [Make a call]...')
        with kb.Listener(on_press=self._on_press) as listener:
            listener.join()

        print('Processing capture...')
        time.sleep(2)
        self.setup_clicks()

        return self.captured

    def execute_call(self, phonenum):
        if not self.captured:
            print('Must capture before call')
            return False

        # self.mouseController.move(x1, y1)
        # self.mouseController.click(ms.Button.left)

        self.keyboardController.type(phonenum)
        # self.keyboardController.press(kb.Key.enter)
        x1, y1 = self.coords[1]
        self.mouseController.position = (x1, y1 + 30)
        time.sleep(.5)
        self.mouseController.click(ms.Button.left)
        return True

    def setup_clicks(self):
        if not self.captured:
            return False
        print('Clicking to ensure phone is up and address bar active...')
        self.mouseController.position = self.coords[0]
        self.mouseController.click(ms.Button.left)
        time.sleep(1)
        self.mouseController.position = self.coords[1]
        self.mouseController.click(ms.Button.left)
        return True

    def click_address_bar(self):
        if not self.captured:
            return False

        self.mouseController.position = self.coords[1]
        self.mouseController.click(ms.Button.left)

    def __init__(self):

        self.mouseController = ms.Controller()
        self.keyboardController = kb.Controller()

        self.coords = []
        self.captured = False


class TwitchBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel, phone_controller, command_username, listen_usernames):
        self.phone_controller = phone_controller
        self.command_username = command_username
        self.listen_usernames = set(listen_usernames)

        self.fired = False

        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel

        # Get the channel id, we will need this for v5 API calls
        url = 'https://api.twitch.tv/kraken/users?login=' + channel
        headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['users'][0]['_id']

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        print('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:' + token)], username, username)

    def on_welcome(self, c, e):
        print('Joining ' + self.channel)

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        print('Joined!')

    def on_pubmsg(self, c, e):
        source_user = e.source.split('!')[0]
        print(source_user)  # TODO remove this

        if source_user in self.listen_usernames:
            msg = e.arguments[0]
            call_success = self.try_parse_and_call(msg)
            if call_success:
                return

            if source_user == self.command_username:
                if msg[:1] == '1':
                    tokens = msg.split(' ')
                    cmd = tokens[0][1:]
                    print('Received command: ' + cmd)
                    self.do_command(e, cmd, tokens[1:])
                else:
                    print('Check phone requested (non-command received)...')
                    self.phone_controller.click_address_bar()
            else:
                print("[" + source_user + "]: " + msg)
        return

    def try_parse_and_call(self, msg):
        for match in re.finditer(r"\(?\b[2-9][0-9]{2}\)?[-. ]*[1-9][0-9]{2}[-. ]*[0-9]{4}\b", msg):
            if self.fired:
                print('Already fired, [1reload] to call again')
                return False

            call_success = self.phone_controller.execute_call(match.group(0))
            if call_success:
                print('OK: Call fired, [1reload] to call again')
                self.fired = True

            return call_success

        return False

    def do_command(self, e, cmd, cmd_args):
        c = self.connection

        # Poll the API to get current game.
        if cmd == "status":
            print('STATUS')
            call_state_desc = "FIRED ([1reload] to fire again)" if self.fired else "READY"
            print('Call state: ' + call_state_desc)
            print('Listen usernames:')
            for listen_username in sorted(self.listen_usernames):
                print(listen_username)

        elif cmd == "reload" or cmd == "r":
            self.fired = False
            print('Ready to call again')

        elif cmd == "add":
            if len(cmd_args) > 0:
                username_to_add = cmd_args[0].lower()
                self.listen_usernames.add(username_to_add)
                print('Added ' + username_to_add)
            else:
                print('No username provided')

        elif cmd == "remove":
            if len(cmd_args) > 0:
                username_to_remove = cmd_args[0].lower()
                self.listen_usernames.remove(username_to_remove)
                print('Removed ' + username_to_remove)
            else:
                print('No username provided')

        elif cmd == "setup" or cmd == "s":
            self.phone_controller.setup_clicks()

        elif cmd == "capture":
            self.phone_controller.capture_coords()

        elif cmd == "?" or cmd == "help" or cmd == "h":
            print("[1status]: display FIRED and listen usernames")
            print("[1reload]: enable next call")
            print("[1add][remove]: edit listen usernames")
            print("[1setup]: click phone buttons")
            print("[1capture]: set phone button locations")

        # The command was not recognized
        else:
            print('Did not understand command: ' + cmd)

        print('')


def main():
    config = configparser.ConfigParser()
    config.read('switcherino.ini')

    phone_controller = PhoneController()
    phone_controller.capture_coords()

    bot = TwitchBot(config['Login']['ClientUsername']
                    , config['Login']['ClientId']
                    , config['Login']['ClientToken']
                    , config['DEFAULT']['Channel']
                    , phone_controller
                    , config['DEFAULT']['CommandUsername'].lower()
                    , [lu.lower() for lu in config['DEFAULT']['ListenUsernames'].split(',')])
    bot.start()


if __name__ == '__main__':
    main()
