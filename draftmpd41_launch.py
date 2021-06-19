portnum = 5610

print("Loading dependencies")
import tornado.ioloop
import tornado.web
from tornado import concurrent
from tornado import escape
import json, os, time, datetime
import pandas as pd
import uuid

import commonfuncs as cf
import dbconnect
import api1

cf.logmessage("All dependences loaded.")

root = os.path.dirname(__file__) # needed for tornado


# from https://stackoverflow.com/a/55762431/4355695 : restrict direct browser access to .py files and stuff
class MyStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache") # https://stackoverflow.com/a/12031093/4355695

    def validate_absolute_path(self, root, absolute_path):
        page = os.path.basename(absolute_path)
        # do blocking as necessary
        # print(absolute_path, page)

        if 'config' in absolute_path:
            cf.logmessage('caught snooping!')
            return os.path.join(root,'redirect.html')
        return super().validate_absolute_path(root, absolute_path) # you may pass


class Application(tornado.web.Application):
    _routes = [
        # tornado.web.url(r"/API/fetchBreezoMap", api1.fetchBreezoMap),
        tornado.web.url(r"/API/addInput", api1.addInput),
        tornado.web.url(r"/(.*)", MyStaticFileHandler, {"path": root, "default_filename": "redirect.html"})
    ]
    def __init__(self):
        settings = {
            "debug": True, # make this false when pushing to openshift
            "cookie_secret": "EYeRT%&)WERterGEfYTjR",
            "compress_response": True # https://stackoverflow.com/a/11872086/4355695    
        }
        super(Application, self).__init__(self._routes, **settings)

if __name__ == "__main__":
    app = Application()
    app.listen(port=portnum)
    print(f"Launched on port {portnum}")
    tornado.ioloop.IOLoop.current().start()
