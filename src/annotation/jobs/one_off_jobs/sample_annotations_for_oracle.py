import math

from annotation.schema.annotations_rds import create_session

session = create_session()


result = session.execute("""
select sum(isOracle) as oracount, sum(isReval) as revalcount, count(*) as total from claim
where testing = 0
""").first()

oracle_target = math.ceil(result['total']*.01)
reval_target = math.ceil(result['total']*.1)

oracle_remaining = max(0,oracle_target-result['oracount'])
reval_remaining = max(0,reval_target-result['revalcount'])

print(oracle_remaining,reval_remaining)



update = session.execute("""
UPDATE claim
INNER JOIN (
    SELECT claim.id FROM claim
    LEFT JOIN annotation on annotation.claim_id = claim.id
    WHERE annotation.id is null and claim.isOracle = 0 and claim.isReval = 0
    ORDER BY RAND() LIMIT :toupdate
) as t on t.id = claim.id
SET isOracle = 1
""",{"toupdate":oracle_remaining})

update = session.execute("""
UPDATE claim
INNER JOIN (
    SELECT claim.id FROM claim
    LEFT JOIN annotation on annotation.claim_id = claim.id
    WHERE annotation.id is null and claim.isOracle = 0 and claim.isReval = 0
    ORDER BY RAND() LIMIT :toupdate
) as t on t.id = claim.id
SET isReval = 1
""",{"toupdate":reval_remaining})

result = session.execute("""
select sum(isOracle) as oracount, sum(isReval) as revalcount, count(*) as total from claim
where testing = 0
""").first()

oracle_remaining = max(0,oracle_target-result['oracount'])
reval_remaining = max(0,reval_target-result['revalcount'])

print(oracle_remaining,reval_remaining)

session.commit()
session.close()