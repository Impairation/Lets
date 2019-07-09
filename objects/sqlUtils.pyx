from objects import glob
import pandas as pd
from common.db import dbConnector
from helpers import config

def pandasQuery(query_str):
	return pd.DataFrame.from_dict(list(glob.db.fetchAll(query_str)))

def wrapArrayForSelect(els):
	return '(' + ','.join(['\''+str(x)+'\'' for x in els]) + ')'

def connectToDB(connections):
	readConfig = config.config("config.ini")
	return dbConnector.db(readConfig.config["db"]["host"], readConfig.config["db"]["username"], readConfig.config["db"]["password"], readConfig.config["db"]["database"], 2)