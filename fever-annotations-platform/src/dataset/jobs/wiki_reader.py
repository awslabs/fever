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
import os
import xml

import logging

import time
from bz2 import BZ2File
from threading import Thread

from multiprocessing import Process

from comms.sqs_comms import SQSClient
from dataset.reader.article_queue import ArticleReadingQueue
from dataset.reader.wiki_reader import WikiReader
from persistence.s3_persistence import S3Writer


def process_article():
    sqs = SQSClient(args.sqs_queue)
    s3 = S3Writer(args.s3_bucket)

    while not (shutdown and arq.article_queue.empty()):
        title,source = arq.article_queue.get()
        s3.save("article",title,source)
        sqs.put(S3Writer.clean(title))

def process_redirect():
    while not (shutdown and arq.redirect_queue.empty()):
        line = arq.redirect_queue.get()
        dest_file.write(line[0] + "\t" + line[1] + "\n")



def display():
    while True:
        logger.debug("Queue sizes {0} {1}".format(arq.redirect_queue.qsize(), arq.article_queue.qsize()))
        time.sleep(1)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logging.getLogger(WikiReader.__name__).setLevel(logging.INFO)
    logging.getLogger(WikiReader.__name__).addHandler(ch)

    logger.setLevel(logging.DEBUG)

    shutdown = False

    parser = argparse.ArgumentParser()
    parser.add_argument('--wiki_file', required=True, type=str, help='wikipedia file path to read')
    parser.add_argument('--redirects_file',required=True, type=str, help='redirects file path to write')
    parser.add_argument('--s3_bucket', required=True, type=str, help='s3 bucket to place parsed articles in')
    parser.add_argument('--sqs_queue', required=True, type=str, help="sqs queue for parser instances to read from")
    args = parser.parse_args()

    arq = ArticleReadingQueue()

    wiki = BZ2File(args.wiki_file)
    dest_file = open(os.path.join(args.redirects_file),"w+")


    thread = Thread(target=display, args=())
    thread.daemon = True  # Daemonize thread
    thread.start()  # Start the execution

    for _ in range(15):
        t = Process(target=process_article)
        t.start()


    t2 = Thread(target=process_redirect)
    t2.start()

    reader = WikiReader(lambda ns: ns == 0, arq.enqueue_article, arq.enqueue_redirect)

    try:
        xml.sax.parse(wiki, reader)
    except Exception as e:
        logger.error(e)

    shutdown = True

    while True:
        logger.info("Done")
        time.sleep(10)

