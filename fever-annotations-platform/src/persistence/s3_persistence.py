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


class S3Writer:
    def __init__(self,bucket):
        self.logger = logging.getLogger(S3Writer.__name__)
        self.s3 = boto3.client('s3')
        self.logger.info("S3 write bucket {0}".format(bucket))
        self.bucket = bucket

    @staticmethod
    def clean(filename):
        filename = filename.split("#")[0]
        return filename.replace("(","-LRB-").replace(")","-RRB-").replace("[","-LSB-").replace("]","-RSB-").replace(":","-COLON-").replace(" ","_")

    def save(self,namespace,name,body):
        self.logger.debug("S3 Save")
        name = self.clean(name)
        self.logger.debug("Put file {0}/{1}".format(namespace,name))
        response = self.s3.put_object(
            Bucket=self.bucket,
            Body=body,
            Key=namespace+"/"+name
        )
        self.logger.debug(response)

    def read(self,key):
        return self.s3.get_object(Bucket=self.bucket,Key=key)



    def read_string(self,key):
        return bytes.decode(self.s3.get_object(Bucket=self.bucket,Key=key)["Body"].read())
