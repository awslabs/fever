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


from datetime import timedelta, datetime
from sqlalchemy import func
from annotation.schema.annotations_rds import create_session, Annotation, AnnotationAssignment

session = create_session()


"""
select *,  max(annotation_assignment.expires) as maxexp from claim
left join annotation on annotation.claim_id = claim.id
left join annotation_assignment on annotation_assignment.claim_id = claim.id
where claim.isReval = 0
      and claim.isOracle = 0
      and annotation.id IS NULL
group by claim.id
HAVING maxexp < CURRENT_TIMESTAMP or maxexp is NULL
limit 1

"""


class SimpleClaim(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def get_next_regular(session, username):
    next = session.execute("""select cl.*, sentence.entity_id as ent from
    (SELECT claim.id as id, claim.sentence_id as sent,claim.text as text,  max(annotation_assignment.expires) as maxexp from claim
        left join annotation on annotation.claim_id = claim.id 
              and annotation.isForReportingOnly = 0
              and annotation.isTestMode = 0
        left join annotation_assignment on annotation_assignment.claim_id = claim.id
        where claim.isReval = 0
              and claim.isOracle = 0
              and annotation.id IS NULL
              and claim.testing = 0
        group by claim.id
        HAVING maxexp < CURRENT_TIMESTAMP or maxexp is NULL
        limit 1) as cl
    inner join sentence on cl.sent = sentence.id
        """).first()

    if next is None:
        return next
    return SimpleClaim(id=next['id'], sentence=SimpleClaim(entity_id=next["ent"]), text=next["text"],
                       sentence_id=next["sent"])


def get_oracle_assignment(session, username):
    next = session.execute("""select cl.*,sentence.entity_id as ent from
    (SELECT claim.id as id, claim.sentence_id as sent,claim.text as text,  max(annotation_assignment.expires) as maxexp from claim
        left join annotation on annotation.claim_id = claim.id and annotation.user = :username 
              and annotation.isForReportingOnly = 0
              and annotation.isTestMode = 0

        left join annotation_assignment on annotation_assignment.claim_id = claim.id
        where claim.isOracle = 1 and annotation.id IS NULL and claim.testing = 0
        group by claim.id
        HAVING maxexp < CURRENT_TIMESTAMP or maxexp is NULL
        limit 1) as cl
    inner join sentence on cl.sent = sentence.id
        """, {"username": username}).first()

    if next is None:
        return next
    return SimpleClaim(id=next['id'], sentence=SimpleClaim(entity_id=next["ent"]), text=next["text"],
                       sentence_id=next["sent"])


def get_oracle_assignment_master(session, username):
    next = session.execute("""select cl.*,sentence.entity_id as ent from
    (SELECT claim.id as id, claim.sentence_id as sent,claim.text as text,  max(annotation_assignment.expires) as maxexp from claim
        left join annotation on annotation.claim_id = claim.id
              and annotation.isForReportingOnly = 0
              and annotation.isTestMode = 0
              and annotation.isOracleMaster = 1
        left join annotation_assignment on annotation_assignment.claim_id = claim.id
        where claim.isOracle = 1 and annotation.id IS NULL 
              and claim.testing = 0
        group by claim.id
        HAVING maxexp < CURRENT_TIMESTAMP or maxexp is NULL
        limit 1) as cl
    inner join sentence on cl.sent = sentence.id
        """, {"username": username}).first()

    if next is None:
        return next
    return SimpleClaim(id=next['id'], sentence=SimpleClaim(entity_id=next["ent"]), text=next["text"],
                       sentence_id=next["sent"])


def get_reval_assignment(session, username):
    next = session.execute("""
    SELECT
      cl.*,
      sentence.entity_id AS ent
    FROM (
           SELECT
             claim.id                  AS id,
             claim.sentence_id         AS sent,
             claim.text                AS text,
             maxexp,
             count(all_annotations.id) AS cntall
           FROM claim
             LEFT JOIN annotation AS all_annotations ON all_annotations.claim_id = claim.id
                                                        AND all_annotations.isForReportingOnly = 0
                                                        AND all_annotations.isTestMode = 0
                                                        AND NOT exists(SELECT 1 
                                                                       FROM annotation 
                                                                       WHERE annotation.user = :username AND 
                                                                             annotation.claim_id = claim.id)
             LEFT JOIN (SELECT
                          claim_id,
                          max(annotation_assignment.expires) AS maxexp
                        FROM annotation_assignment
                        WHERE NOT exists(SELECT 1
                                         FROM annotation
                                         WHERE annotation.user = :username AND
                                               annotation.claim_id = annotation_assignment.claim_id)
                        GROUP BY claim_id) AS assignment ON assignment.claim_id = claim.id
           WHERE claim.isReval = 1
                 AND claim.testing = 0
           GROUP BY claim.id
           HAVING cntall < 5 AND maxexp < CURRENT_TIMESTAMP
         LIMIT 1) AS cl
      INNER JOIN sentence ON cl.sent = sentence.id
    """, {"username": username}).first()

    if next is None:
        return next
    return SimpleClaim(id=next['id'], sentence=SimpleClaim(entity_id=next["ent"]), text=next["text"],
                       sentence_id=next["sent"])


    # Get next claim.
    # Get oracle
    # Get reval


def get_next_assignment(session, username, oracleAnnotatorMode=False, testMode=False):
    user_done_count = session.query(Annotation) \
        .filter(~Annotation.isTestMode) \
        .filter(Annotation.user == username) \
        .filter(~Annotation.isDiscounted) \
        .filter(~Annotation.isForReportingOnly) \
        .count()

    if oracleAnnotatorMode:
        next = get_oracle_assignment_master(session, username)
        print("Getting oracle master")
    elif user_done_count % 90 == 89 and not testMode:
        # Do oracle every 90
        next = get_oracle_assignment(session, username)
        print("Getting oracle")
    elif user_done_count % 10 == 9 and not testMode:
        # Reval every 10 - except oracle round
        print("Getting reval")
        next = get_reval_assignment(session, username)
    else:
        next = get_next_regular(session, username)

    if next is None and not oracleAnnotatorMode:
        next = get_next_regular(session, username)
        if next is None:
            # If there are no more regular annotations left, go for the reval
            print("Regular next not found -- Getting reval")
            next = get_reval_assignment(session, username)
        if next is None:
            # If there are no more reval, go for oracle
            print("Regular next not found -- Getting oracle")
            next = get_oracle_assignment(session, username)

    ret = {"sentence_id": next.sentence_id, "claim_id": next.id, "text": next.text, "entity": next.sentence.entity_id}

    expires = datetime.utcnow() + timedelta(hours=4)
    session.add(AnnotationAssignment(user=username, sentence_id=next.sentence_id, claim_id=next.id, expires=expires,
                                     created=func.now()))
    session.commit()

    return ret


if __name__ == "__main__":
    print(get_next_assignment(session, "jim").text)

