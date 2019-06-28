#!/usr/bin/python3
# -*- mode:python; coding:utf-8; tab-width:4 -*-

'''
Implementation of class SyncTimer
'''

import sys
import time

import Ice
import IceStorm
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import Downloader

DEFAULT_INTERVAL = 5.0

ICESTORM_MANAGER = 'Downloader.IceStorm/TopicManager'
TOPIC_NAME = 'SyncTopic'

class SyncTimer(Ice.Application):
    '''
    Publisher responsible for sending the synchronization requests
    '''
    def get_topic(self, topic_name):
        '''
        Get the synchronization topic
        '''
        broker = self.communicator()

        topic_mqr_prx = broker.stringToProxy(ICESTORM_MANAGER)
        if topic_mqr_prx is None:
            print("Cannot found {0}".format(ICESTORM_MANAGER))
            return 1

        topic_mqr = IceStorm.TopicManagerPrx.checkedCast(topic_mqr_prx)

        if not topic_mqr:
            print("Cannot cast proxy")
            return 2

        try:
            topic = topic_mqr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mqr.create(topic_name)
        finally:
            return topic

    def run(self, args):
        '''
        Sends the synchronization request
        '''
        topic = self.get_topic(TOPIC_NAME)
        publisher = Downloader.SyncEventPrx.uncheckedCast(topic.getPublisher())

        self.shutdownOnInterrupt()

        broker = self.communicator()
        properties = broker.getProperties()
        interval = properties.getProperty("SyncInterval")

        try:
            interval = float(interval)
        except Exception:
            interval = DEFAULT_INTERVAL

        while not broker.isShutdown():
            publisher.requestSync()
            time.sleep(interval)

        return 0


if __name__ == '__main__':
    app = SyncTimer()
    exit_status = app.main(sys.argv)
    sys.exit(exit_status)
