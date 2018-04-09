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