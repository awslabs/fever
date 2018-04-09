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


import datetime
import hashlib
import boto3
from tqdm import tqdm

from annotation.schema.annotations_rds import *

res = boto3.resource('dynamodb')
table = res.Table("FeverAnnotations")

session = create_session()


md5 = hashlib.md5()
response = table.scan()


def process_scan(items):
    for item in tqdm(items):
        sid = int(item["sentence_id"])
        stext = item["sentence"]
        original = item["original"]
        mutation_type = item["mutation_type"]
        modified = item["mutation"]
        uuid = item["uuid"]
        entity = item["entity"]
        user = item["user"] if "user" in item else "guest"
        version = int(item["version"]) if "version" in item else 3
        created = datetime.datetime.utcfromtimestamp(int(item["date_unix"])) if "date_unix" in item else None
        testing = bool(item["testing"]) if "testing" in item else False
        time_taken_to_annotate = int(item["timer"])

        if session.query(Processed).filter(Processed.id == uuid).count() > 0:
            continue
        else:
            session.add(Processed(id=uuid))
            session.commit()

        if session.query(Entity).filter(Entity.name == entity).count() == 0:
            session.add(Entity(name=entity))

        if session.query(Sentence).filter(Sentence.entity_id == entity).filter(Sentence.text == stext).count() == 0:
            session.add(Sentence(dataset_id=sid, text=stext, entity_id=entity))

        sid = session.query(Sentence).filter(Sentence.entity_id == entity).filter(Sentence.text == stext).first().id

        if session.query(Claim).filter(Claim.text == original).count() == 0:
            session.add(Claim(testing=testing, isReval=False, isOracle=False, sentence_id=sid, text=original,
                              timeTakenToAnnotate=time_taken_to_annotate, created=created,
                              inserted=datetime.datetime.utcnow(), user=user, version=version))
            session.commit()

        if session.query(ClaimMutationType).filter(ClaimMutationType.name == mutation_type).count() == 0:
            session.add(ClaimMutationType(name=mutation_type))

        if session.query(Claim).filter(Claim.uuid == uuid).count() == 0:
            orid = session.query(Claim).filter(Claim.text == original).first().id
            session.add(Claim(testing=testing, text=modified, mutation_type_id=mutation_type, original_claim_id=orid,
                              timeTakenToAnnotate=time_taken_to_annotate, sentence_id=sid, uuid=uuid, created=created,
                              inserted=datetime.datetime.utcnow(), user=user, version=version))

        session.commit()
    print(session.query(Entity).count(), session.query(Sentence).count(), session.query(ClaimMutationType).count(),
          session.query(Claim).count(), session.query(Claim).count())


process_scan(response["Items"])
while 'LastEvaluatedKey' in response:
    response = table.scan(
        ExclusiveStartKey=response['LastEvaluatedKey'],
        ConsistentRead=True
    )
    process_scan(response["Items"])
