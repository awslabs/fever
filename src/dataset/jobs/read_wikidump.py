import os
import xml

import logging

import time
from bz2 import BZ2File
from threading import Thread

from botocore.exceptions import ClientError
from multiprocessing import Process

from comms.sqs_comms import SQSClient
from dataset.reader.article_queue import ArticleReadingQueue
from dataset.reader.wiki_reader import WikiReader
from persistence.s3_persistence import S3Writer

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

data_path = "./data"
wiki_file = "enwiki-20170601-pages-articles-multistream.xml.bz2"

wiki = BZ2File(os.path.join(data_path,wiki_file))

arq = ArticleReadingQueue()

dest_file = open(os.path.join(data_path,"redirect.txt"),"w+")

def process_article():
    sqs = SQSClient("https://sqs.eu-west-1.amazonaws.com/576699973142/fever-parse-jobs")
    s3 = S3Writer("com.amazon.evi.fever.wiki")

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

