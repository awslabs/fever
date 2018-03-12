from experiments.framework.labels import Labels


class Fever6Labels(Labels):
    def __init__(self):
        states = dict()
        states["rephrase"] = 0
        states["original"] = 0
        states["negate"] = 1
        states["neg"] = 1
        states["substitute_similar"] = 2
        states["sim"] = 2
        states["substitute_dissimilar"] = 3
        states["dis"] = 3
        states["specific"] = 4
        states["spec"] = 4
        states["gen"] = 5
        states["general"] = 5

        super().__init__(states)


class Fever5Labels(Labels):
    def __init__(self):
        states = dict()
        states["rephrase"] = 0
        states["original"] = 0
        states["negate"] = 1
        states["neg"] = 1
        states["substitute_similar"] = 2
        states["sim"] = 2
        states["substitute_dissimilar"] = 2
        states["dis"] = 2
        states["specific"] = 3
        states["spec"] = 3
        states["gen"] = 4
        states["general"] = 4

        super().__init__(states)


class Fever4Labels(Labels):
    def __init__(self):
        states = dict()
        states["rephrase"] = 0
        states["original"] = 0
        states["negate"] = 1
        states["neg"] = 1

        states["specific"] = 3
        states["spec"] = 3
        states["gen"] = 4
        states["general"] = 4

        super().__init__(states)


class Fever3Labels(Labels):
    def __init__(self):
        states = dict()
        states["rephrase"] = 0
        states["original"] = 0
        states["negate"] = 1
        states["neg"] = 1

        states["specific"] = 2
        states["spec"] = 2
        states["gen"] = 0
        states["general"] = 0



        super().__init__(states)


class Fever2Labels(Labels):
    def __init__(self):
        states = dict()
        states["rephrase"] = 0
        states["original"] = 0
        states["gen"] = 0
        states["general"] = 0

        states["negate"] = 1
        states["neg"] = 1
        states["specific"] = 1
        states["spec"] = 1

        states["substitute_similar"] = 1
        states["sim"] = 1
        states["substitute_dissimilar"] = 1
        states["dis"] = 1

        super().__init__(states)
