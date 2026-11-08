#!/usr/bin/env python3
"""Wake the existing guarded publisher after committed PostgreSQL notifications.

The listener uses the existing limited application database role in read-only
transactions. It can start one fixed systemd unit; notification payloads are never executed, logged or forwarded.
The original timer remains the independent fallback.
"""
import os
import subprocess
import psycopg

CHANNEL='ism_bank_publication'
UNIT='ism-oracle-bank-review.service'
PENDING="""SELECT EXISTS(SELECT 1 FROM bank_publications WHERE state='exported') OR
 EXISTS(SELECT 1 FROM review_outbox WHERE kind='publication-intent'
 AND finished_at IS NULL AND available_at<=now())"""

def events(conn,timeout=5):
    conn.execute('LISTEN '+CHANNEL)
    yield 'ready' # LISTEN precedes the startup wake; restart cannot miss queued work.
    while True:
        # Capture only a bounded notification burst; one wake is sufficient.
        notifications=conn.notifies(timeout=timeout,stop_after=1)
        try:changed=next(notifications,None) is not None
        finally:notifications.close()
        if changed or conn.execute(PENDING).fetchone()[0]:yield 'wake'


def start_publisher():
    subprocess.run(['systemctl','start','--no-block',UNIT],check=True,timeout=10)


def serve():
    # Reuse the existing service credential; never log it or store another copy.
    database=os.environ.get('DATABASE_URL','postgresql://mpsc@localhost:5432/mpsc')
    with psycopg.connect(database,autocommit=True,options='-c default_transaction_read_only=on -c statement_timeout=5000')as conn:
        for event in events(conn):
            if event in ('ready','wake'):
                start_publisher()
                print('Publisher wake requested',flush=True)

if __name__=='__main__':serve()
