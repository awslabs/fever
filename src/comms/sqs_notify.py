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
