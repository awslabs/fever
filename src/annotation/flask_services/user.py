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


#For user authentication
class ForwardedUserMiddleware(object):
    def __init__(self, application):
        self.app = application

    def __call__(self, environ, start_response):
        user = environ.pop('HTTP_X_FORWARDED_USER', None)
        if user is not None:
            environ['REMOTE_USER'] = user.split("@")[0]

        return self.app(environ, start_response)