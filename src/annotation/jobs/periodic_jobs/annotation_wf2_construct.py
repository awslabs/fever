import datetime
import hashlib

import boto3
from boto3.dynamodb.conditions import Key
from tqdm import tqdm

from annotation.schema.annotations_rds import *

res = boto3.resource('dynamodb')
table = res.Table("FeverAnnotations")

session = create_session()

mintime = (datetime.date.today() - datetime.timedelta(hours=6)).strftime("%s")
print(mintime)
md5 = hashlib.md5()
response = table.query(
    IndexName="version-date_unix-index",
    Select="ALL_ATTRIBUTES",
    KeyConditionExpression=Key("version").eq(5) & Key("date_unix").gt(int(mintime))
)


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
        time_taken_to_annotate = int(item["timer"]) if "timer" in item else None

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
            session.add(Claim(testing=testing, sentence_id=sid, isReval=False, isOracle=False, text=original,
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
    response = table.query(
        ExclusiveStartKey=response['LastEvaluatedKey'],
        IndexName="version-date_unix-index",
        Select="ALL_ATTRIBUTES",
        KeyConditionExpression=Key("version").eq(5) & Key("date_unix").gt(int(mintime))
    )
    process_scan(response["Items"])
