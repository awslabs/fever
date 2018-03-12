import logging
import os
import json

from tqdm import tqdm

from experiments.data.dataset import Dataset

class SNLI(Dataset):
    def __init__(self, file, data_dir="./data/snli_1.0"):
        self.snli_logger = logging.getLogger(SNLI.__name__)

        file = "snli_1.0_" + file + ".jsonl"
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


    # Credit @Smerity https://github.com/Smerity/keras_snli/
    def get_tokens(self,parse):
        return parse.replace('(', ' ').replace(')', ' ').replace('-LRB-', '(').replace('-RRB-', ')').split()

    def get_pos(self,parse):
        return list(
            filter(None, parse.
                   replace("(ROOT", "").

                   replace("(SBARQ", "").
                   replace("(SBAR", "").

                   replace("(SQ", "").
                   replace("(S","").

                   replace("(NP", "").
                   replace("(VP", "").
                   replace("(ADVP", "").
                   replace("(ADJP", "").
                   replace("(FRAG", "").
                   replace("(WHNP" ,"").
                   replace("(WHPP" ,"").
                   replace("(WHADJP" ,"").

                   replace("(WHADVP", "").
                   replace("(X" ,"").
                   replace("(NX" ,"").
                   replace("(RRC" ,"").
                   replace("(UCP" ,"").
                   replace("(LST","").
                   replace("(INTJ","").
                   replace("(PRN" ,"").
                   replace("(CONJP" ,"").
                   replace("(PRT" ,"").
                   replace("(QP","").
                   replace("(Q","").
                   replace("(PP", "").
                   replace("(.", "").
                   replace("(,", "").

                   replace("(", "").
                   replace(")", "").
                   replace('-LRB-', '(').
                   replace('-RRB-', ')').

                   split()
                   )
            )[::2]

    def preprocess(self,snli_examples):
        ret = []

        self.snli_logger.info("Tokenizing Sentences for {0}".format(self.file))
        for item in tqdm(snli_examples):
            if item['gold_label'] != "-":
                ret.append((self.get_tokens(item['sentence1_binary_parse']), self.get_tokens(item['sentence2_binary_parse']),
                        item['gold_label'],self.get_pos(item['sentence1_parse']),self.get_pos(item['sentence2_parse'])))

        return ret