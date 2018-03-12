import logging
import torch
import numpy as np
import os
from torch import nn
from tqdm import tqdm
from experiments.framework.early_stopping import EarlyStopping
from experiments.model.pytorch_wrapper import PyTorchModel
from model import Entailment


class LSTMWithAttention(PyTorchModel):


    def model_factory(self,num_feats,objectives,use_gpu=False):
        torch.manual_seed(1234)
        if use_gpu:
            torch.cuda.manual_seed(1234)

        self.siames_logger.info("Model not initialised. Creating one.")

        vocab_size,embedding_dim = self.embeddings.shape

        emb = torch.from_numpy(self.embeddings)
        if use_gpu:
            self.attn_logger.info("Using GPU for embeddings")
            emb = emb.cuda()

        # (self.embeddings.shape[0],self.embeddings.shape[1],300,1, self.labels.count(), self.embeddings)
        model = Entailment(vocab_size, embedding_dim, embedding_dim, W_emb=emb, p=0.8, num_layers=1, train_emb=False)

        if use_gpu:
            self.attn_logger.info("Using GPU for model")
            model = model.cuda()



        early_stopping = EarlyStopping(self.name, LSTMWithAttention.__name__, model, patience=5)
        return model,early_stopping

    def __init__(self, name, labels, vis=None, feature_functions_additional = list()):
        self.attn_logger = logging.getLogger(LSTMWithAttention.__name__)
        feature_functions = [
            self.feat_word_embedding_lookup]
        feature_functions.extend(feature_functions_additional)
        self.l2_lambda = 4e-6
        self.words,self.embeddings = self.load_embeddings()


        super().__init__(name,os.path.join(os.getenv("MODEL_DIR", "models"), name, LSTMWithAttention.__name__),labels,feature_functions,vis)

    def feat_word_embedding_lookup(self,data):
        self.attn_logger.info("Looking up word ids")
        mapped = map(lambda datum: ([self.lookup(word) for word in datum[0]],[self.lookup(word) for word in datum[1]]),tqdm(data))
        return list(mapped)

    def lookup(self,word):
        return self.words[word] if word in self.words else 1

    def loss_calc(self,criterion,y_pred,y_actual):
        return criterion(y_pred, y_actual) + self.l2_lambda * self.model.l2loss()

    def load_embeddings(self):




        embeddings_file = "word2vec.840B.300d.txt"
        data_dir = "data"

        self.siames_logger.info("Trying to load embeddings from pickle file")

        if os.path.exists(os.path.join("data","embeddings.npy")):
            self.siames_logger.info("Embeddings file exists. loading")
            return np.load(os.path.join("data","words.npy")).item(), np.load(os.path.join("data","embeddings.npy"))


        self.siames_logger.info("Embeddings file does not exist. Importing")
        emb_file = os.path.join(data_dir, embeddings_file)


        self.siames_logger.info("Counting size of vocab")
        with open(emb_file) as f:
            for i, l in enumerate(f):
                pass
        vocab_size = i + 1
        self.siames_logger.info("Vocab size is {0}".format(vocab_size))


        emb_size = vocab_size + 3
        words = dict()

        i = 3

        embeddings = np.zeros((emb_size, 300))

        self.siames_logger.info("Importing embeddings")
        with open(emb_file, "r") as f:
            for line in tqdm(f,total=vocab_size):

                if len(line) == 0:
                    break
                bits = line.split()
                try:
                    embeddings[i, :] = np.array(bits[-300:])
                except Exception as e:
                    self.siames_logger.error(e)
                    self.siames_logger.error("At position {0}. Could not import this row: \n{1}".format(i, bits))

                words[" ".join(bits[:-300])] = i
                i += 1

        np.save(os.path.join("data","embeddings"),embeddings)
        np.save(os.path.join("data","words"),words)
        return words,embeddings