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
import csv
import datetime
import json
from decimal import Decimal

from annotation.schema.annotations_rds import create_session

session = create_session()


users = session.execute("""
SELECT user
FROM claim
GROUP BY user
UNION
SELECT user
FROM annotation
GROUP BY user;
""")

# Manually exclude users from the reports (in case they are not currently active)
# NB: This is a duplicate of the list in oracle_eval.py (line 278)
exclude_list = ['esservis', 'flynna', 'guest', 'hjingnin',
                'hokathle', 'mpearsal', 'stefom', 'chrchrs']

user_list = [user[0] for user in users if user[0] not in exclude_list]


def get_user_cube():
    return ",\n".join(["sum(case user when '{0}' then total else 0 end) as '{0}'".format(user) for user in user_list])


def get_stats(name, testing):
    testing = {"testing": testing}
    weekly_live_breakdown = session.execute("""
    SELECT
      date_format(created, '%Y-%U') AS week_number,
      str_to_date(concat(date_format(created, '%Y-%U'),'-',0),'%Y-%U-%w') as week_commencing,
      count(*) as total
    FROM claim
    WHERE testing = :testing
    GROUP BY week_number
    ORDER BY week_number;
                    """, testing)

    daily_live_breakdown = session.execute("""
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      count(*) as total
    FROM claim
    WHERE testing = :testing
    GROUP BY date
    ORDER BY date;
                    """, testing)

    user_cube = get_user_cube()

    weekly_user_live_breakdown = session.execute("""
    select week_number,
      week_commencing,
      {0}
    from (
    SELECT
      date_format(created, '%Y-%U') AS week_number,
      str_to_date(concat(date_format(created, '%Y-%U'),'-',0),'%Y-%U-%w') as week_commencing,
      user,
      count(*) as total
    FROM claim
    WHERE testing = :testing
    GROUP BY week_number,user
    ORDER BY week_number) as a
    group by week_number
    ORDER BY week_number;
    """.format(user_cube), testing)

    weekly_time_user_live_breakdown = session.execute("""
    select week_number,
      week_commencing,
      {0}
    from (
    SELECT
      date_format(created, '%Y-%U') AS week_number,
      str_to_date(concat(date_format(created, '%Y-%U'),'-',0),'%Y-%U-%w') as week_commencing,
      user,
      sum(timeTakenToAnnotate) as total
    FROM claim
    WHERE testing = :testing
    GROUP BY week_number,user
    ORDER BY week_number) as a
    group by week_number
    ORDER BY week_number;
    """.format(user_cube), testing)

    daily_user_live_breakdown = session.execute("""
    select 
      Date,
      {0}
    from (
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      user,
      count(*) as total
    FROM claim
    WHERE testing = :testing
    GROUP BY Date,user
    ORDER BY Date) as a
    group by Date
    ORDER BY Date;
    """.format(user_cube), testing)

    daily_time_user_live_breakdown = session.execute("""
    select 
      Date,
      {0}
    from (
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      user,
      sum(timeTakenToAnnotate) as total
    FROM claim
    WHERE testing = :testing
    GROUP BY Date,user
    ORDER BY Date) as a
    group by Date
    ORDER BY Date;
    """.format(user_cube), testing)

    lwk, lw = coerce_all(weekly_user_live_breakdown)
    ldk, ld = coerce_all(daily_user_live_breakdown)

    lwtk, ltw = coerce_all(weekly_time_user_live_breakdown, time=True)
    ldtk, ltd = coerce_all(daily_time_user_live_breakdown, time=True)

    dbk, db = coerce_all(daily_live_breakdown)
    wbk, wb = coerce_all(weekly_live_breakdown)

    save_csv(name+"_weekly", lwk, lw)
    save_csv(name+"_time_weekly", lwtk, ltw)
    save_csv(name+"_daily", ldk, ld)
    save_csv(name+"_time_daily", ldtk, ltd)
    save_csv(name+"_daily_totals", dbk, db)
    save_csv(name+"_weekly_totals", wbk, wb)


