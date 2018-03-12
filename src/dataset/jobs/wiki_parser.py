import logging
import time

from botocore.exceptions import ClientError

from comms.sqs_comms import SQSClient
from dataset.reader.wiki_parser import WikiParser
from persistence.s3_persistence import S3Writer

import time


if __name__ == "__main__":
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

    sqs = SQSClient("https://sqs.eu-west-1.amazonaws.com/576699973142/fever-parse-jobs")
    s3 = S3Writer("com.amazon.evi.fever.wiki")

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
