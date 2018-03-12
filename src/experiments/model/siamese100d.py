import logging
import torch
import torch.nn.functional as F
import numpy as np
import os
from functools import reduce
from torch import nn
from torch.autograd import Variable
from tqdm import tqdm
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from experiments.framework.early_stopping import EarlyStopping
from experiments.model.pytorch_wrapper import PyTorchModel


class Siamese100d(PyTorchModel):

    class Siamese100dLSTM(nn.Module):





        def __init__(self,emb_size,emb_dim,objectives,glove,run_cuda):
            self.emb_dim = emb_dim
            self.run_cuda = run_cuda

            super(Siamese100d.Siamese100dLSTM, self).__init__()

            self.emb = nn.Embedding(emb_size, emb_dim)
            self.emb.weight.data.copy_(torch.from_numpy(glove))
            self.emb.weight.requires_grad = False

            self.fc = nn.Linear(emb_dim, 100)

            self.bn300 = nn.BatchNorm1d(300)
            self.bn600 = nn.BatchNorm1d(600)

            self.lstm = nn.LSTM(100, 300)

            self.drp = nn.Dropout(p=0.2)

            self.fc_out1 = nn.Linear(600, 600)
            self.fc_out2 = nn.Linear(600, 600)
            self.fc_out3 = nn.Linear(600, 600)

            self.output_layers = dict()
            for objective in objectives:
                self.output_layers[objective.get_name()] = nn.Linear(600,objective.get_num_classes())
                if self.run_cuda:
                    self.output_layers[objective.get_name()] = self.output_layers[objective.get_name()].cuda()
                self.add_module(objective.get_name() + "_linear", self.output_layers[objective.get_name()])


            self.layers_for_l2 = {self.fc_out1, self.fc_out2, self.fc_out3}

            if run_cuda:
                self.fc = self.fc.cuda()
                self.bn300 = self.bn300.cuda()
                self.bn600 = self.bn600.cuda()
                self.lstm = self.lstm.cuda()
                self.drp = self.drp.cuda()
                self.fc_out1 = self.fc_out1.cuda()
                self.fc_out2 = self.fc_out2.cuda()
                self.fc_out3 = self.fc_out3.cuda()


        def forward(self, name, X, batch_size):
            a1,a2 = X

            a1 = self.emb(a1)
            a2 = self.emb(a2)

            a1 = a1.view(-1, self.emb_dim)
            a2 = a2.view(-1, self.emb_dim)

            if self.run_cuda:
                a1 = a1.cuda()
                a2 = a2.cuda()

            a1 = self.fc(a1).view(batch_size, -1, 100)
            a2 = self.fc(a2).view(batch_size, -1, 100)

            a1 = a1.transpose(0, 1)
            a2 = a2.transpose(0, 1)

            _, a1 = self.lstm(a1)  # Getting final hidden state from the LSTM
            _, a2 = self.lstm(a2)

            a1 = a1[0].squeeze(0)  # h_t
            a2 = a2[0].squeeze(0)

            a1 = self.bn300(a1)
            a2 = self.bn300(a2)

            b = torch.cat((a1, a2), 1)
            b = self.drp(b)

            b = F.relu(self.fc_out1(b))
            b = self.drp(b)
            b = self.bn600(b)

            b = F.relu(self.fc_out2(b))
            b = self.drp(b)
            b = self.bn600(b)

            b = F.relu(self.fc_out3(b))
            b = self.drp(b)
            b = self.bn600(b)

            b = self.output_layers[name](b)

            b = b.cpu()

            return b

        def add_objective(self, objective):
            self.output_layers[objective.get_name()] = nn.Linear(600,objective.get_num_classes())
            if self.run_cuda:
                self.output_layers[objective.get_name()] = self.output_layers[objective.get_name()].cuda()
            self.add_module(objective.get_name() + "_linear", self.output_layers[objective.get_name()])

        def l2loss(self):
            p = 2
            l2acc = lambda params: reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), params)
            param_sum = lambda layer: map(lambda param: \
                                              (torch.sum(torch.pow(param.data, p)),
                                               reduce(lambda x, y: x * y, [dim for dim in param.data.size()]))
                                          , layer)

            params = map(lambda layer_params: l2acc(layer_params),
                         map(lambda layer: param_sum(layer.parameters()), self.layers_for_l2))
            total_weight = l2acc(params)

            return np.power(total_weight[0], 1 / p)


    def features_to_var(self,b_features):
        longest_a = max([len(sample[0]) for sample in b_features])
        longest_b = max([len(sample[1]) for sample in b_features])

        a = np.zeros((len(b_features), longest_a), dtype=np.long)
        b = np.zeros((len(b_features), longest_b), dtype=np.long)
        for idx, sample in enumerate(b_features):
            a[idx] = np.pad(np.array(sample[0]), (longest_a - len(sample[0]), 0), 'constant', constant_values=(0))
            b[idx] = np.pad(np.array(sample[1]), (longest_b - len(sample[1]), 0), 'constant', constant_values=(0))

        a = Variable(torch.from_numpy(a))
        b = Variable(torch.from_numpy(b))

        return a,b






    def model_factory(self, num_feats ,objectives,use_gpu=False):
        torch.manual_seed(1234)
        if use_gpu:
            torch.cuda.manual_seed(1234)

        self.siames_logger.info("Model not initialised. Creating one.")
        model = Siamese100d.Siamese100dLSTM(self.embeddings.shape[0],self.embeddings.shape[1],objectives, self.embeddings,use_gpu)
        if use_gpu:
            self.siames_logger.info("Using GPU")
        early_stopping = EarlyStopping(self.name, Siamese100d.__name__, model, patience=5)
        return model,early_stopping

    def __init__(self, name, labels, vis=None, feature_functions_additional = list()):
        self.siames_logger = logging.getLogger(Siamese100d.__name__)
        feature_functions = [
            self.feat_word_embedding_lookup]
        feature_functions.extend(feature_functions_additional)
        self.l2_lambda = 4e-6
        self.words,self.embeddings = self.load_embeddings()


        super().__init__(name,os.path.join(os.getenv("MODEL_DIR", "models"), name, Siamese100d.__name__),labels,feature_functions,vis)

    def feat_word_embedding_lookup(self,data):
        self.siames_logger.info("Looking up word ids")
        mapped = map(lambda datum: ([self.lookup(word) for word in datum[0]],[self.lookup(word) for word in datum[1]]),tqdm(data))
        return list(mapped)

    def lookup(self,word):
        return self.words[word] if word in self.words else 1

    def loss_calc(self,criterion,y_pred,y_actual):
        return criterion(y_pred, y_actual) + self.l2_lambda * self.model.l2loss()

    def load_embeddings(self):

        embeddings_file = "glove.840B.300d.txt"
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