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
import argparse
import logging

from botocore.exceptions import ClientError

from comms.sqs_comms import SQSClient
from dataset.reader.wiki_parser import WikiParser
from persistence.s3_persistence import S3Writer

import time


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--s3_bucket', required=True, type=str, help='s3 bucket to place parsed articles in')
    parser.add_argument('--sqs_queue', required=True, type=str, help="sqs queue for parser instances to read from")
    args = parser.parse_args()

    start_time = time.time()

    ignore_existing = True

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("Wikipedia article parser")

    sqs = SQSClient(args.sqs_queue)
    s3 = S3Writer(args.s3_bucket)

    parser = WikiParser(s3)

    counter = 0

    while True:
        response = sqs.next()
        if 'Messages' in response:
            for message in response['Messages']:
                try:
                    page = message['Body']
                    logger.info("Process ({1} done, {2:.1f} seconds) {0}".format(page,counter,(time.time() - start_time)))

                    exists = False
                    if not ignore_existing:
                        try:
                            s3.read("intro/"+page)
                            logger.info("Exists in S3, skipping")
                            exists = True
                        except ClientError:
                            logger.info("Does not exist in S3")
		
                    if not exists:
                        obj = s3.read("article/"+page)
                        text = bytes.decode(obj['Body'].read())
                        parser.article_callback(page,text)
                    sqs.delete(message['ReceiptHandle'])
                    counter+=1


                except Exception as e:
                    logger.error(e)

        else:
            logger.info("No new messages")
            time.sleep(5)
