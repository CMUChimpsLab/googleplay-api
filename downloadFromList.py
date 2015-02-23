import sys
import time
import traceback
from pymongo import MongoClient
from multiprocessing import Pool, get_logger
from download import connect, downloadApkAndUpdateDB
import random

from config import *

from dbConfig import USERNAME, PASSWORD

nextAuthTime = int(time.time()) + random.randint(900,3600)
if __name__ == '__main__':
    client = MongoClient('localhost',27017)
    client['admin'].authenticate(USERNAME, PASSWORD)
    db = client['androidApp']

    if (len(sys.argv) < 4):
      print """Usage: python downloadFromList.py app_list_file file_dir 
        downloaded_list_file [download_progress_file]"""
      sys.exit(0)

    appListFile = open(sys.argv[1])
    fileDir = sys.argv[2]
    downloadedList = open(sys.argv[3], "a")
    progressFile = sys.stdout

    if (len(sys.argv) == 5):
      progressFile = open(sys.argv[4], "a") 

    #the first line of appList is a timestamp
    appListFile.readline()
    appList = appListFile.read().split('\n')
    appListFile.close()

    numApps = len(appList)
    numProcessed = 0

    def apiConnect():
      if len(ANDROID_ID_S) > 0:
        # Pick a random account to use
        i = random.randint(0, len(ANDROID_ID_S) - 1)
        return connect(ANDROID_ID_S[i], GOOGLE_LOGIN_S[i], GOOGLE_PASSWORD_S[i], AUTH_TOKEN_S[i])
      else:
        # Use a single account
        return connect(ANDROID_ID, GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)

    api = apiConnect()
    nextAuthTime = int(time.time()) + random.randint(900,3600)
    def downloadPackage(packagename, db=db, fileDir=fileDir):
        global nextAuthTime
        global api
        global numProcessed
        global numApps
        try:
          if int(time.time()) > nextAuthTime:
            api = apiConnect()
            nextAuthTime = int(time.time()) + random.randint(900,3600)

            # Update progress
            percent = (float(numProcessed)/numApps) * 100
            progress = "%d \t %.2f%s" % (int(time.time()), percent, "%")
            progressFile.write(progress + "\n")

          success, msg = downloadApkAndUpdateDB(api, db, packagename, fileDir)
          
          if success:
            # Write package name to downloaded list
            downloadedList.write(packagename + "\n")
          
          numProcessed += 1

          # TODO Send email to alert for failure
        except:
            print >> sys.stderr, int(time.time()), packagename
            traceback.print_exc(file=sys.stderr)
        return packagename
      
    for app in appList:
      downloadPackage(app)

    downloadedList.close()
    progressFile.close()

    """
    the following code always stops for a period of time
    """
    #numberOfProcess = 1
    #pool = Pool(numberOfProcess)
    #for packagename in pool.imap(downloadPackage, appList):
    #    print packagename
    #    #sys.stdout.flush()
