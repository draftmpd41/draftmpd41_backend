# dbconnect.py

import urllib.parse # urljoin
import sqlalchemy
# requires pymysql so keep that installed
import pandas as pd
import os, json, time

import commonfuncs as cf

root = os.path.dirname(__file__) # needed for tornado
absPath = os.path.realpath(__file__)

#############################
# initiate DB connection
creds = {"host": os.environ.get('MYSQL_SERVER'),
    "db": os.environ.get('MYSQL_DB'),
    "uid": os.environ.get('MYSQL_UID'),
    "pw": os.environ.get('MYSQL_PW')
}
tsql1 = time.time()
conn_str = f"mysql+pymysql://{creds['uid']}:{creds['pw']}@{creds['host']}/{creds['db']}"
sqlEngine = sqlalchemy.create_engine(conn_str,echo=False, pool_recycle=1)
tsql2 = time.time()
cf.logmessage(f"Connected to SQL in {round(tsql2-tsql1,3)} secs")

#############################
# SQL security

def sqlSecurty(x, inputTerm=False):
    sqlBlacklist = [';', '(select', '-->', '<--', '<!--', 'sleep(', '#exec']
    sql_inputs_Blacklist = sqlBlacklist + list(""""'`\/^*()!#""") # 2021-06-17 allowing space

    if isinstance(x, (int, float)):
        # its a number. let em pass
        return True
    if not isinstance(x, str):
        # not a number, not a string also? Suspicious!
        cf.logmessage("not a number, not a string also? Suspicious!")
        return False
    if inputTerm:
        # stricter check for input values ids tablenames etc
        if any([f in x for f in sql_inputs_Blacklist]):
            return False
    else:
        if any([f in x for f in sqlBlacklist]):
            return False
    return True


def sqlSecurity_payload(payload):
    for key in payload.keys():
        if not sqlSecurty(key, inputTerm=True):
            cf.logmessage("Suspicious key found in payload json")
            return False
        if not sqlSecurty(payload[key], inputTerm=True):
            cf.logmessage("Suspicious value found in payload json")
            return False
    return True


#############################
# Generic SQL query handling functions

def makeQuery(s1, output='oneValue', lowerCaseColumns=False, keepCols=True, fillna=True):
    '''
    output choices:
    oneValue : ex: select count(*) from table1 (output will be only one value)
    oneRow : ex: select * from table1 where id='A' (output will be onle one row)
    df: ex: select * from users (output will be a table)
    list: json array, like df.to_dict(orient='records')
    column: first column in output as a list. ex: select username from users
    oneJson: First row, as dict
    '''
    if not isinstance(s1,str):
        cf.logmessage("query needs to be a string")
        return False
    if ';' in s1:
        cf.logmessage("; not allowed")
        return False

    # if len(s1) > 100:
    #     cf.logmessage("Querying SQL: {}...".format(s1.strip().replace('\n',' ')[:100]))
    # else:
    #     cf.logmessage("Querying SQL:",s1.strip().replace('\n',' '))
    
    # # keeping auth check and some other queries out
    # skipPrint = ['where token=', '.STArea()', 'STGeomFromText']
    # if not any([(x in s1) for x in skipPrint]) : 
    #     cf.logmessage("Querying SQL:",s1.strip().replace('\n',' '))
    # else: 
    #     cf.logmessage("Querying SQL: {}...".format(s1.strip().replace('\n',' ')[:20]))

    global sqlEngine
    c = sqlEngine.connect()
    if output == 'oneValue':
        result = c.execute(s1).fetchone()
        c.close()
        if not result: return None
        return result[0]
    elif output == 'oneRow':
        result = c.execute(s1).fetchone()
        c.close()
        return result
    elif output in ['df','list','oneJson','column']:
        # df
        if fillna:
            df = pd.read_sql_query(s1, con=c, coerce_float=False).fillna('') 
        else:
            df = pd.read_sql_query(s1, con=c, coerce_float=False)
        # coerce_float : need to ensure mobiles aren't screwed
        c.close()
        
        # make all colunm headers lowercase
        # if lowerCaseColumns: df.columns = [x.lower() for x in df.columns] # from https://stackoverflow.com/questions/19726029/how-can-i-make-pandas-dataframe-column-headers-all-lowercase
        
        if output=='df':
            if (not len(df)) and (not keepCols): return []
            else: return df

        if not len(df): return []
        if output == 'column':
            return df.iloc[:,0].tolist() # .iloc[:,0] -> first column
        elif output == 'list':
            return df.to_dict(orient='records')
        elif output == 'oneJson':
            return df.to_dict(orient='records')[0]
        else:
            # default - df
            return df


def execSQL(s1):
    if not isinstance(s1,str):
        cf.logmessage("query needs to be a string")
        return False
    if ';' in s1:
        cf.logmessage("; not allowed")
        return False

    if len(s1) > 100:
        cf.logmessage("Executing SQL: {}...".format(s1.strip().replace('\n',' ')[:100]))
    else:
        cf.logmessage("Executing SQL:",s1.strip().replace('\n',' '))

    # # keeping auth check and some other queries out
    # skipPrint = ['set token=', 'polyline6', 'STGeomFromText']
    # if not any([(x in s1) for x in skipPrint]) : 
    #     cf.logmessage("Executing SQL:",s1.strip().replace('\n',' '))
    # else: 
    #     cf.logmessage("Executing SQL: {}...".format(s1.strip().replace('\n',' ')[:20]))

    global sqlEngine
    try:
        c = sqlEngine.connect()
        c.execute(s1)
        c.close()
        return True
    except sqlalchemy.exc.IntegrityError as e:
        cf.logmessage("This entry already exists, skipping.")
        cf.logmessage(e)
        return False
    except:
        cf.logmessage('WARNING: could not execute query.')
        raise
        return False


##### brought in from Sourcing Workflow application
def getColumnsList(tablename, engine):
    statement1 = f"""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = N'{tablename}'
    """
    # sql = db.text(statement1)
    df = pd.read_sql_query(statement1,con=engine)
    # return df['COLUMN_NAME'].str.lower().to_list()
    return df['COLUMN_NAME'].to_list()


def addRow(params,tablename):
    df = pd.DataFrame([params]) 
    return addTable(df, tablename) # heck

def addTable(df, tablename):
    global sqlEngine
    c = sqlEngine.connect()

    table_cols = getColumnsList(tablename,c)
    # df.columns = [x.lower() for x in df.columns] # make lowercase
    sending_cols = [x for x in table_cols if x in df.columns]
    discarded_cols = set(df.columns.to_list()) - set(table_cols)
    if len(discarded_cols): cf.logmessage("Dropping {} cols from uploaded data as they're not in the DB: {}".format(len(discarded_cols),', '.join(discarded_cols)))
    
    # ensure only those values go to DB table that have columns there
    # cf.logmessage("Adding {} rows into {} with these columns: {}".format(len(df), tablename, sending_cols))
    try:
        df[sending_cols].to_sql(name=tablename, con=c, if_exists='append', index=False )
        c.close()
    except:
        c.close()
        return False
    return True
