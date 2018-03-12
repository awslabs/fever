import csv
import datetime
from collections import defaultdict

from annotation.schema.annotations_rds import create_session

session = create_session()

master_list = session.execute(
    """
      SELECT
        claim.id                                      AS claim_id,
        concat(verdict_line.page, '---', line_number) AS oracle,
        annotation.user
      FROM claim
        INNER JOIN annotation ON annotation.claim_id = claim.id
        INNER JOIN annotation_verdict ON annotation_verdict.annotation_id = annotation.id
        INNER JOIN verdict_line ON verdict_line.verdict_id = annotation_verdict.id
      WHERE annotation.isOracleMaster = 1 and annotation.isForReportingOnly = 0 
        and annotation.verifiable<2
        and annotation.isTestMode = 0
        and annotation.version = 4
    """).fetchall()


slave_list = session.execute(
    """
    select
      annotation.user,
      annotation.claim_id,
      concat(verdict_line.page, '---', line_number) AS annotator,
      date_format(annotation.created, '%Y-%m-%d') as Date,
      date_format(annotation.created, '%Y-%U') AS Week,
      claimtext
    from annotation
    inner join (
      SELECT
        claim.id                                      AS claimid,
        claim.text                                    AS claimtext
      FROM claim
      INNER JOIN annotation ON annotation.claim_id = claim.id
      WHERE annotation.isOracleMaster = 1 
      and annotation.isForReportingOnly = 0 
        and annotation.verifiable<2
        and annotation.isTestMode = 0
        and annotation.version = 4
      group by claim.id
    ) as t on t.claimid = annotation.claim_id
    INNER JOIN annotation_verdict ON annotation_verdict.annotation_id = annotation.id
    INNER JOIN verdict_line ON verdict_line.verdict_id = annotation_verdict.id
    where annotation.isOracleMaster = 0 
    and annotation.isForReportingOnly = 0
    and annotation.verifiable<2
    and annotation.isTestMode = 0
    and annotation.version = 4
    """).fetchall()

master_evidence_all = defaultdict(set)
slave_evidence_all = defaultdict(set)
slave_evidence_texts = {}

master_evidence = defaultdict(lambda: defaultdict(set))
slave_evidence = defaultdict(lambda: defaultdict(set))

slave_day_evidence = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
slave_day_evidence_all = defaultdict(lambda: defaultdict(set))

slave_week_evidence = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
slave_week_evidence_all = defaultdict(lambda: defaultdict(set))

for item in master_list:
    master_evidence_all[item['claim_id']].add(item['oracle'])
    master_evidence[item['user']][item['claim_id']].add(item['oracle'])

for item in slave_list:
    slave_evidence_all[item['claim_id']].add(item['annotator'])
    slave_evidence_texts[item['claim_id']] = item['claimtext']
    slave_day_evidence_all[item['Date']][item['claim_id']].add(item['annotator'])
    slave_week_evidence_all[item['Week']][item['claim_id']].add(item['annotator'])

    slave_evidence[item['user']][item['claim_id']].add(item['annotator'])
    slave_day_evidence[item['user']][item['Date']][item['claim_id']].add(item['annotator'])
    slave_week_evidence[item['user']][item['Week']][item['claim_id']].add(item['annotator'])


users = set()
users.update(master_evidence.keys())
users.update(slave_evidence.keys())


def prec_rec(relevant, retrieved):
    precision = len(relevant.intersection(retrieved)) / len(retrieved) if len(retrieved) > 0 else 1
    recall = len(relevant.intersection(retrieved)) / len(relevant) if len(relevant) > 0 else 1
    return precision, recall


def evidence_missed_by_all(dataset):
    report_html = ""
    missed_claims = defaultdict(list)
    for claim in dataset:
        relevant = master_evidence_all[claim]
        retrieved = slave_evidence_all[claim]
        diff = relevant.difference(retrieved)
        missed_claims[claim].extend(list(diff))
    missed_sorted_keys = sorted(missed_claims.keys(), key=lambda k: len(missed_claims[k]), reverse=True)
    for key in missed_sorted_keys:
        if len(missed_claims[key]) == 0:
            continue
        claim_link = 'https://fever-annotate.corp.amazon.com/#!/label-claims/%d' % key
        report_html += '<a href=%s>%s</a>\n' % (claim_link, slave_evidence_texts[key])
        for missed_claim in sorted(missed_claims[key]):
            report_html += '<li>%s</li>\n' % missed_claim
        report_html += '<br/>'
    return report_html


