# Copyright 2018 Amazon Research Cambridge
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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