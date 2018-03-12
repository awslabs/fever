import logging
import multiprocessing
import os
import numpy as np
import pathlib

from experiments.framework.sparse import sp_len


class Model:
    def __init__(self,labels,feature_functions):
        self.mapfunction = map #multiprocessing.Pool().map
        self.labels = labels
        self.logger = logging.getLogger(Model.__name__)
        self.feature_functions = feature_functions
        self.stackfn = np.column_stack
        self.loaders = dict()
        self.num_feats = None
        self.model = None

    def num_features(self):
        return self.num_feats

    def register_loader(self,feature_function,loading_function):
        self.loaders[feature_function] = loading_function

    def generate_features(self,dataset,name,data):
        self.logger.info("Generating features for {0} {1} on {2} data".format(dataset,name,len(data)))
        features = self.mapfunction(lambda ff: self.log_and_generate(ff,dataset,name,data), self.feature_functions)
        return self.stackfn(list(features))

    def generate_labels(self,data,override=None):
        self.logger.info("Generating labels on {0} data".format(len(data)))
        label_schema = override if override is not None else self.labels
        labels = self.mapfunction(lambda datum: label_schema.get_index(datum[2]), data)
        return np.array(list(labels),dtype=np.long)

    def log_and_generate(self,feature,dataset,name,data):
        data_dir = os.path.join(os.getenv("FEATURES_DIR","features"),str(dataset),str(name))

        self.logger.debug("Checking if directory exists: {0}".format(data_dir))
        if not os.path.exists(data_dir):
            self.logger.debug("Generating directory {0}".format(data_dir))
            os.makedirs(data_dir)

        self.logger.debug("Checking if features file exists for {0} {1} {2}".format(dataset,name,feature.__name__))
        data_path = os.path.join(data_dir, ".".join(["feature", feature.__name__]))


        if not os.path.exists(data_path+".npy"):
            self.logger.info("Creating features in {0}".format(data_path))
            generated_data = feature(data)
            if feature in self.loaders:
                self.logger.info("Running saver for {0}".format(feature))
                loaded = self.loaders[feature][0](generated_data)
                np.save(data_path,loaded)
            else:
                np.save(data_path,generated_data)
            return generated_data
        else:
            self.logger.info("Loading features from {0}".format(data_path))
            loaded = np.load(data_path+".npy")
            if feature in self.loaders:
                self.logger.info("Running loader for {0}".format(feature))
                loaded = self.loaders[feature][1](loaded)
            return loaded

    def train(self,objectives,dev=None):

        self.logger.info("Training with {0} objectives".format(sp_len(objectives)))

        for idx,objective in enumerate(objectives):
            data,labels = objective.get_data(), objective.get_labels()

            if self.num_feats is None:
                self.num_feats = data.shape[1]
            else:
                assert data.shape[1] == self.num_feats, "Each training objective must have same number of features"

            self.logger.info("Objective {0}: Training with {1} data and {2} labels".format(idx, sp_len(data),sp_len(labels)))
            assert sp_len(data)==sp_len(labels), "Data length must equal label length"

        if dev is None:
            self.train_model(objectives)
        else:
            self.train_model(objectives,dev['data'],dev['labels'])


    def fine_tune(self,objective,dev=None):
        self.logger.info("Fine Tuning model with {0}".format(objective.get_name()))
        data,labels = objective.get_data(), objective.get_labels()
        assert data.shape[1] == self.num_feats, "Each training objective must have same number of features"

        self.add_model_objective(objective)

        if dev is None:
            self.train_model([objective])
        else:
            self.train_model([objective],dev['data'],dev['labels'])


    def add_model_objective(self,objective):
        self.model.add_objective(objective)

    def predict(self,objective):
        data = objective.get_data()
        self.logger.info("Predicting with {0} data".format(sp_len(data)))
        return self.predict_model(objective.get_name(),data)

    def score(self,predicted,actual):
        self.logger.info("Scoring with {0} labels".format(sp_len(predicted)))
        assert sp_len(predicted) == sp_len(actual)
        return self.scoring_metric(predicted,actual)

    def scoring_metric(selfs,predicted,actual):
        pass

    def train_model(self,objectives,dev_data=None,dev_labels=None):
        pass

    def predict_model(self,name,data):
        pass
