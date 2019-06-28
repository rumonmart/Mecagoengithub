#!/usr/bin/python3
# -*- mode:python; coding:utf-8; tab-width:4 -*

'''
Implementation of classes Shell and Client
'''

import os
import binascii
import sys
import random
import uuid
import cmd

import Ice
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import Downloader

BLOCK_SIZE = 10240

class Shell(cmd.Cmd):
    '''
    Class where the commands used in the client terminal are defined
    '''
    prompt = 'Downloader> '
    client = None

    @property
    def online(self):
        if self.client is None:
            return False
        return self.client.factory is not None

    def _compute_prompt_(self):
        if self.online:
            self.prompt = 'Downloader (online)> '
        else:
            self.prompt = 'Downloader> '

    def precmd(self, line):
        self._compute_prompt_()
        return line

    def postcmd(self, stop, line):
        self._compute_prompt_()
        return stop

    def emptyLine(self):
        pass

    def default(self, line):
        line = line.strip()
        if line.startswith('#') or line.startswith('//'):
            return
        print('ERROR: command not recognized: %s' % line.split()[0])

    def do_connect(self, line):
        '''
        Method used to connect with a factory by means of a endpoint
        '''
        if self.online:
            print('ERROR: already connected')
            return
        self.client.connect_factory(line)

    def do_disconnect(self, line):
        '''
        Method used to disconnect from factory
        '''
        if not self.online:
            print('ERROR: you are disconnected')
            return
        self.client.disconnect()

    def do_new_scheduler(self, line):
        '''
        Method used to create a scheduler
        '''
        if not self.online:
            print('ERROR: you are not connected to a factory')
            return None
        if line == '':
            name = str(uuid.uuid4())
        else:
            name = line

        try:
            self.client.make_scheduler(name)
        except Exception as error:
            print("ERROR: {}".format(error))

    def do_del_scheduler(self, line):
        '''
        Method to delete a scheduler
        '''
        if not self.online:
            print('ERROR: you are not connected to a factory')
        return None

        try:
            self.client.remove_scheduler(line)
            print('***Scheduler has been removed***')
        except Exception as error:
            print("ERROR: {}".format(error))

    def do_list_schedulers(self, line):
        '''
        Method to print all the created schedulers
        '''
        if not self.client.schedulers:
            print('There are no schedulers created')
        else:
            for scheduler in self.client.schedulers:
                print("\n{}".format(scheduler))

    def do_add_download(self, line):
        '''
        Add a new file to download
        '''
        self.client.add_download(line)

    def do_list_songs(self, line):
        '''
        Method to print all the songs availables
        '''
        try:
            songs = self.client.songs
        except Exception as error:
            print("ERROR: {}". format(error))

        if not songs:
            print('There are no songs availables')
            return

        for song in songs:
            print("\n{}".format(song))

    def do_get_song(self, line):
        '''
        Method to download the song file
        '''
        self.client.get(line)

    def do_quit(self, line):
        '''
        Method to quit the client
        '''
        if self.online:
            self.do_disconnect(line)
        return True


class Client(Ice.Application):
    '''
    Client class used to manage the dowload of songs
    '''
    factory = None
    schedulers = {}

    @property
    def scheduler(self):
        if not self.factory:
            raise RuntimeError('Not connected')
        if not self.schedulers:
            self.make_scheduler(str(uuid.uuid4()))
        return random.choice(list(self.schedulers.values()))

    @property
    def songs(self):
        '''
        List songs already download
        '''
        try:
            return self.scheduler.getSongList()
        except Exception:
            raise Exception('Error while getting songs list')

    def connect_factory(self, proxy):
        '''
        Connect to factory
        '''
        factory_prx = self.communicator().stringToProxy(proxy)
        if not factory_prx:
            print('ERROR: invalid proxy for factory')
            return -1
        self.factory = Downloader.SchedulerFactoryPrx.checkedCast(factory_prx)
        if not self.factory:
            print('ERROR: invalid factory')
            return -1

    def disconnect(self):
        '''
        Disconnect from factory
        '''
        if self.factory is None:
            return
        for key in self.schedulers.keys():
            self.factory.kill(key)
        self.factory = None
        self.schedulers = {}


    def make_scheduler(self, name):
        '''
        Create a new scheduler
        '''
        if self.factory is None:
            raise RuntimeError('Not connected')
        try:
            self.schedulers[name] = self.factory.make(name)
        except Downloader.SchedulerAlreadyExists:
            raise Exception("Scheduler {} already exists".format(name))


    def remove_scheduler(self, name):
        '''
        Remove an existing scheduler
        '''
        if self.factory is None:
            raise RuntimeError('Not connected')
        try:
            self.factory.kill(name)
        except Downloader.SchedulerNotFound:
            raise Exception("Scheduler {} not found".format(name))
        del(self.scheduler[name])


    def add_download(self, url):
        '''
        Add a new song to download by using a URL
        '''
        self.scheduler.addDownloadTask(url)
        print('***Download success***')

    def get(self, song, destination='./'):
        '''
        Get the song downloaded to your device
        '''
        remoteFd = self.scheduler.get(song)
        with open(os.path.join(destination, song), 'wb') as fd:
            remoteEOF = False
            while not remoteEOF:
                data = remoteFd.recv(BLOCK_SIZE)
                if len(data) > 1:
                    data = data[1:]
                data = binascii.a2b_base64(data)
                remoteEOF = len(data) < BLOCK_SIZE
                if data:
                    fd.write(data)
            remoteFd.end()

    def run(self, args):
        shell = Shell()
        shell.client = self
        shell.cmdloop()
        return 0

sys.exit(Client().main(sys.argv))
