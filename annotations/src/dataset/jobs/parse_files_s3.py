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


import os
from botocore.exceptions import ClientError
from dataset.reader.wiki_parser import WikiParser
from persistence.s3_persistence import S3Writer



s3 = S3Writer(os.getenv("S3_BUCKET"))
parser = WikiParser(s3)


with open("data/pages.txt") as f:
    files = f.readlines()

files = [file.replace(" ","_").strip() for file in files]

for file in files:
    try:
        obj = s3.read("article/"+file)
        text = bytes.decode(obj['Body'].read())

        parser.article_callback(file,text)
    except ClientError:
        print("CE" + file)
