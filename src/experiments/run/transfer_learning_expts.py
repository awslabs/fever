import logging
import visdom

from experiments.data.dataset import Dataset
from experiments.data.fever import Fever
from experiments.data.snli import SNLI
from experiments.framework.fever_labels import *
from experiments.framework.labels import Labels
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
    (SNLI, SNLILabels),
    (Fever, Fever3Labels, "fever_2017_9_22_4way_oc"),
    (Fever, Fever3Labels, "fever_2017_9_22_4way_os"),
]

models = [Unlex,Siamese100d]

scores = {}
for idx,v in enumerate(versions_schemata):
    print(v)
    expt = v[0]
    labels = v[1]

    data = ""


    test_objs = []
    if len(v)>2:
        data = v[2]
        train_data = expt("train",data).read()
        dev_data = expt("dev",data).read()
    else:
        train_data = expt("train").read()
        dev_data = expt("dev").read()


    for u in versions_schemata:
        uexpt = u[0]
        ulabels = u[1]

        data2 = ""
        if len(u) > 2:
            data2 = u[2]
            test_objs.append((uexpt,ulabels,data2,uexpt("test", data2).read()))
        else:
            test_objs.append((uexpt,ulabels,None,uexpt("test").read()))

    task = ""+expt.__name__+"_"+labels.__name__+"_"+data



    for m in models:
        model = m(task,labels(),vis=vis)
        train_feats = model.generate_features(task, "train", train_data)
        dev_feats = model.generate_features(task, "dev", dev_data)

        train_labels = model.generate_labels(train_data)
        dev_labels = model.generate_labels(dev_data)

        model.train(train_feats, train_labels,
                    dev={"data": dev_feats,
                         "labels": dev_labels})

        for test_obj in test_objs:
            test_data = test_obj[3]
            test_task = task+"_TXFR_"+test_obj[0].__name__+"_"+test_obj[1].__name__+"_"+(test_obj[2] if test_obj[2] is not None else "")
            test_feats = model.generate_features(test_task, "test", test_data)
            test_labels = model.generate_labels(test_data,test_obj[1]())
            score = model.score(model.predict(test_feats), test_labels)
            scores[test_task+"_"+m.__name__] = score
            print(score)

            vis.text("\n".join([k + ":" + str(v) for k, v in scores.items()]),"scores")
