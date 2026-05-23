import sqlite3
import csv
import itertools
from datetime import datetime
from dateutil import parser

conn = sqlite3.connect('test_db.db')
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()



conn.commit()
conn.close()