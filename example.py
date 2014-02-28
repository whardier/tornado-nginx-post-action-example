#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys

import pprint

import pytz
import time
import datetime

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.options

from tornado.options import options
from tornado.options import define

define('debug', default=False, help='Debug', type=bool, group='Application')

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, **kwargs):
        super(BaseHandler, self).initialize(**kwargs)

        self.kwargs = kwargs

        self.start = datetime.datetime.now(pytz.UTC)

    @tornado.gen.coroutine
    def prepare(self):

        if self.request.headers.get('X-Post-Action'):
            self.set_status(202)
            self.finish()

            ## Do something coroutine specific here.. in this case we will just pprint some data

            pprint.pprint(
                {
                    'start': self.start,
                    'end': datetime.datetime.now(pytz.UTC),
                    'duration': (datetime.datetime.now(pytz.UTC) - self.start).total_seconds(),
                    'request': {
                        'protocol': self.request.protocol,
                        'uri': self.request.uri,
                        'body': self.request.body,
                        'full_url': self.request.full_url(),
                        'args': self.path_args,
                        'kwargs': self.path_kwargs,
                        'headers': dict((key,value) for key, value in self.request.headers.iteritems() if not key.startswith('X-Response')),
                    },
                    'response': {
                        'headers': dict((key.replace('X-Response-',''), value) for key, value in self.request.headers.iteritems() if key.startswith('X-Response')),
                    },
                    'kwargs': self.kwargs,
                }
            )

        if self.request.headers.get('X-Throughput-Junkie'):
            self.set_status(200)
            self.finish()


class StubHandler(BaseHandler):
    def check_xsrf_cookie(self, *args, **kwargs):
        pass

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, *args, **kwargs):
        self.write(dict(self.request.headers))
        yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 1)
        self.finish()

    def head(self, *args, **kwargs):
        self.write('')

    def post(self, *args, **kwargs):
        self.write(self.request.body)

    def patch(self, *args, **kwargs):
        self.write('')

    def delete(self, *args, **kwargs):
        self.write('')

    def options(self, *args, **kwargs):
        self.write('')


def main():

    tornado.options.parse_command_line()

    handlers = [
        tornado.web.url(r'/', StubHandler, name='index'),
    ]

    settings = dict(
        #...
        **options.as_dict()
    )

    application = tornado.web.Application(handlers=handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)

    http_server.listen(8081)

    loop = tornado.ioloop.IOLoop.instance()

    try:
        loop_status = loop.start()
    except KeyboardInterrupt:
        loop_status = loop.stop()

    return loop_status


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
