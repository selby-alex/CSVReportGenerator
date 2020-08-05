# CSVReportGenerator

CSVReportGenerator (CRG) is a tool made to pull data from a database and deliver it to the end-user in a CSV file.

To properly function, CRG requires...

- access to a google or other SMTP client
- database credentials

## Functional Overview

The program is designed to be run once a day, typically early to get Ops/marketing personel required data early in the day. In the past, I typically had it run at 8:30am to deliver reports as people were sitting at their desks.

The general flow is:

1. CRG pulls all SQL files stored in the _queries_ directory and loops over a list of the files
2. CRG validates that the file has been scheduled and whether it should be run on the current day
3. If the query should run, CRG...
   opens a database connection
   runs the query stored in the _.sql_ file
   loads returned data into a temp _.csv_ file
   creates an SMTP MIMEmultipart message and attaches the _.csv_
   sends it to all recipients stored in the scheduled list

## Set up

1. Create a scheduler object in the **schedule_manager.py** file
2. options are...
   dow: day of week, [0-6]
   dom: day of month, [1-31]
   qrt: quarterly sending

```python
# python scheduler objects
schedule_manager = {
 "sample_query.sql": {
     "frequency": "dow",
     "day_validator" : [1,2,3,4,5,6],
     "receiver" : ["alex@protoboard.io"]
 },
}
```

3. in the **queries** directory,

```sql
select * from schema.database limit 10;
```

4. Schedule the code to run daily using either CRON or a cloud service like AWS Lambda + Cloudwatch
