import mysql.connector

# Connect without specifying a database
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="14Abr2003.MYSQL"
)

# Create a cursor to execute SQL commands
cursor = connection.cursor()

# Create the database
cursor.execute("CREATE DATABASE IF NOT EXISTS ydb")
print("Database 'ydb' created sucfully!")

# Now connect to the specificabase
cursor.execute("USE ydb")

# Your existing code continues here...
# ydb = mysql.connector.connect(host="localhost", user="root", passwd="14Abr2003.MYSQL", database="ydb")