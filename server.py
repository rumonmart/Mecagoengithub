#!/usr/bin/python3
# -*- mode:python; coding:utf-8; tab-width:4 -*

'''
Implementation of classes SchedulerFactory and Server
'''

import sys

import Ice
import IceStorm
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import Downloader

from work_queue import WorkQueue
from downloadScheduler import DownloadSchedulerI

ICESTORM_MANAGER = 'Downloader.IceStorm/TopicManager'
SYNC_TOPIC = 'SyncTopic'
STATUS_TOPIC = 'ProgressTopic'

class SchedulerFactoryI(Downloader.SchedulerFactory):
    '''
    Factory of schedulers
    '''

    registry = {}
    sync_publisher = None

    def __init__(self, tasks, sync_publisher=None):
        self.tasks = tasks
        self.sync_publisher = sync_publisher

    def make(self, name, current=None):
        '''
        Create a new scheduler or server
        '''
        servant = DownloadSchedulerI(self.tasks, self.sync_publisher)
        if name in self.registry:
            raise Downloader.SchedulerAlreadyExists()
        id = Ice.stringToIdentity(name)
        prx = current.adapter.add(servant, id)
        print("New scheduler created {}, {}".format(name, prx))

        self.registry[name] = prx
        prx = Downloader.DownloadSchedulerPrx.checkedCast(prx)

        return prx

    def kill(self, name, current=None):
        '''
        Destroy an existing scheduler
        '''
        if name not in self.registry:
            raise Downloader.SchedulerNotFound()
        print("Removed scheduler: {}".format(name))
        id = Ice.stringToIdentity(name)
        current.adapter.remove(id)

        del(self.registry[name])

    def availableSchedulers(self, current=None):
        '''
        Returns the number of schedulers availables
        '''
        return len(self.registry)


class Server(Ice.Application):

    def get_topic(self, topic_name):
        '''
        Returns the topic if exists, if not creates a new one and returns it
        '''
        topic_mgr_proxy = self.communicator().stringToProxy(ICESTORM_MANAGER)
        if topic_mgr_proxy is None:
            raise Exception("Error getting: {0}".format(ICESTORM_MANAGER))
        topic_mgr = IceStorm.TopicManagerPrx.checkedCast(topic_mgr_proxy)
        if not topic_mgr:
            raise Exception('Invalid IceStorm proxy')

        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)
        finally:
            return topic

    def run(self, args):
        broker = self.communicator()
        adapter = broker.createObjectAdapter('FactoryAdapter')

        publisher = self.get_topic(STATUS_TOPIC).getPublisher()
        progress_publisher = Downloader.ProgressEventPrx.uncheckedCast(publisher)
        print("ProgressTopic created")

        queue = WorkQueue(progress_publisher)
        servant = SchedulerFactoryI(queue)

        proxy = adapter.addWithUUID(servant)
        sync_topic = self.get_topic(SYNC_TOPIC)
        pub = sync_topic.subscribeAndGetPublisher({}, proxy)
        servant.sync_publisher = Downloader.SyncEventPrx.uncheckedCast(pub)
        print("SynTopic created")

        print(proxy, flush=True)

        adapter.activate()
        queue.start()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        queue.destroy()

        return 0


if __name__ == '__main__':
    app = Server()
    sys.exit(app.main(sys.argv))
