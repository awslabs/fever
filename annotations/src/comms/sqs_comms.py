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


import boto3
import logging
import time


class SQSClient:
    def __init__(self, queue):
        self.max_retries = 5
        self.sqs = boto3.client("sqs")
        self.logger = logging.getLogger(SQSClient.__name__)
        self.q = queue

    def next(self, retry=0):
        try:
            msg = self.sqs.receive_message(QueueUrl=self.q)
            return msg
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Retry {0} of {1}".format(retry+1, self.max_retries))
            time.sleep(5)
            return self.next(retry) if retry <= self.max_retries else None

    def delete(self, message):
        self.sqs.delete_message(QueueUrl=self.q, ReceiptHandle=message)

    def put(self, message, retry=0):
        try:
            self.sqs.send_message(QueueUrl=self.q, MessageBody=message)
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Retry {0} of {1}".format(retry + 1, self.max_retries))
            time.sleep(5)
            if retry <= self.max_retries:
                self.put(message, retry)
