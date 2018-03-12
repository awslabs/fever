import logging
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
from experiments.model.model import Model
from torch.autograd import Variable

from experiments.model.pytorch_wrapper import PyTorchModel


class Unlex(PyTorchModel):

    class UnlexMLP(nn.Module):
        def __init__(self,input_dim,layers,objectives,run_cuda):
            super(Unlex.UnlexMLP, self).__init__()
            self.layers = layers
            self.run_cuda = run_cuda

            self.first_layer = nn.Linear(input_dim,layers[0])

            self.output_layers = dict()
            for objective in objectives:
                self.output_layers[objective.get_name()] = nn.Linear(layers[0],objective.get_num_classes())
                if self.run_cuda:
                    self.output_layers[objective.get_name()] = self.output_layers[objective.get_name()].cuda()

                self.add_module(objective.get_name() + "_linear", self.output_layers[objective.get_name()])

            if self.run_cuda:
                self.first_layer = self.first_layer.cuda()

        def forward(self, name, x, batch_size):
            if self.run_cuda:
                x = x.cuda()

            x = self.first_layer(x)
            x = F.relu(x)
            x = self.output_layers[name](x)
            return x.cpu()

        def add_objective(self, objective):
            self.output_layers[objective.get_name()] = nn.Linear(self.layers[0],objective.get_num_classes())
            if self.run_cuda:
                self.output_layers[objective.get_name()] = self.output_layers[objective.get_name()].cuda()
            self.add_module(objective.get_name()+"_linear",self.output_layers[objective.get_name()])


    def model_factory(self,num_feats,objectives,use_gpu=False):
        torch.manual_seed(1234)
        if use_gpu:
            torch.cuda.manual_seed(1234)

        self.unlex_logger.info("Model not initialised. Creating one.")
        model = Unlex.UnlexMLP(num_feats, [8], objectives, use_gpu)
        if use_gpu:
            self.unlex_logger.info("Using GPU")
        early_stopping = EarlyStopping(self.name, Unlex.__name__, model, patience=5)
        return model,early_stopping


    def __init__(self, name, labels, path=None, vis=None, feature_functions_additional = list()):
        self.unlex_logger = logging.getLogger(Unlex.__name__)
        self.unlex_feature_functions = [
            self.feat_bleu_score,
            self.feat_length_difference,
            self.feat_unigram_word_abs_overlap,
            self.feat_unigram_word_rel_overlap,
            self.feat_filtered_unigram_word_abs_overlap,
            self.feat_filtered_unigram_word_rel_overlap]
        feature_functions = []
        feature_functions.extend(self.unlex_feature_functions)
        feature_functions.extend(feature_functions_additional)

        if path is None:
            path = os.path.join(os.getenv("MODEL_DIR", "models"), name, Unlex.__name__)

        super().__init__(name,path,labels,feature_functions,vis)

    def feat_bleu_score(self,data):
        self.unlex_logger.info("Computing BLEU scores")
        sm = SmoothingFunction()
        mapped = map(lambda datum: sentence_bleu([datum[0]],datum[1],smoothing_function=sm.method1),tqdm(data))
        return list(mapped)

    def feat_length_difference(self,data):
        self.unlex_logger.info("Computing differences in sentence lengths")
        mapped = map(lambda datum: len(datum[0]) - len(datum[1]),tqdm(data))
        return list(mapped)

    def feat_unigram_word_abs_overlap(self,data):
        self.unlex_logger.info("Computing unigram absolute word overlap")
        mapped = map(lambda datum: self._calc_abs_overlap(datum[0],datum[1]), tqdm(data))
        return list(mapped)

    def feat_unigram_word_rel_overlap(self,data):
        self.unlex_logger.info("Computing unigram absolute word overlap")
        mapped = map(lambda datum: self._calc_relative_overlap(datum[0],datum[1]), tqdm(data))
        return list(mapped)

    def feat_filtered_unigram_word_abs_overlap(self,data):
        self.unlex_logger.info("Computing unigram absolute word overlap")
        mapped = map(lambda datum: self._calc_abs_overlap(self.filter_pos(datum[0],datum[3]),self.filter_pos(datum[1],datum[4])), tqdm(data))
        return list(mapped)

    def feat_filtered_unigram_word_rel_overlap(self,data):
        self.unlex_logger.info("Computing unigram absolute word overlap")
        mapped = map(lambda datum: self._calc_relative_overlap(self.filter_pos(datum[0],datum[3]),self.filter_pos(datum[1],datum[4])), tqdm(data))
        return list(mapped)

    def filter_pos(self,words,pos):
        allowed = {"JJ","JJR","JJS","NN","NNS","NNP","NNPS","RB","RBR","RBS","VB","VBD","VBG","VBN","VBP","VBZ"}
        found = list(zip(*filter(lambda w: w[1] in allowed, zip(words,pos))))
        return found[0] if len(found)>0 else []

    def _calc_abs_overlap(self,a,b):
        return len(set(a).intersection(b))

    def _calc_relative_overlap(self,a,b):
        return len(set(a).intersection(b))/len(set(a).union(b)) if len(a) > 0 and len(b) > 0 else 0
