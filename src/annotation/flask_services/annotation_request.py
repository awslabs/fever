from flask import jsonify
import random

class AnnotationRequest:
    def __init__(self, dataset, claim=None):
        super().__init__()

        if claim is None:
            self.example = dataset[random.randint(0, len(dataset))]
        else:
            self.example = dataset[int(claim)]

        while len(self.example["sentence"].strip()) == 0:
            self.example = dataset[random.randint(0, len(dataset)-1)]

    def get_dict(self):
        annotation_dict = dict()
        annotation_dict.update(self.example)
        return annotation_dict

    def get_json(self):
        return jsonify(self.get_dict())