import sys
import time
import traceback
from pymongo import MongoClient
from multiprocessing import Pool, get_logger
from download import connect, downloadApkAndUpdateDB
import random

nextAuthTime = int(time.time()) + random.randint(900,3600)
if __name__ == '__main__':
    client = MongoClient('localhost',27017)
    db = client['androidApp']
    appListFile = open(sys.argv[1])
    fileDir = sys.argv[2]

    #the first line of appList is a timestamp
    appListFile.readline()
    appList = appListFile.read().split('\n')
    appListFile.close()
    api = connect()
    nextAuthTime = int(time.time()) + random.randint(900,3600)
    def downloadPackage(packagename, db=db, fileDir=fileDir):
        global nextAuthTime
        global api
        try:
          if int(time.time()) > nextAuthTime:
              api = connect()
              nextAuthTime = int(time.time()) + random.randint(900,3600)
          downloadApkAndUpdateDB(api, db, packagename, fileDir)
        except:
            print >> sys.stderr, int(time.time()), packagename
            traceback.print_exc(file=sys.stderr)
        return packagename
      
    for app in appList:
        downloadPackage(app)

    """
    the following code always stops for a period of time
    """
    #numberOfProcess = 1
    #pool = Pool(numberOfProcess)
    #for packagename in pool.imap(downloadPackage, appList):
    #    print packagename
    #    #sys.stdout.flush()