def get_stats_wf2(name, testing):
    testing = {"testing": testing}
    weekly_live_breakdown = session.execute("""
    SELECT
      date_format(created, '%Y-%U') AS week_number,
      str_to_date(concat(date_format(created, '%Y-%U'),'-',0),'%Y-%U-%w') as week_commencing,
      count(*) as total
    FROM annotation
    WHERE isTestMode = :testing
    GROUP BY week_number
    ORDER BY week_number;
                    """, testing)

    daily_live_breakdown = session.execute("""
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      count(*) as total
    FROM annotation
    WHERE isTestMode = :testing
    GROUP BY date
    ORDER BY date;
                    """, testing)

    user_cube = get_user_cube()

    weekly_user_live_breakdown = session.execute("""
    select week_number,
      week_commencing,
      {0}
    from (
    SELECT
      date_format(created, '%Y-%U') AS week_number,
      str_to_date(concat(date_format(created, '%Y-%U'),'-',0),'%Y-%U-%w') as week_commencing,
      user,
      count(*) as total
    FROM annotation
    WHERE isTestMode = :testing
    GROUP BY week_number,user
    ORDER BY week_number) as a
    group by week_number
    ORDER BY week_number;
    """.format(user_cube), testing)

    weekly_time_user_live_breakdown = session.execute("""
    select week_number,
      week_commencing,
      {0}
    from (
    SELECT
      date_format(created, '%Y-%U') AS week_number,
      str_to_date(concat(date_format(created, '%Y-%U'),'-',0),'%Y-%U-%w') as week_commencing,
      user,
      sum(timeTakenToAnnotate) as total
    FROM annotation
    WHERE isTestMode = :testing
    GROUP BY week_number,user
    ORDER BY week_number) as a
    group by week_number
    ORDER BY week_number;
    """.format(user_cube), testing)

    daily_user_live_breakdown = session.execute("""
    select 
      Date,
      {0}
    from (
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      user,
      count(*) as total
    FROM annotation
    WHERE isTestMode = :testing
    GROUP BY Date,user
    ORDER BY Date) as a
    group by Date
    ORDER BY Date;
    """.format(user_cube), testing)

    daily_time_user_live_breakdown = session.execute("""
    select 
      Date,
      {0}
    from (
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      user,
      sum(timeTakenToAnnotate) as total
    FROM annotation
    WHERE isTestMode = :testing
    GROUP BY Date,user
    ORDER BY Date) as a
    group by Date
    ORDER BY Date;
    """.format(user_cube), testing)

    flagged_claims = session.execute("""
    SELECT claim_id, user
    FROM annotation
    WHERE isTestMode = :testing
    AND annotation.verifiable < 0
    """, testing)

    save_html(name+"_flagged_claims", flagged_claims)

    lwk, lw = coerce_all(weekly_user_live_breakdown)
    ldk, ld = coerce_all(daily_user_live_breakdown)

    lwtk, ltw = coerce_all(weekly_time_user_live_breakdown, time=True)
    ldtk, ltd = coerce_all(daily_time_user_live_breakdown, time=True)

    dbk, db = coerce_all(daily_live_breakdown)
    wbk, wb = coerce_all(weekly_live_breakdown)

    save_csv(name+"_weekly_wf2", lwk, lw)
    save_csv(name+"_time_weekly_wf2", lwtk, ltw)
    save_csv(name+"_daily_wf2", ldk, ld)
    save_csv(name+"_time_daily_wf2", ldtk, ltd)
    save_csv(name+"_daily_totals_wf2", dbk, db)
    save_csv(name+"_weekly_totals_wf2", wbk, wb)


def coerce(line, is_time_spent):
    newline = []

    for item in line:
        if type(item) == Decimal:
            if is_time_spent:
                newline.append(convert(item, add_days=False, to_hours_dec=True))
            else:
                newline.append(str(item))
        elif type(item) == datetime.date:
            newline.append(str(item))
        else:
            newline.append(item)

    return newline


def coerce_all(records, time=False):
    all_lines = []
    for line in records:
        all_lines.append(coerce(line, time))
    return records.keys(), all_lines


