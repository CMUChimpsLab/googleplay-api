import sys
from pymongo import MongoClient
from multiprocessing import Pool, get_logger
from download import connect, downloadApkAndUpdateDB



if __name__ == '__main__':
    client = MongoClient('localhost',27017)
    db = client['androidApp']
    appListFile = open(sys.argv[1])
    fileDir = sys.argv[2]

    appListFile.readline()
    appList = appListFile.read().split('\n')
    appListFile.close()
    def downloadPackage(packagename, db=db, fileDir=fileDir):
        api = connect()
        downloadApkAndUpdateDB(api, db, packagename, fileDir)
        return packagename
      
    

    numberOfProcess = 1
    pool = Pool(numberOfProcess)
    for packagename in pool.imap(downloadPackage, appList):
        print packagename
        sys.stdout.flush()
