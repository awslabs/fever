import logging
import numpy as np
import visdom

from experiments.data.dataset import Dataset
from experiments.data.fever import Fever
from experiments.data.snli import SNLI
from experiments.framework.fever_labels import *
from experiments.framework.labels import Labels
from experiments.framework.learning_style import Objective
from experiments.framework.logging import get_logger
from experiments.framework.snli_labels import SNLILabels
from experiments.model.lex import Lex
from experiments.model.model import Model
from experiments.model.siamese100d import Siamese100d
from experiments.model.unlex import Unlex

logger = get_logger(logging.DEBUG)

logging.getLogger(Dataset.__name__).setLevel(logging.DEBUG)
logging.getLogger(Dataset.__name__).addHandler(logger)

logging.getLogger(SNLI.__name__).setLevel(logging.DEBUG)
logging.getLogger(SNLI.__name__).addHandler(logger)

logging.getLogger(Fever.__name__).setLevel(logging.DEBUG)
logging.getLogger(Fever.__name__).addHandler(logger)

logging.getLogger(Labels.__name__).setLevel(logging.DEBUG)
logging.getLogger(Labels.__name__).addHandler(logger)

logging.getLogger(Model.__name__).setLevel(logging.DEBUG)
logging.getLogger(Model.__name__).addHandler(logger)

logging.getLogger(Lex.__name__).setLevel(logging.DEBUG)
logging.getLogger(Lex.__name__).addHandler(logger)

logging.getLogger(Unlex.__name__).setLevel(logging.DEBUG)
logging.getLogger(Unlex.__name__).addHandler(logger)

logging.getLogger(Siamese100d.__name__).setLevel(logging.DEBUG)
logging.getLogger(Siamese100d.__name__).addHandler(logger)

vis = visdom.Visdom()


versions_schemata = [
    (Fever, Fever6Labels, "fever_2017_9_22_6way_oc",(SNLI, SNLILabels)),
    (Fever, Fever6Labels, "fever_2017_9_22_6way_os",(SNLI, SNLILabels)),
    (SNLI, SNLILabels, None,(Fever, Fever6Labels)),
    (SNLI, SNLILabels, None,(Fever, Fever6Labels)),
]

models = [Unlex,Siamese100d]

scores = {}

vis.text("Training FT", "FT scores")

for v in versions_schemata:
    print(v)
    expt = v[0]
    labels = v[1]
    extra_obj = v[3]

    data = ""


    if len(v)>2 and v[2] is not None:
        data = v[2]
        train_data = expt("train",data).read()
        dev_data = expt("dev",data).read()
        test_data = expt("test",data).read()

    else:
        train_data = expt("train").read()
        dev_data = expt("dev").read()
        test_data = expt("test").read()


    task = expt.__name__+"_"+labels.__name__+"_"+data


    for m in models:
        objs = []
        model = m(task,labels(),vis=vis)
        train_feats = model.generate_features(task, "train", train_data)
        dev_feats = model.generate_features(task, "dev", dev_data)
        test_feats = model.generate_features(task, "test", test_data)

        train_labels = model.generate_labels(train_data)
        dev_labels = model.generate_labels(dev_data)
        test_labels = model.generate_labels(test_data)

        objective = Objective(labels.__name__, labels(), train_feats,train_labels)

        objs.append(objective)

        model.train(objs,
                    dev={"data": dev_feats,
                         "labels": dev_labels})

        score = model.score(model.predict(Objective(objs[0].get_name(),objs[0].get_schema(),test_feats,test_labels)), test_labels)


        scores[task+"_"+m.__name__] = score
        print(score)

        vis.text("\n".join([k + ":" + str(v) for k, v in scores.items()]),"FT scores")



        extra_train_data = extra_obj[0]("train").read()
        extra_dev_data = extra_obj[0]("dev").read()
        extra_test_data = extra_obj[0]("test").read()

        extra_task = task + "_FT_" + extra_obj[0].__name__ + "_" + extra_obj[1].__name__

        extra_train_feats = model.generate_features(extra_task, "train", extra_train_data)
        extra_dev_feats = model.generate_features(extra_task, "dev", extra_dev_data)
        extra_test_feats = model.generate_features(extra_task, "test", extra_test_data)

        extra_train_labels = model.generate_labels(extra_train_data,extra_obj[1]())
        extra_dev_labels = model.generate_labels(extra_dev_data,extra_obj[1]())
        extra_test_labels = model.generate_labels(extra_test_data,extra_obj[1]())

        extra_objective = Objective(extra_obj[1].__name__, extra_obj[1](), extra_train_feats, extra_train_labels)

        model.fine_tune(extra_objective,dev={"data": extra_dev_feats,
                         "labels": extra_dev_labels})


        score = model.score(model.predict(Objective(extra_objective.get_name(), extra_objective.get_schema(),extra_test_feats,extra_test_labels)), extra_test_labels)

        scores[extra_task+"_"+m.__name__] = score
        print(score)




        vis.text("\n".join([k + ":" + str(v) for k, v in scores.items()]),"FT scores")