def evidence_missed_by_user(dataset, user_set):
    report_html = ''
    for user in user_set:
        total_missed = 0
        missed_claims = defaultdict(list)
        for claim in dataset:
            relevant = master_evidence_all[claim]
            retrieved = slave_evidence[user][claim]
            diff = relevant.difference(retrieved)
            missed_claims[claim].extend(list(diff))
            total_missed += len(diff)
        missed_sorted_keys = sorted(missed_claims.keys(), key=lambda k: len(missed_claims[k]), reverse=True)

        report_html += '<a href="#" onclick="show_hide(\'%s\')">%s (%d claims)</a>\n' % (user, user, total_missed)
        report_html += '<div id="' + user + '" style="display: none; margin-left: 2%;">'
        for key in missed_sorted_keys:
            if len(missed_claims[key]) == 0:
                continue
            claim_link = 'https://fever-annotate.corp.amazon.com/#!/label-claims/%d' % key
            report_html += '<a href=%s>%s</a>\n' % (claim_link, slave_evidence_texts[key])
            for missed_claim in sorted(missed_claims[key]):
                report_html += '<li>%s</li>\n' % missed_claim
            report_html += '<br/>\n'
        report_html += '</div>\n<br/>\n'
    return report_html


def macro_pr(user, dataset):
    p = []
    r = []
    for claim in dataset:
        relevant = master_evidence_all[claim]
        retrieved = slave_evidence[user][claim]

        precision, recall = prec_rec(relevant, retrieved)
        p.append(precision)
        r.append(recall)

    return sum(p)/len(p) if len(p) > 0 else 0, sum(r)/len(r) if len(r) > 0 else 0


def micro_pr_all(dataset):
    p = []
    r = []
    for claim in dataset:
        relevant = master_evidence_all[claim]
        retrieved = slave_evidence_all[claim]

        precision, recall = prec_rec(relevant, retrieved)
        p.append(precision)
        r.append(recall)

    return sum(p)/len(p) if len(p) > 0 else 0, sum(r)/len(r) if len(r) > 0 else 0


def macro_pr_all_by_user(dataset, user_set):
    p = []
    r = []
    for user in user_set:
        for claim in dataset:
            if claim not in slave_evidence[user]:
                continue

            relevant = master_evidence_all[claim]
            retrieved = slave_evidence[user][claim]

            precision, recall = prec_rec(relevant, retrieved)
            p.append(precision)
            r.append(recall)

    return sum(p)/len(p) if len(p) > 0 else "-", sum(r)/len(r) if len(r) > 0 else "-"


def macro_pr_time_by_user(dataset, user_set, time):
    p = []
    r = []
    for user in user_set:
        for claim in dataset[user][time]:
            relevant = master_evidence_all[claim]
            retrieved = dataset[user][time][claim]

            precision, recall = prec_rec(relevant, retrieved)
            p.append(precision)
            r.append(recall)

    return sum(p)/len(p) if len(p) > 0 else "-", sum(r)/len(r) if len(r) > 0 else "-"


p_by_user = defaultdict(float)
r_by_user = defaultdict(float)

p_by_day = defaultdict(float)
r_by_day = defaultdict(float)

p_by_week = defaultdict(float)
r_by_week = defaultdict(float)

p_by_day_by_user = defaultdict(lambda: defaultdict(float))
r_by_day_by_user = defaultdict(lambda: defaultdict(float))

p_by_week_by_user = defaultdict(lambda: defaultdict(float))
r_by_week_by_user = defaultdict(lambda: defaultdict(float))


rracc = 0
ppacc = 0

for u in users:
    up, ur = macro_pr(u, slave_evidence[u])
    p_by_user[u] = up
    r_by_user[u] = ur

    for d in slave_day_evidence[u].keys():
        upd, urd = macro_pr(u, slave_day_evidence[u][d])

        p_by_day_by_user[d][u] = upd
        r_by_day_by_user[d][u] = urd

    for d in slave_week_evidence[u].keys():
        upw, urw = macro_pr(u, slave_week_evidence[u][d])

        p_by_week_by_user[d][u] = upw
        r_by_week_by_user[d][u] = urw


pp, rr = macro_pr_all_by_user(slave_evidence_all, users)
print(pp, rr)

for d in slave_day_evidence_all.keys():
    p_by_day[d], r_by_day[d] = macro_pr_time_by_user(slave_day_evidence, users, d)

for d in slave_week_evidence_all.keys():
    p_by_week[d], r_by_week[d] = macro_pr_time_by_user(slave_week_evidence, users, d)


def save_csv(filename, header, report):
    with open("data/reports/"+filename+".csv", "w+") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for line in report:
            writer.writerow(line)


