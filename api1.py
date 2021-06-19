# api1.py

import tornado.web
from tornado import concurrent
from tornado import escape
import json, os, time, datetime, uuid
import pandas as pd

import commonfuncs as cf
import dbconnect

root = os.path.dirname(__file__) # needed for tornado
# dataFolder = os.path.join(root,'data')

#########################
# API CALLS

# alert_id = uuid.uuid4().hex # make a new id like dc77fcf4020943a0adcf499a02fc735a

class addInput(cf.BaseHandler):
    executor = concurrent.futures.ThreadPoolExecutor(cf.maxThreads)
    @tornado.gen.coroutine
    def post(self):
        status, result = yield self.post_func()
        self.set_status(status)
        self.write(result)

    @tornado.concurrent.run_on_executor 
    def post_func(self):
        cf.logmessage("addInput POST api call")
        start = time.time()
        payload = escape.json_decode(self.request.body)

        '''
        { "message": "Multiline message",
          "category": "categ",
          "name": "name",
          "mobile": "+91xxxxx",
          "email": "email",
          "lat":345,
          "lon": 324
        }
        '''
        # security check
        if not dbconnect.sqlSecurity_payload(payload):
            return cf.makeError("CHAL HUT")
        
        message = payload.get('message')
        category = payload.get('category')
        name = payload.get('name')
        mobile = payload.get('mobile')
        email = payload.get('email')
        lat = payload.get('lat')
        lon = payload.get('lon')

        if len(message) > maxMessageLength:
            return cf.makeError("KUCH BHI KYA")

        if not cf.validateLL(lat,lon):
            return cf.makeError("KIDHAR BHI KYA")
        
        if not cf.validateEmail(email):
            return cf.makeError("INVALID EMAIL")
        
        if not cf.validateMobile(mobile):
            return cf.makeError("INVALID MOBILE")

        mid = uuid.uuid4().hex

        payload['mid'] = mid
        payload['username'] = 'anon'
        date1, timestamp = cf.getDateNTime()
        payload['date1'] = date1
        payload['created_on'] = timestamp
        payload['deleted'] = 0
        payload['approved'] = 0

        status = dbconnect.addRow(payload)
        if not status:
            return cf.makeError("Error adding to DB")

        returnD = {'message': f'Thank you for your inputs. mid: {mid}'}
        return cf.makeSuccess(returnD)    


class listInputs(cf.BaseHandler):
    executor = concurrent.futures.ThreadPoolExecutor(cf.maxThreads)
    @tornado.gen.coroutine
    def post(self):
        status, result = yield self.post_func()
        self.set_status(status)
        self.write(result)

    @tornado.concurrent.run_on_executor 
    def post_func(self):
        cf.logmessage("listInputs POST api call")
        start = time.time()
        
        # payload = escape.json_decode(self.request.body)
        """
        might want to add filter in payload later on
        """
        returnD = {}

        s1 = f"""select * from messages
        where approved = 1
        order by created_on
        """
        s2 = f"""select * from messages
        where approved != 1
        order by created_on
        """

        returnD['approved'] = dbconnect.makeQuery(s1, output='list')
        returnD['submitted'] = dbconnect.makeQuery(s2, output='list')
        end = time.time()
        returnD['timeTaken'] = round(end-start,2)

        return cf.makeSuccess(returnD)