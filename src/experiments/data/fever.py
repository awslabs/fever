import json
import logging
import os

from tqdm import tqdm

from experiments.data.dataset import Dataset


class Fever(Dataset):
    def __init__(self, filename, version, data_dir="./data/"):
        self.snli_logger = logging.getLogger(Fever.__name__)

        file = filename + "_" + version + ".jsonl"
        self.data_dir = data_dir
        super().__init__(os.path.join(data_dir,file))

    def read_file(self,file):
        data = []
        with open(file,"r") as f:
            for line in f.readlines():
                data.append(json.loads(line))
        return data

    def process(self,file):
        return self.preprocess(self.read_file(file))


    def preprocess(self,snli_examples):
        ret = []

        self.snli_logger.info("Tokenizing Sentences for {0}".format(self.file))
        for item in tqdm(snli_examples):
            if item['type'] != "sub":
                ret.append((item['original'], item['mutation'], item['type'],item['original_pos'],item['mutation_pos']))

        return ret