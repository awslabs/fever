import logging
import os
import torch
import numpy as np
from sklearn.metrics import accuracy_score
from torch.autograd import Variable
from tqdm import tqdm

from experiments.framework.batching import Batching
from experiments.framework.learning_style import Objective
from experiments.model.model import Model

from sklearn.utils import shuffle

class PyTorchModel(Model):

    def __init__(self, name, path, labels,  feature_functions, vis=None,):

        self.name = name
        self.vis = vis
        self.early_stopping = None
        self.pytorch_logger = logging.getLogger(PyTorchModel.__name__)
        self.path = path
        super().__init__(labels, feature_functions)

    def predict_model(self, name,data):
        self.pytorch_logger.debug("Data: {0}".format(type(data)))

        num_feats = data.shape[1]
        self.pytorch_logger.debug("Number of features {0}".format(num_feats))

        batching = Batching(data, None, os.getenv("TARGET_BATCH_SIZE", 50))
        predictions = []
        for i, batch in enumerate(batching):
            self.model.zero_grad()
            self.model.train()

            b_features, _, actual_batch_size = batch
            X = self.features_to_var(b_features)
            y_pred = self.model(name, X, actual_batch_size)
            predictions.append(torch.max(y_pred, -1)[1].data.numpy())

        return np.concatenate(predictions)

    def lr_schedule(self,optimizer, init_lr, iter, lr_decay_iter=1,
                      max_iter=100, power=0.9):
        if iter == 0 or iter % lr_decay_iter or iter > max_iter:
            return

        lr = init_lr * (1 - iter / max_iter) ** power
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr

    def features_to_var(self,b_features):
        return Variable(torch.FloatTensor(b_features))

    def get_optimizer(self):
        return torch.optim.RMSprop(filter(lambda param: param.requires_grad, self.model.parameters()), lr=1e-3)

    def train_model(self,objectives,dev_data=None,dev_labels=None):
        self.pytorch_logger.info("Training with {0} with {1} objectives".format(type(self.model),len(objectives)))

        if self.model is None:
            num_feats = self.num_features()
            self.pytorch_logger.debug("Number of features {0}".format(num_feats))

            use_gpu = torch.cuda.is_available() and os.getenv("GPU", "0").lower() in ["1", "y", "t", "yes", "true"]
            self.dev_accuracy_history = []
            self.loss_history = []
            self.model, self.early_stopping = self.model_factory(num_feats,objectives,use_gpu)


        for epoch in tqdm(range(os.getenv("NUM_EPOCHS",50)),desc="Epoch",leave=True):

            criterion = torch.nn.CrossEntropyLoss()
            optimizer = self.get_optimizer()

            self.lr_schedule(optimizer, 1e-3, epoch)


            for idx, objective in enumerate(objectives):
                self.pytorch_logger.debug("Objective #{0}".format(idx))
                data, labels = objective.get_data(), objective.get_labels()

                self.pytorch_logger.debug("Data: {0} {1}".format(type(data), data.shape))
                self.pytorch_logger.debug("Labels: {0} {1}".format(type(labels), labels.shape))

                data, labels = shuffle(data,labels)
                bs = os.getenv("TARGET_BATCH_SIZE",250)
                batching = Batching(data, labels, bs)

                batches_done = 0
                epoch_loss = 0

                for i,batch in enumerate(batching):
                    self.model.zero_grad()
                    self.model.train()

                    batches_done += 1
                    b_features, b_labels, actual_batch_size = batch

                    X = self.features_to_var(b_features)
                    y = Variable(torch.LongTensor(b_labels))

                    y_pred = self.model(objective.get_name(), X, actual_batch_size)
                    loss = self.loss_calc(criterion,y_pred,y)
                    loss.backward()

                    optimizer.step()
                    epoch_loss += loss.data[0]

            self.loss_history.append(epoch_loss/batches_done)

            mname = self.name +"-"+ str(type(self.model))
            if self.vis is not None:
                self.vis.line(np.array(self.loss_history), win="{0} Training Loss".format(mname), opts={'title': "{0} Training Loss".format(mname)})

            if dev_data is not None and dev_labels is not None:
                self.dev_accuracy_history.append(self.score(self.predict(Objective(objectives[0].get_name(),objectives[0].get_schema(),dev_data,dev_labels)),dev_labels))
                if self.vis is not None:
                    self.vis.line(np.array(self.dev_accuracy_history), win="{0} Dev Accuracy".format(mname), opts={'title': "{0} Dev Accuracy".format(mname)})

                try:
                    self.early_stopping.check(epoch,self.dev_accuracy_history)
                except StopIteration:
                    self.logger.warning("Early Stopping")
                    break

        if dev_data is not None:
            self.early_stopping.cleanup()


    def scoring_metric(self,predicted,actual):
        return accuracy_score(actual,predicted)

    def model_factory(self,num_feats,objectives,gpu):
        return None,None

    def loss_calc(self,criterion,y_pred,y_actual):
        return criterion(y_pred, y_actual)