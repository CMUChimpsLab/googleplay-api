import sys
import time
import traceback
from pymongo import MongoClient
from multiprocessing import Pool, get_logger
from download import connect, downloadApkAndUpdateDB
import random

from dbConfig import USERNAME, PASSWORD

nextAuthTime = int(time.time()) + random.randint(900,3600)
if __name__ == '__main__':
    client = MongoClient('localhost',27017)
    client['admin'].authenticate(USERNAME, PASSWORD)
    db = client['androidApp']

    if (len(sys.argv) < 4):
      print """Usage: python downloadFromList.py app_list_file file_dir 
        downloaded_list_file"""
      sys.exit(0)

    appListFile = open(sys.argv[1])
    fileDir = sys.argv[2]
    downloadedList = open(sys.argv[3], "a")

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
          success, msg = downloadApkAndUpdateDB(api, db, packagename, fileDir)
          
          if success:
            # Write package name to downloaded list
            downloadedList.write(packagename + "\n")

          # TODO Send email to alert for failure
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
