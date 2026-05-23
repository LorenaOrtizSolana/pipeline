import sqlite3

conn = sqlite3.connect('test_db.db')
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

cursor.execute('''
               CREATE TABLE IF NOT EXISTS balance
               (
                   BalanceId
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   AccountId
                   INTEGER
                   NOT
                   NULL
                   UNIQUE,
                   Balance
                   DECIMAL(12,2),
                   DateLastUpdate
                   DATETIME,
                   Timezone
                   TEXT,
                   FOREIGN
                   KEY
               (
                   AccountId
               ) REFERENCES accounts
               (
                   AccountId
               )
                   ON DELETE CASCADE
                   ON UPDATE CASCADE
                   )
               ''')

cursor.execute('''CREATE TRIGGER IF NOT EXISTS update_balance_after_transaction_delete      
AFTER
DELETE
ON transactions      
FOR EACH ROW
BEGIN
UPDATE balance
SET Balance        = (SELECT IFNULL(SUM(Amount), 0)
                      FROM transactions
                      WHERE AccountId = OLD.AccountId),
    DateLastUpdate = (SELECT MAX(Date)
                      FROM transactions
                      WHERE AccountId = OLD.AccountId)
WHERE AccountId = OLD.AccountId;
END;
               ''')

cursor.execute('''CREATE TRIGGER IF NOT EXISTS update_balance_after_transaction_update      
AFTER
UPDATE ON transactions
    FOR EACH ROW
BEGIN
UPDATE balance
SET Balance        = (SELECT IFNULL(SUM(Amount), 0)
                      FROM transactions
                      WHERE AccountId = NEW.AccountId),
    DateLastUpdate = (SELECT MAX(Date)
                      FROM transactions
                      WHERE AccountId = NEW.AccountId)
WHERE AccountId = NEW.AccountId;

UPDATE balance
SET Balance        = (SELECT IFNULL(SUM(Amount), 0)
                      FROM transactions
                      WHERE AccountId = OLD.AccountId),
    DateLastUpdate = (SELECT MAX(Date)
                      FROM transactions
                      WHERE AccountId = OLD.AccountId)
WHERE AccountId = OLD.AccountId
  AND OLD.AccountId != NEW.AccountId;
END;
               ''')

cursor.execute(''' CREATE TRIGGER IF NOT EXISTS update_balance_after_transaction_insert        
AFTER INSERT ON transactions        
FOR EACH ROW
BEGIN
UPDATE balance
SET Balance        = (SELECT IFNULL(SUM(Amount), 0)
                      FROM transactions
                      WHERE AccountId = NEW.AccountId),
    DateLastUpdate = (SELECT MAX(Date)
                      FROM transactions
                      WHERE AccountId = NEW.AccountId)
WHERE AccountId = NEW.AccountId;
END;
               ''')

# Fill balance table
# all accounts should appear even if they have no transactions
cursor.execute('DELETE FROM balance')
cursor.execute('''
               INSERT INTO balance (AccountId, Balance)
               SELECT a.AccountId, IFNULL(SUM(t.Amount), 0)
               FROM accounts a
                        LEFT JOIN transactions t ON a.AccountId = t.AccountId
               GROUP BY a.AccountId
               ''')

conn.commit()
conn.close()