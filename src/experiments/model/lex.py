import logging
from functools import reduce

import scipy.sparse
import torch.optim as optim
import random
import torch
import os
import numpy as np
import torch.nn.functional as F
from sklearn.metrics import accuracy_score

from torch import nn
from tqdm import tqdm
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

from experiments.framework.batching import Batching
from experiments.framework.early_stopping import EarlyStopping
from experiments.framework.sparse_io import load_sparse_matrix, save_sparse_matrix
from experiments.model.model import Model
from torch.autograd import Variable

from experiments.model.pytorch_wrapper import PyTorchModel
from experiments.model.unlex import Unlex

from collections import Counter

class Lex(Unlex):

    class LexMLP(nn.Module):
        def __init__(self,input_dim,layers,output_dim,run_cuda):
            super(Lex.LexMLP, self).__init__()
            self.run_cuda = run_cuda

            self.first_layer = nn.Linear(input_dim,layers[0])
            self.hidden1 = nn.Linear(layers[0],output_dim)

            if self.run_cuda:
                self.first_layer = self.first_layer.cuda()
                self.hidden1 = self.hidden1.cuda()



        def forward(self, x, batch_size):
            if self.run_cuda:
                x = x.cuda()

            x = self.first_layer(x)
            x = F.relu(x)
            x = self.hidden1(x)

            return x.cpu()


    def model_factory(self,num_feats,use_gpu=False):
        torch.manual_seed(1234)
        if use_gpu:
            torch.cuda.manual_seed(1234)

        self.lex_logger.info("Model not initialised. Creating one.")
        model = Lex.LexMLP(num_feats, [8], self.labels.count(), use_gpu)
        if use_gpu:
            self.lex_logger.info("Using GPU")
        early_stopping = EarlyStopping(self.name, Lex.__name__, model, patience=5)
        return model,early_stopping


    def __init__(self, name, labels, vis=None):
        self.lex_logger = logging.getLogger(Lex.__name__)
        feature_functions = [self.feat_unigrams, self.feat_bigrams,self.feat_cross_unigrams, self.feat_cross_bigrams]
        super().__init__(name,os.path.join(os.getenv("MODEL_DIR", "models"), name, Lex.__name__),labels,vis,feature_functions)
        self.stackfn = self.join
        self.register_loader(self.feat_unigrams,(save_sparse_matrix,load_sparse_matrix))
        self.register_loader(self.feat_cross_unigrams,(save_sparse_matrix,load_sparse_matrix))
        self.register_loader(self.feat_bigrams,(save_sparse_matrix,load_sparse_matrix))
        self.register_loader(self.feat_cross_bigrams,(save_sparse_matrix,load_sparse_matrix))

        self.top_unigrams=50000
        self.top_bigrams=10000
        self.top_x_unigrams=10000
        self.top_x_bigrams=15000

        self.l2_lambda = 5e-4

    def feat_unigrams(self,data):
        self.lex_logger.info("Computing Unigram Features")


        if not os.path.exists(os.path.join("features",self.name,"lex","unigrams.npy")):
            c = Counter()

            for d in tqdm(data):
                c.update(self.normalize(d[0]))
                c.update(self.normalize(d[1]))

            words_dict = {word[0]:i+1 for i,word in tqdm(enumerate(c.most_common(self.top_unigrams)))}
            words_dict["UNK"] = 0

            if not os.path.exists(os.path.join("features", self.name,"lex")):
                os.makedirs(os.path.join("features",self.name, "lex"))
            np.save(os.path.join("features",self.name, "lex", "unigrams"),words_dict)
        else:
            words_dict = np.load(os.path.join("features", self.name, "lex", "unigrams.npy")).item()

        mapped = map(lambda datum: scipy.sparse.coo_matrix(self.indicator_arr(words_dict, self.normalize(datum[0])) + self.indicator_arr(words_dict, self.normalize(datum[1]))), tqdm(data))
        return scipy.sparse.vstack(list(mapped))


    def feat_cross_unigrams(self,data):
        self.lex_logger.info("Computing Cross-Unigram Features")

        if not os.path.exists(os.path.join("features",self.name,"lex","cross_unigrams.npy")):
            c = Counter()
            for datum in data:
                c.update(["_".join(xw) for xw in self.find_cross_words(datum)])


            words_dict = {word[0]: i + 1 for i, word in tqdm(enumerate(c.most_common(self.top_x_unigrams)))}
            words_dict["UNK"] = 0



            if not os.path.exists(os.path.join("features", self.name,"lex")):
                os.makedirs(os.path.join("features",self.name, "lex"))
            np.save(os.path.join("features",self.name, "lex", "cross_unigrams"),words_dict)
        else:
            words_dict = np.load(os.path.join("features", self.name, "lex", "cross_unigrams.npy")).item()

        mapped = map(lambda datum: scipy.sparse.coo_matrix(self.indicator_arr(words_dict,["_".join(xw) for xw in self.find_cross_words(datum)])), tqdm(data))
        return scipy.sparse.vstack(list(mapped))



    def feat_cross_bigrams(self,data):
        self.lex_logger.info("Computing Cross-Bigram Features")

        if not os.path.exists(os.path.join("features",self.name,"lex","cross_bigrams.npy")):
            c = Counter()
            for datum in data:
                c.update(["__".join(xw) for xw in self.find_cross_bigrams(datum) ])


            words_dict = {word[0]:i+1 for i,word in tqdm(enumerate(c.most_common(self.top_x_bigrams)))}
            words_dict["UNK"] = 0

            if not os.path.exists(os.path.join("features", self.name,"lex")):
                os.makedirs(os.path.join("features",self.name, "lex"))
            np.save(os.path.join("features",self.name, "lex", "cross_bigrams"),words_dict)
        else:
            words_dict = np.load(os.path.join("features", self.name, "lex", "cross_bigrams.npy")).item()

        mapped = map(lambda datum: scipy.sparse.coo_matrix(self.indicator_arr(words_dict,["__".join(xw) for xw in self.find_cross_bigrams(datum)])), tqdm(data))
        ss =  scipy.sparse.vstack(list(mapped))
        return ss






    def find_cross_words(self,datum):
        x_words = []

        datum2 = [self.normalize(datum[0]), self.normalize(datum[1])]
        for widx, pos in enumerate(datum[3]):
            for idx, pos2 in enumerate(datum[4]):
                if pos == pos2:
                    if widx >= len(datum2[0]):
                        print(datum)
                    if idx >= len(datum2[1]):
                        print(datum)

                    x_words.append((datum2[0][widx], datum2[1][idx]))

        return x_words





    def find_cross_bigrams(self,datum):
        x_words = []

        datum2 = [self.ngrams(self.normalize(datum[0])), self.ngrams(self.normalize(datum[1]),2)]
        for widx, pos in enumerate(self.ngrams(datum[3], 2)):
            for idx, pos2 in enumerate(self.ngrams(datum[4], 2)):
                if pos.split("_")[1] == pos2.split("_")[1]:
                    x_words.append((datum2[0][widx],datum2[1][idx]))

        return x_words



    def feat_bigrams(self,data):
        self.lex_logger.info("Computing Bigram Features")

        if not os.path.exists(os.path.join("features",self.name,"lex","bigrams.npy")):
            c = Counter()
            for d in tqdm(data):
                c.update(self.ngrams(self.normalize(d[0]),2))
                c.update(self.ngrams(self.normalize(d[1]),2))


            words_dict = {word[0]:i+1 for i,word in tqdm(enumerate(c.most_common(self.top_bigrams)))}
            words_dict["UNK"] = 0



            if not os.path.exists(os.path.join("features",self.name,"lex")):
                os.makedirs(os.path.join("features",self.name, "lex"))
            np.save(os.path.join("features",self.name, "lex", "bigrams"),words_dict)
        else:
            words_dict = np.load(os.path.join("features", self.name, "lex", "bigrams.npy")).item()

        mapped = map(lambda datum: scipy.sparse.coo_matrix(self.indicator_arr(words_dict, self.ngrams(self.normalize(datum[0]),2)) + self.indicator_arr(words_dict, self.ngrams(self.normalize(datum[1]),2))), tqdm(data))
        return scipy.sparse.vstack(list(mapped))



    def ngrams(self,words,n=2):
        return ["_".join(ng) for ng in list(zip(*[words[i:] for i in range(n)]))]





    def features_to_var(self,b_features):
        mat = b_features.todok()
        return Variable(
            torch.sparse.FloatTensor(
                torch.from_numpy(
                    np.array(
                        list(mat.keys()),dtype=np.long)).t(),
                torch.from_numpy(
                    np.array(
                        list(mat.values()),dtype=np.float32)),
                torch.Size(mat.shape)).to_dense())


    def normalize(self,data):
        return [d.lower() for d in data]

    def indicator_arr(self,words_dict,words):
        arr = np.zeros(len(words_dict))
        for word in words:
            arr[self.lookup(words_dict,word)]=1
        return arr

    def lookup(self,words_dict,word):
       return words_dict[word] if word in words_dict else words_dict["UNK"]

    def join(self,bits):
        sparse = list(filter(lambda bit: scipy.sparse.isspmatrix(bit), bits))
        not_sparse = list(filter(lambda bit: not scipy.sparse.isspmatrix(bit), bits))

        return scipy.sparse.hstack([scipy.sparse.coo_matrix(not_sparse).T]+sparse)

    def loss_calc(self,criterion,y_pred,y_actual):
        return criterion(y_pred, y_actual)

    def get_optimizer(self):
        return torch.optim.RMSprop(filter(lambda param: param.requires_grad, self.model.parameters()), lr=1e-3, weight_decay=self.l2_lambda)
