from collections import defaultdict

from statsmodels.stats.inter_rater import fleiss_kappa

from annotation.schema.annotations_rds import create_session

session = create_session()

claims = session.execute(
    """
select claim.id,
annotation.user,
annotation.verifiable,
date_format(annotation.created, '%Y-%m-%d') as Date,
date_format(annotation.created, '%Y-%U') AS Week
from annotation
inner join claim on claim.id = annotation.claim_id
where claim.isReval = 1
order by Date asc
    """).fetchall()


claims_dict = defaultdict(list)


def row_ct(row):
    rowct = []
    for i in range(5):
        rowct.append(row.count(i))

    return rowct


for claim in claims:
    claims_dict[claim['id']].append(claim['verifiable'])

print(claims_dict)
print([len(claims_dict[key]) for key in claims_dict])

fkt1 = [row_ct(claims_dict[key]) for key in claims_dict if len(claims_dict[key]) == 5]
if len(fkt1) == 0:
    print('No claims with 5 annotations; cannot check Fleiss Kappa.')
else:
    print(fleiss_kappa(fkt1))
