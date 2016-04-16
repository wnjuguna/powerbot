#!/usr/bin/env python

from bottle import Bottle, request, error
from messagehandler import MessageHandler
from powerbot import PowerAlert

app = Bottle()

@error(404)
def error404(error):
    return "Nothing here. Move along."

@app.route('/powerbot/<action>', method='GET')
def runCmd(action):
    if action == 'notify':
        worker = MessageHandler()
        worker.notifySubs()
    elif action == 'update':
        PowerAlert().crawlPage()
    return 'OK'

@app.route('/powerbot', method='POST')
def handleRequest():
    msg = request.json['message']
    worker = MessageHandler()
    worker.routeMessage(msg)
    return 'OK'
