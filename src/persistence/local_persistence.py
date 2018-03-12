

import logging


class LocalQueuePersistence:
    def __init__(self,queue):
        self.logger = logging.getLogger(LocalQueuePersistence.__name__)
        self.logger.info("Local queuing persistence {0}".format(queue))
        self.queue = queue

    def save(self,*args):
        self.logger.debug("Enqueue {0}/{1}".format(args[0],args[1]))
        self.queue.enqueue(args)