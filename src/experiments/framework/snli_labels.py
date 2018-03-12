from experiments.framework.labels import Labels


class SNLILabels(Labels):
    def __init__(self):
        states = dict()
        states["entailment"] = 0
        states["contradiction"] = 1
        states["neutral"] = 2

        super().__init__(states)