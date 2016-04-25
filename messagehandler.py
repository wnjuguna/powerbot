#!/usr/bin/env python

from powerbot import PowerAlert
from urllib import urlencode
from telepot import glance
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import InvalidURLError, DownloadError
from google.appengine.ext import deferred
from users import User
import json
import yaml

class MessageHandler(object):
    def __init__(self):
        self._errmsg = 'Sorry. I do not understand your request.'
        self._successmsg = "*Great!* Thanks for registering \xf0\x9f\x98\x84. We'll send you alerts for scheduled power outages at 18:00"
        self._emptynoticemsg = 'There are *no* scheduled outages today'
        self._registeredmsg = 'You are already registered.'
        self._deregistermsg = '\xf0\x9f\x98\x9e We are sad to see you go. You will no longer receive alerts.'
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
        if sub.isRegistered(msg):
            kb = {'keyboard':[['Check'], ['Unsubscribe']],
                  'resize_keyboard': True}
        else:
            kb = {'keyboard':[['Check'],['Subscribe']],
                  'resize_keyboard': True}

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
            deferred.defer(self._sendReply)
        return

    def routeMessage(self, msg):
        content_type, chat_type, chat_id = glance(msg)
        self.params['chat_id'] = chat_id
        self.params['reply_markup'] = self._getKeyboard(msg)
        if content_type == 'text':
            command = msg['text'].strip().lower()
            if command == '/start' or command == 'subscribe':
                User().registerUser(msg)
                self.params['text'] = self._successmsg
                self.params['reply_markup'] = self._getKeyboard(msg)
            elif command == 'unsubscribe':
                result = User().deregisterUser(msg)
                if result:
                    self.params['text'] = self._deregistermsg
                    self.params['reply_markup'] = self._getKeyboard(msg)
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
