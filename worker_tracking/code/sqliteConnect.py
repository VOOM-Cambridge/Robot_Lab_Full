
import sqlite3
from datetime import datetime
import json
import time

class sqliteConnect:
    def __init__(self, config_file_json):
        self.tableName = config_file_json['dataBaseName']
        self.fileName = config_file_json['filePath']

    def connect(self):
        self.conn = sqlite3.connect(self.fileName, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cursor = self.conn.cursor()
        checkTable = ''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}' '''.format(self.tableName)
        checkAnswer = self.cursor.execute(checkTable)
        print(checkAnswer)
        if self.cursor.fetchone()[0]!=1:
            print("Table needs creating")
            table = """CREATE TABLE {0}(IDNUM VARCHAR(50), FIRST_NAME VARCHAR(100), STATUS VARCHAR(20), TIME_LAST_ACTION TIMESTAMP, TIME_WORKED INTEGER, TIME_WORKED_TODAY INTEGER);""".format(self.tableName)
            self.cursor.execute(table)

    def addNew(self, IDnum, firstName, status):
        self.cursor = self.conn.cursor()
        timeNow = datetime.now()
        insertQuery = """INSERT INTO {0} VALUES (?, ?, ?, ?, ?, ?);""".format(self.tableName)
        self.cursor.execute(insertQuery, (IDnum, firstName, status, timeNow, 0, 0))
        #self.cursor.execute(conn)
        self.conn.commit()
        return "data added"

    def updateStatus(self, IDnum, statusNew):
        data = self.checkIfExists(IDnum)
        lastAction = data[3]
        timeWorkedOld = data[4]
        timeWokedToday = data[5]
        self.cursor = self.conn.cursor()
        timeNow = datetime.now()
        reset = False
        dayStart = datetime(timeNow.year, timeNow.month, timeNow.day, 0, 0, 0)
        if statusNew == "Log out": # logging out of job
            # calculate time passed since login
            timePastS = (timeNow - lastAction).total_seconds()
            # calculate time since day start 
            if lastAction < dayStart:
                reset = True
                timeForDay = (timeNow - dayStart).total_seconds()
            else:
                timeForDay = (timeNow - lastAction).total_seconds()
        else: # logging in to job
            if lastAction < dayStart:
                reset = True
            timePastS = 0 
            timeForDay = 0    
        # convert new times to get ready to store
        print(timePastS)
        timeWorked = timeWorkedOld + timePastS
        if reset: # new day 
            timeWorkToday = timeForDay
        else:
            timeWorkToday = timeForDay + timeWokedToday
        # Updating
        conText = '''UPDATE {0} SET STATUS = '{2}', TIME_LAST_ACTION = '{3}', TIME_WORKED = '{4}', TIME_WORKED_TODAY = '{5}' WHERE IDNUM = '{1}';'''.format(self.tableName, IDnum, statusNew, timeNow, timeWorked, timeWorkToday)

        self.cursor.execute(conText)
        self.conn.commit()
        return "data updated in " + IDnum

    def allData(self):
        data = self.cursor.execute('''SELECT * FROM {0}'''.format(self.tableName))
        return data
    
    def checkIfExists(self, IDnum):
        res = self.cursor.execute("SELECT * FROM {0} WHERE trim(IDNUM) LIKE '{1}'".format(self.tableName, IDnum))
        data = res.fetchall()
        if len(data) > 0:
            return data[0]
        else:
            return []
        
            