def save_html(filename, report):
    with open('data/reports/'+filename+'.html', 'w', encoding='utf-8') as f:
        f.write('<!DOCTYPE html>\n<html>\n')
        f.write('<html>\n<head>\n<script>\n'
                'function show_hide(id) {\nvar el = document.getElementById(id);\n'
                'if( el && el.style.display == "none")\nel.style.display = "block";\n'
                'else \nel.style.display = "none";\n}\n</script>\n'
                '</head>\n')
        f.write('<body style="margin-left: 2%;">\n')
        f.write(report)
        f.write('\n</body>')
        f.write('\n</html>')


users = list(users)

# Manually exclude users from the reports (in case they are not currently active)
# NB: This is a duplicate of the list in annotation_reporting_service.py (line 23)
exclude_list = ['esservis', 'flynna', 'guest', 'hjingnin',
                'hokathle', 'mpearsal', 'stefom', 'chrchrs']

users = [user for user in users if user not in exclude_list]


def daily_report(title, data, user_set):
    ds = data
    report = []
    for key in sorted(ds.keys()):
        report_line = [key]
        for user in user_set:
            report_line.append(ds[key][user])
        report.append(report_line)

    header = [title]
    header.extend(user_set)
    return header, report


def user_report(title, data, user_set):
    report = []

    for user in sorted(user_set):
        report_line = [user, data[user]]
        report.append(report_line)

    header = ["User", title]
    return header, report


def date_report(title, data, days):
    report = []

    for day in sorted(days):
        report_line = [day, data[day]]
        report.append(report_line)

    header = ["Date", title]
    return header, report


save_csv("p_user_by_day", *daily_report("Date", p_by_day_by_user, users))
save_csv("r_user_by_day", *daily_report("Date", r_by_day_by_user, users))
save_csv("p_user_by_week", *daily_report("Week", p_by_week_by_user, users))
save_csv("r_user_by_week", *daily_report("Week", r_by_week_by_user, users))

save_csv("p_by_user", *user_report("Precision", p_by_user, users))
save_csv("r_by_user", *user_report("Recall", r_by_user, users))


save_csv("p_by_day", *date_report("Precision", p_by_day, p_by_day.keys()))
save_csv("r_by_day", *date_report("Recall", r_by_day, r_by_day.keys()))

save_csv("p_by_week", *date_report("Precision", p_by_week, p_by_week.keys()))
save_csv("r_by_week", *date_report("Recall", r_by_week, r_by_week.keys()))

save_csv("pr", ["Precision", "Recall"], [[pp, rr]])

save_html("missed_by_all", evidence_missed_by_all(slave_evidence_all))
save_html("missed_by_user", evidence_missed_by_user(slave_evidence_all, users))

today = datetime.datetime.utcnow()
last_week = today + datetime.timedelta(weeks=-1)

start_date = datetime.datetime.strptime("2017-09-01", "%Y-%m-%d")
qdate = start_date

labels1 = []

labels2 = []
pdata = []
rdata = []
pddata = []
rddata = []


def get_date_week(date_obj):
    return datetime.datetime.strptime(date_obj.strftime("%Y-%U-1"), "%Y-%U-%w")


while get_date_week(qdate) <= get_date_week(today):
    labels1.append(qdate.strftime("%Y-%U"))
    pdata.append(p_by_week[qdate.strftime("%Y-%U")])
    rdata.append(r_by_week[qdate.strftime("%Y-%U")])
    qdate = qdate+datetime.timedelta(weeks=1)

qdate = start_date


def get_date_day(date_obj):
    return datetime.datetime.strptime(date_obj.strftime("%Y-%m-%d"), "%Y-%m-%d")


while get_date_day(qdate) <= get_date_day(today):
    labels2.append(qdate.strftime("%Y-%m-%d"))
    print(qdate.strftime("%Y-%m-%d"))
    pddata.append(p_by_day[qdate.strftime("%Y-%m-%d")])
    rddata.append(r_by_day[qdate.strftime("%Y-%m-%d")])
    qdate = qdate+datetime.timedelta(days=1)


sdata = [pdata, rdata]
oracle_report = {
    "p": pp,
    "r": rr,
    "p_tw": p_by_week[today.strftime("%Y-%U")],
    "r_tw": r_by_week[today.strftime("%Y-%U")],
    "p_lw": p_by_week[last_week.strftime("%Y-%U")],
    "r_lw": r_by_week[last_week.strftime("%Y-%U")],
    "chart": {
        "data": sdata,
        "series": ["Precision (Weekly)", "Recall (Weekly)"],
        "labels": labels1
    },
    "chart2": {
        "data": [pddata, rddata],
        "series": ["Precision (Daily)", "Recall (Daily)"],
        "labels": labels2
    }

}

import json

json.dump(oracle_report, open("data/oracle.json", "w"))