def save_csv(filename, header, report_lines):
    if not os.path.exists('data/reports'):
        os.mkdir('data/reports')

    with open("data/reports/"+filename+".csv", "w+") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for line in report_lines:
            writer.writerow(line)


def save_html(filename, flagged_claims):
    with open('data/reports/'+filename+'.html', 'w', encoding='utf-8') as f:
        f.write('<!DOCTYPE html>\n<html>\n')
        f.write('<body style="margin-left: 2%;">\n')
        for claim in flagged_claims:
            claim_link = 'https://fever-annotate.corp.amazon.com/#!/label-claims/%d' % claim[0]
            user = claim[1]
            f.write('%s: <a href=%s>%s</a><br/>\n' % (user, claim_link, claim_link))
        f.write('\n</body>')
        f.write('\n</html>')


def done_today(testing):
    testing = {"testing": testing}
    qry = """
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      count(*) as total
    FROM claim
    WHERE testing = :testing
    AND date_format(created, '%Y-%m-%d') = date_format(NOW(), '%Y-%m-%d')
    GROUP BY date
    order by Date
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        return res.first()[1]


def convert(sec_dec, add_days=True, to_hours_dec=False):
    if not sec_dec:
        return 'N/A'
    if sec_dec == 0:
        return '0'
    sec = int(sec_dec)
    if to_hours_dec:
        return "%.2f" % (float(sec)/60/60)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if add_days:
        time_spent_str = "%d days; %d hours, %d minutes" % (d, h, m)
    else:
        time_spent_str = "%d hours, %d minutes" % (h, m)
    return time_spent_str


def time_today(testing):
    testing = {"testing": testing}
    qry = """
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      sum(timeTakenToAnnotate) as total
    FROM claim
    WHERE testing = :testing
    AND date_format(created, '%Y-%m-%d') = date_format(NOW(), '%Y-%m-%d')
    GROUP BY date
    order by Date
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        # Return time spent in day,hours,minutes
        seconds_spent = res.first()[1]
        return convert(seconds_spent)


def done_week(testing, offset):
    wk = datetime.datetime.utcnow() + datetime.timedelta(weeks=offset)
    print(wk.strftime("%Y-%U"))
    testing = {"testing": testing, "dwk": wk.strftime("%Y-%U")}
    qry = """
    SELECT
      count(*) as total
    FROM claim
    WHERE testing = :testing
    AND date_format(created, '%Y-%U') = :dwk
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        return res.first()[0]


def time_week(testing, offset):
    wk = datetime.datetime.utcnow() + datetime.timedelta(weeks=offset)
    print(wk.strftime("%Y-%U"))
    testing = {"testing": testing, "dwk": wk.strftime("%Y-%U")}
    qry = """
    SELECT
      sum(timeTakenToAnnotate) as total
    FROM claim
    WHERE testing = :testing
    AND date_format(created, '%Y-%U') = :dwk
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        # Return time spent in hours,minutes,seconds
        seconds_spent = res.first()[0]
        return convert(seconds_spent)


def done(testing):
    testing = {"testing": testing}
    qry = """
    SELECT
      count(*) as total
    FROM claim
    WHERE testing = :testing
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        return res.first()[0]


def done_today_wf2(testing):
    testing = {"testing": testing}
    qry = """
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      count(*) as total
    FROM annotation
    WHERE isTestMode = :testing
    AND date_format(created, '%Y-%m-%d') = date_format(NOW(), '%Y-%m-%d')
    GROUP BY date
    order by Date
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        return res.first()[1]


