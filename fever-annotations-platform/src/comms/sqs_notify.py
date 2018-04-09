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


import logging

from persistence.s3_persistence import S3Writer


class SQSNotify(object):
    def __init__(self, persistence, sqs):
        self.logger = logging.getLogger(SQSNotify.__name__)
        self.persistence = persistence
        self.sqs = sqs

    def article_callback(self, title, source):
        self.sqs.send(S3Writer.clean(title))
        self.persistence.put("article", title, source)
