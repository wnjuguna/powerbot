#!/usr/bin/env python

from powerbot import PowerAlert
from urllib import urlencode
from telepot import glance
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import InvalidURLError, DownloadError
from users import User
import json
import yaml

class MessageHandler(object):
    def __init__(self):
        self._errmsg = 'Sorry. I do not understand your request.'
        self._successmsg = '*Great!* Thanks for registering'
        self._emptynoticemsg = 'There are *no* scheduled outages today'
        self._registeredmsg = 'You are already registered.'
        self._deregistermsg = 'We are sad to see you go'
        self.params = {'chat_id': None, 'text': None, 'parse_mode': 'markdown'}
        try:
            f = open('config.yaml', 'r').read()
        except IOError, e:
            raise(e)
        else:
            config = yaml.load(f)
            self.api = 'https://api.telegram.org/bot%s/' %(config['api_key'])
            return

    def _sendReply(self):
        params = urlencode(self.params)
        try:
            urlfetch.Fetch(self.api+'sendMessage', payload=params, method='POST')
        except (InvalidURLError, DownloadError), e:
            raise(e)
        return
    
    def _getKeyboard(self, msg):
        sub = User()
        kb = {'keyboard':[['Check'], ['Unsubscribe']],
              'resize_keyboard': True}
        self.params['text'] = self._registeredmsg
        if not sub.isRegistered(msg):
            sub.registerUser(msg)
            self.params['text'] = self._successmsg
        if sub.isAdmin(msg):
            kb = {'keyboard': [['Check'], ['Update']],
                  'resize_keyboard': True}
        return json.dumps(kb)

    def notifySubs(self):
        notices = PowerAlert().notices
        subs = User().subs
        for sub in subs:
            self.params['chat_id'] = sub.chat_id
            self.params['text'] = notices
            self._sendReply()
        return

    def routeMessage(self, msg):
        content_type, chat_type, chat_id = glance(msg)
        self.params['chat_id'] = chat_id
        self.params['reply_markup'] = self._getKeyboard(msg)
        if content_type == 'text':
            command = msg['text'].strip().lower()
            if command == '/start':
                pass
            elif command == 'unsubscribe':
                result = User().deregisterUser(msg)
                if result:
                    self.params['text'] = self._deregistermsg
            elif command == 'update':
                notice = PowerAlert().crawlPage()
                self.params['text'] = 'updated'
            elif command == 'check':
                reply = PowerAlert().notices
                self.params['text'] = reply
                if reply:
                    self.params['text'] = reply
                else:
                    self.params['text'] = self._emptynotice
            else:
                self.params['text'] = self._errmsg
        else:
                self.params['text'] = self._errmsg
        self._sendReply()
        return
