
class LearningStyle:
    def __init__(self):
        self.objectives = []

class Objective:
    def __init__(self,name,schema,data,labels):
        self.name = name
        self.schema = schema
        self.data = data
        self.labels = labels

    def get_data(self):
        return self.data

    def get_labels(self):
        return self.labels

    def get_schema(self):
        return self.schema

    def get_num_classes(self):
        return self.schema.count()

    def get_name(self):
        return self.name

class TrainTest(LearningStyle):
    def __init__(self):
        super()

    def add_objective(self,obj):
        self.objectives.append(obj)



class TrainDevTest(LearningStyle):
    def __init__(self,train,dev,test):
        super()

    def add_objective(self,obj):
        self.objectives.append(obj)