def total_left_reval_wf2():
    qry = """
    SELECT count(done)
    FROM (SELECT count(annotation.id) AS done
      FROM claim
        LEFT JOIN annotation ON annotation.claim_id = claim.id
                                AND annotation.isForReportingOnly = 0
                                AND annotation.isTestMode = 0
      WHERE claim.isReval = 1
            AND claim.isOracle = 0
            AND claim.testing = 0
      GROUP BY claim.id
      HAVING done = :num) AS cad;
    """
    num4_left = session.execute(qry, {"num": 1}).first()[0] * 4
    num3_left = session.execute(qry, {"num": 2}).first()[0] * 3
    num2_left = session.execute(qry, {"num": 3}).first()[0] * 2
    num1_left = session.execute(qry, {"num": 4}).first()[0]

    qry = """
    SELECT count(done)
    FROM (SELECT count(annotation.id) AS done
      FROM claim
        LEFT JOIN annotation ON annotation.claim_id = claim.id
                                AND annotation.isForReportingOnly = 0
                                AND annotation.isTestMode = 0
      WHERE claim.isReval = 0
            AND claim.isOracle = 0
            AND claim.testing = 0
      GROUP BY claim.id
      HAVING done = :num) AS cad;
    """
    num_noreval_left = session.execute(qry, {"num": 0}).first()[0]
    return num_noreval_left + num1_left + num2_left + num3_left + num4_left


def time_today_wf2(testing):
    testing = {"testing": testing}
    qry = """
    SELECT
      date_format(created, '%Y-%m-%d') as Date,
      sum(timeTakenToAnnotate) as total
    FROM annotation
    WHERE isTestMode = :testing
    AND date_format(created, '%Y-%m-%d') = date_format(NOW(), '%Y-%m-%d')
    GROUP BY date
    order by Date
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        # Return time spent in hours,minutes,seconds
        seconds_spent = res.first()[1]
        return convert(seconds_spent)


def done_week_wf2(testing, offset):
    wk = datetime.datetime.utcnow() + datetime.timedelta(weeks=offset)
    print(wk.strftime("%Y-%U"))
    testing = {"testing": testing, "dwk": wk.strftime("%Y-%U")}
    qry = """
    SELECT
      count(*) as total
    FROM annotation
    WHERE isTestMode = :testing
    AND date_format(created, '%Y-%U') = :dwk
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        return res.first()[0]


def time_week_wf2(testing, offset):
    wk = datetime.datetime.utcnow() + datetime.timedelta(weeks=offset)
    print(wk.strftime("%Y-%U"))
    testing = {"testing": testing, "dwk": wk.strftime("%Y-%U")}
    qry = """
    SELECT
      sum(timeTakenToAnnotate) as total
    FROM annotation
    WHERE isTestMode = :testing
    AND date_format(created, '%Y-%U') = :dwk
    """

    res = session.execute(qry, testing)
    if res.rowcount == 0:
        return 0
    else:
        # Return time spent in hours,minutes,seconds
        seconds_spent = res.first()[0]
        return convert(seconds_spent)


def done_wf2(testing):
    testing = {"testing": testing}
    qry = """
    SELECT
      count(*) as total
    FROM annotation
    WHERE isTestMode = :testing
    """

    res = session.execute(qry, testing)

    if res.rowcount == 0:
        return 0
    else:
        return res.first()[0]


get_stats("live", 0)
get_stats("sandbox", 1)

get_stats_wf2("live", 0)
get_stats_wf2("sandbox", 1)


report = {"live_count": done(0),
          "sandbox_count": done(1),
          "last_run": str(datetime.datetime.now()),
          "done_today": done_today(0),
          "time_today": time_today(0),
          "done_this_week": done_week(0, 0),
          "time_this_week": time_week(0, 0),
          "done_last_week": done_week(0, -1),
          "time_last_week": time_week(0, -1),
          }


json.dump(report, open("data/state.json", "w+"))


report = {"live_count": done_wf2(0),
          "sandbox_count": done_wf2(1),
          "last_run": str(datetime.datetime.now()),
          "done_today": done_today_wf2(0),
          "time_today": time_today_wf2(0),
          "total_left": total_left_reval_wf2(),
          "done_this_week": done_week_wf2(0, 0),
          "time_this_week": time_week_wf2(0, 0),
          "done_last_week": done_week_wf2(0, -1),
          "time_last_week": time_week_wf2(0, -1),
          }


json.dump(report, open("data/state_wf2.json", "w+"))
