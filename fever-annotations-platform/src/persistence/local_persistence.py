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


class LocalQueuePersistence:
    def __init__(self,queue):
        self.logger = logging.getLogger(LocalQueuePersistence.__name__)
        self.logger.info("Local queuing persistence {0}".format(queue))
        self.queue = queue

    def save(self,*args):
        self.logger.debug("Enqueue {0}/{1}".format(args[0],args[1]))
        self.queue.enqueue(args)