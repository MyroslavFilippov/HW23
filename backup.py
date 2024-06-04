import psycopg2
import select
from datetime import datetime, timedelta
from threading import Thread
from apscheduler.schedulers.blocking import BlockingScheduler

# Database connection details
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'example_db'
DB_USER = 'example_user'
DB_PASSWORD = 'example_password'

# Connect to PostgreSQL
def connect():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Full backup
def full_backup():
    with connect() as conn:
        with conn.cursor() as cur:
            with open('full_backup.csv', 'w') as f:
                cur.copy_expert("COPY books TO STDOUT WITH CSV HEADER", f)

# Incremental backup
def incremental_backup(last_backup_time):
    with connect() as conn:
        with conn.cursor() as cur:
            with open('incremental_backup.csv', 'w') as f:
                query = f"COPY (SELECT * FROM books WHERE last_modified > '{last_backup_time}') TO STDOUT WITH CSV HEADER"
                cur.copy_expert(query, f)

# Differential backup
def differential_backup(full_backup_time):
    with connect() as conn:
        with conn.cursor() as cur:
            with open('differential_backup.csv', 'w') as f:
                query = f"COPY (SELECT * FROM books WHERE last_modified > '{full_backup_time}') TO STDOUT WITH CSV HEADER"
                cur.copy_expert(query, f)

# Reverse delta backup
def reverse_delta_backup():
    full_backup()
    incremental_backup(datetime.now() - timedelta(days=1))

# Continuous Data Protection (CDP)
def cdp():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("LISTEN books_changes;")
            print("Listening for changes on books table...")
            while True:
                if select.select([conn], [], [], 5) == ([], [], []):
                    continue
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    print(f"Change detected: {notify.payload}")

# Schedule the batch filling and backups
def schedule_jobs():


    scheduler = BlockingScheduler()

    # Schedule full backup every day at 12 am
    scheduler.add_job(full_backup, 'cron', hour=0, minute=0)

    full_backup_time = datetime.now()

    # Schedule incremental backup every hour
    scheduler.add_job(incremental_backup, 'interval', hours=1, args=[full_backup_time])

    # Schedule differential backup every 6 hours
    scheduler.add_job(differential_backup, 'interval', hours=6, args=[full_backup_time])

    # Schedule reverse delta backup every 24 hours at 1 am
    scheduler.add_job(reverse_delta_backup, 'cron', hour=1, minute=0)

    # Start CDP in a separate thread

    cdp_thread = Thread(target=cdp)
    cdp_thread.daemon = True
    cdp_thread.start()

    # Start the scheduler
    scheduler.start()

if __name__ == '__main__':
    schedule_jobs()
