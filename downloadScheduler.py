#!/usr/bin/python3
# -*- mode:python; coding:utf-8; tab-width:4 -*-

'''
Implementation of classes Transfer, DownloadScheduler and ProgressEvent
'''

import binascii
import Ice
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
# pylint: disable=C0413
# pylint: disable=W0613
import Downloader





class TransferI(Downloader.Transfer):
    '''
    This class is going to be used to transfer the file
    '''

    def __init__(self, local_file):
        self.file = open(local_file, 'rb')

    def recv(self, size, current=None):
        return str(
            binascii.b2a_base64(self.file.read(size), newline=False))

    def end(self, current=None):
        self.file.close()
        current.adapter.remove(current.id)


class DownloadSchedulerI(Downloader.DownloadScheduler, Downloader.SyncEvent):
    '''
    This is the scheduler used to get the files from Youtube
    '''

    downloaded_files = set()

    def __init__(self, tasks_queue, sync_publisher):
        self.tasks = tasks_queue
        self.sync_publisher = sync_publisher

    def addDownloadTask(self, url, current=None):
        '''
        Receives the download requests
        '''
        callback = Ice.Future()
        self.tasks.add(callback, url, self.downloaded_files)
        return callback

    def getSongList(self, current=None):
        '''
        Shows the list of songs
        '''
        songs_list = list(self.downloaded_files)
        return songs_list

    def get(self, file, current=None):
        '''
        Download the files located in the server
        '''
        adapter = current.adapter.addWithUUID(TransferI(file))
        prx = Downloader.TransferPrx.checkedCast(adapter)
        return prx

    def requestSync(self, current=None):
        '''
        Handles the request of the servers to sync all the songs
        '''
        print('Sync() requested')
        if self.sync_publisher:
            songs_list = list(self.downloaded_files)
            self.sync_publisher.notify(songs_list)

    def notify(self, songs, current=None):
        '''
        Synchronizes the songs from all the servers
        '''
        print('Received songs: %s' % songs)
        self.downloaded_files = self.downloaded_files.union(set(songs))

class ProgressEventI(Downloader.ProgressEvent):
    '''
    Class which is the responsable to show the status of the download
    '''
    sync_progress = None
    def __init__(self, sync_progress):
        self.sync_progress = sync_progress

    def notify(self, clipData, current=None):
        print('Song %s' %clipData.URL)
        print('Status %s' %clipData.status)
