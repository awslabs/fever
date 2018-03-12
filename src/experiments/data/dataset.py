import logging

class Dataset:
    def __init__(self,file):
        self.logger = logging.getLogger(Dataset.__name__)
        self.file = file

    def path(self):
        return self.file

    def read(self):
        self.logger.info("Reading {0}".format(self.file))
        ret = self.process(self.file)
        self.logger.info("Finished Reading {0}".format(self.file))
        return ret

    def process(self,file):
        pass