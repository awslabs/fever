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


import re


def is_blank(line):
    pattern = re.compile(r'\s+')
    sentence = re.sub(pattern, '', line)
    return len(sentence.strip())==0


def exact_match(search,text):
    if len(search.strip()) >0 and len (text.strip())>0:
        return len(re.findall('\\b' + re.escape(search.strip()) + '\\b', " "+text+ " ")) > 0
    return False