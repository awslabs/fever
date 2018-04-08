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
