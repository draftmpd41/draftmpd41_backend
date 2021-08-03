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
APIKEY = os.environ.get('APIKEY', False)
assert APIKEY, "APIKEY not loaded!"

#########################
# API CALLS

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
            return cf.makeError("CHORI KARNE WAALEY TERA MOO KAALA")
        
        global APIKEY
        if payload.get('apikey','') != APIKEY:
            return cf.makeError("YOU HAVE BEEN REPORTED TO CRIME BRANCH")

        message = payload.get('message')
        category = payload.get('category')
        name = payload.get('name')
        mobile = payload.get('mobile')
        email = payload.get('email')
        lat = payload.get('lat')
        lon = payload.get('lon')

        if len(message) > cf.maxMessageLength:
            return cf.makeError("KUCH BHI KYA")

        if len(message) < 50:
            return cf.makeError("KUCH TOH KAHO")

        if len(category) < 4:
            return cf.makeError("ITNU SA CATEGORY?")

        if len(category) > 100:
            return cf.makeError("ABEY CATEGORY HAI YA ESSAY?")

        if not cf.validateLL(lat,lon):
            return cf.makeError("KITHEY JAARIYO BHAI? DILLI IDHAR HAI!")
        
        if not cf.validateEmail(email):
            return cf.makeError("BETA, EMAIL ADDRESS DAALO, POSTAL ADDRESS NAHIN")
        
        if not cf.validateMobile(mobile):
            return cf.makeError("MOBILE TOH THEEK SE DAALA KAR")

        mid = uuid.uuid4().hex # make a new unique id like dc77fcf4020943a0adcf499a02fc735a

        payload['mid'] = mid
        payload['username'] = 'anon'
        timestamp, date1 = cf.getDateNTime()
        payload['date1'] = date1
        payload['created_on'] = timestamp
        payload['deleted'] = 0
        payload['approved'] = 0

        status = dbconnect.addRow(payload, tablename='messages')
        if not status:
            return cf.makeError("Error adding to DB")

        returnD = {'message': f'Thank you for your inputs. mid: {mid}', 'mid':mid}
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

        s1 = f"""select mid, message, category, name, username, 
        lat, lon, date1, created_on, modified_on 
        from messages
        where approved = 1
        and deleted != 1
        order by created_on
        """
        s2 = f"""select mid, message, category, name, username, 
        lat, lon, date1, created_on, modified_on
        from messages
        where approved != 1
        and deleted != 1
        order by created_on
        """

        returnD['approved'] = dbconnect.makeQuery(s1, output='list')
        returnD['submitted'] = dbconnect.makeQuery(s2, output='list')
        end = time.time()
        returnD['timeTaken'] = round(end-start,2)
        cf.logmessage(f"listInputs done, {returnD['timeTaken']} secs")
        return cf.makeSuccess(returnD)