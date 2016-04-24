#!/usr/bin/env python

"""
Handle user registration
"""

from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import Error
import logging
import telepot
import yaml

class Subscriber(ndb.Model):
    createdAt = ndb.DateTimeProperty(auto_now=True)
    username = ndb.StringProperty()
    name = ndb.StringProperty()
    chat_id = ndb.IntegerProperty(required=True)
    roles = ndb.StringProperty(repeated=True)

class User(object):
    def __init__(self):
        try:
            f = open('config.yaml', 'r').read()
        except IOError, e:
            loggging.error("Unable to read config file: %s" %(e))
            raise(e)
        else:
            config = yaml.load(f)
            self.admins = config['admin']
            return
    
    def isRegistered(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        try:
            query = Subscriber.query(Subscriber.chat_id == chat_id)
        except Error, e:
            logging.error("Unable to query DB: %s" %(e))
        else:
            user = next(query.iter(), None)
            if user:
                return True
        return

    def registerUser(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        name = msg['chat']['first_name']
        try:
            username = msg['chat']['username']
        except KeyError, e:
            logging.info("Cannot fetch username: %s" %(e))
            username = None
        role = ['subscriber']
        if username in self.admins:
            role.append('admin')
        try:
            Subscriber.get_or_insert(str(chat_id),
                    chat_id = chat_id,
                    name = name,
                    username = username,
                    roles = role)
        except Error, e:
            logging.error("Unable to register user: %s" %(e))
        else:
            return True
        return

    def isAdmin(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        try:
            query = Subscriber.query(Subscriber.chat_id == chat_id,
                    Subscriber.roles.IN(['admin']))
        except Error, e:
            logging.error("Unable to query DB: %s" %(e))
        else:
            user = next(query.iter(), None)
            if user:
                return True
        return

    @property
    def subs(self):
        try:
            subs = Subscriber.query().fetch()
        except Error, e:
            logging.error("Unable to query DB: %s" %(e))
        else:
            return subs

    def deregisterUser(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        sub_key = ndb.Key('Subscriber', str(chat_id))
        try:
            sub_key.delete()
        except Error, e:
            logging.error("Unable to delete sub: %s" %(e))
        else:
            return True
