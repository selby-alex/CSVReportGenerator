import smtplib
import email.message
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from os import environ as env
from os import listdir
from dotenv import load_dotenv, find_dotenv
import csv, datetime, os
import psycopg2 as pg
from schedule_manager import schedule_manager


load_dotenv(find_dotenv())
d = datetime.datetime.now()
d = d.strftime("%Y-%m-%d")

def email_sender(requirements, report):
    username = env.get('USERNAME')
    password = env.get('PASSWORD')
    recipients = requirements["receiver"]
    body = """Hello, 

        Your scheduled report: "{0}" is attached.
    """.format(report.replace('_', ' '))

    msg = MIMEMultipart()
    msg['Subject'] = "Protoboard: {}, {}".format(report.replace('_', ' '), d)
    msg['From'] = username
    msg['To'] = ", ".join(recipients)

    msg.attach(MIMEText(body, 'plain'))

    filename = "{0}_{1}.csv".format(report,d)

    part = MIMEBase('application', "octet-stream")
    part.set_payload(open("/tmp/{}".format(filename), "rb").read())
    encoders.encode_base64(part)

    part.add_header('Content-Disposition', 'attachment; filename={}_{}.csv'.format(report, d))

    msg.attach(part)

    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(username, password)
        server.sendmail(msg['From'], recipients, msg.as_string())
        server.close()

    except Exception as e:  
        print(e)


def report_grabber(query):
    conn_string = "dbname='{}' port='{}' user='{}' password='{}' host='{}'"\
            .format(env.get('DB_NAME'), env.get('DB_PORT'), env.get('DB_USER'), env.get('DB_PW'), env.get('DB_HOST'))

    try:
        con = pg.connect(conn_string)
        cur = con.cursor()
    except Exception as e:
        print(e)
        print("Unable to connect to Redshift")

    try:
        cur.execute(query)
        response = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
    except Exception as e:
        print(e)
        print("Failed to execute copy command")

    con.close()

    return response, colnames

def csv_writer(headers, data ,report="report_from"):
    report = open("/tmp/{0}_{1}.csv".format(report, d), "w") ## need /tmp/ for lambda
    report_writer = csv.writer(report, delimiter=",")
    report_writer.writerow(headers)

    for row in data:
        full_row = []
        for cell in row:
            full_row.append(cell)
        report_writer.writerow(row)

    report.close()


def sql_scripts():
    scripts = []
    
    for file in listdir("/var/task/queries"):
        if file.endswith(".sql"):
            scripts.append(file)

    return(scripts)

def date_validator(requirements):
    dom_actual = int(datetime.datetime.today().strftime('%d'))
    dow_actual = int(datetime.datetime.today().weekday())
    qrt_actual = int(datetime.datetime.today().strftime('%m'))

    should_run = False

    if requirements["frequency"] == "dow" and dow_actual in requirements["day_validator"]:
        should_run = True
    elif requirements["frequency"] == "dom" and dom_actual in requirements["day_validator"]:
        should_run = True
    elif requirements["frequency"] == "qrt" and dom_actual in requirements["day_validator"] and qrt_actual in [1,4,7,10]: ##first day of new quarter
        should_run = True

    return should_run

def execute_script(event, context):
    scripts = sql_scripts()
    for script in scripts:
        print("running {}".format(script))
        if script in schedule_manager:
            if date_validator(schedule_manager[script]):
                sql = open("/var/task/queries/{}".format(script), "r").read()
                response, colnames = report_grabber(sql)
                csv_writer(headers = colnames, data= response, report = script.replace('.sql', ''))
                email_sender(schedule_manager[script], report = script.replace('.sql', ''))
            else:
                print("report: {} should not run".format(script))
        else:
            print("report: {} is not properly scheduled".format(script))
