import multiprocessing
import logging


class ArticleReadingQueue():
    def __init__(self):
        self.logger = logging.getLogger(ArticleReadingQueue.__name__)
        manager = multiprocessing.Manager()
        self.article_queue = manager.Queue(maxsize=200)
        self.redirect_queue = manager.Queue(maxsize=200)

    def enqueue_article(self, title, source):
        self.logger.debug("Enqueue article {0}".format(title))
        self.article_queue.put((title, source))
        self.logger.debug("Done")

    def enqueue_redirect(self, from_title, to_title):
        self.logger.debug("Enqueue redirect {0}".format(from_title))
        self.redirect_queue.put((from_title, to_title))
        self.logger.debug("Done")
