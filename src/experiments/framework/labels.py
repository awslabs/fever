import logging


class Labels:
    def __init__(self,labels):
        self.logger = logging.getLogger(Labels.__name__)
        self.label_dict = labels
        self.index_dict = {v: k for k, v in labels.items()}
        self.logger.info("Created Label Dictionary")
        self.logger.debug("Lookup Labels {0}".format(self.label_dict))
        self.logger.debug("Reverse Lookup Labels {0}".format(self.index_dict))

    def get_index(self,name):
        return self.label_dict[name] if name in self.label_dict else None

    def get_name(self,index):
        return self.index_dict[index] if index in self.index_dict else None

    def count(self):
        return len(self.label_dict.values())