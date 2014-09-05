#!/usr/bin/python

# Do not remove
GOOGLE_LOGIN = GOOGLE_PASSWORD = AUTH_TOKEN = None

import sys
import traceback
import time
from pprint import pprint

from config import *
from googleplay import GooglePlayAPI
from helpers import sizeof_fmt

from pymongo import MongoClient

import datetime


# Connect
def connect():
    api = GooglePlayAPI(ANDROID_ID)
    try:
      api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)
    except:
      print >> sys.stderr, int(time.time()) 
      traceback.print_exc(file=sys.stderr)
    return api

# Get the version code and the offer type from the app details
def downloadApkAndUpdateDB(api, db, packagename, fileDir):
    filename = fileDir + '/' + packagename + ".apk"
    try:
      m = api.details(packagename)
    except:
      print >> sys.stderr, int(time.time()), packagename
      traceback.print_exc(file=sys.stderr)
      return
      
    doc = m.docV2
    vc = doc.details.appDetails.versionCode
    try:
      ot = doc.offer[0].offerType
    except:
      print >> sys.stderr, int(time.time()), packagename
      print >> sys.stderr, doc
      traceback.print_exc(file=sys.stderr)
      return
    
    
    packageName = doc.details.appDetails.packageName
    #use eval, since only with api.toDict, pymongo will throw some warning related to wsgi
    docDict = eval(str(api.toDict(doc)))
    
    isApkUpdated = False
    #apkDetails is collection for doc + updated timestamp
    #if docDict does change, update the db entry
    #use more query instead of insertion to speed up
    #Do not get fields not in docDict from apkDetails
    preDetailsEntry = db.apkDetails.find_one({'details.appDetails.packageName': packageName}, {'updatedTimestamp':0, '_id':0})
    if preDetailsEntry != docDict:
        #Warning: sometimes versionCode is not available
        #versionCode is used for determine whether apk has been updated
        #http://developer.android.com/tools/publishing/versioning.html
        try:
            isApkUpdated = (not preDetailsEntry) or (docDict['details']['appDetails']['versionCode'] != preDetailsEntry['details']['appDetails']['versionCode'])
        except KeyError as e:
            isApkUpdated = True
        docDict['updatedTimestamp'] = datetime.datetime.utcnow()
        db.apkDetails.update({'details.appDetails.packageName': packageName}, docDict, upsert=True)
    else:
        isApkUpdated = False
    
    
    infoDict = docDict['details']['appDetails']
    
    isFree = not doc.offer[0].checkoutFlowRequired
    isCurrentVersionDownloaded = False
    
    #If exceed 50mb apk will not be downloaded, 50mb limit is set on play store by googleplay
    #http://developer.android.com/distribute/googleplay/publish/preparing.html#size
    isSizeExceed = None
    if doc.details.appDetails.installationSize > 52428800:
      isSizeExceed = True
    else:
      isSizeExceed = False
    
    #Remove db entry fields which are not in infoDict
    preInfoEntry = db.apkInfo.find_one({'packageName': packageName}, {'isFree':0, 'isSizeExceed': 0, 'updatedTimestamp':0, '_id':0})
    if preInfoEntry == None:
      preInfoEntry = {}
    preIsDownloaded = preInfoEntry.pop('isDownloaded', False)
    preIsCurrentVersionDownloaded = preInfoEntry.pop('isCurrentVersionDownloaded', False)
    preIsApkUpdated = preInfoEntry.pop('isApkUpdated', False)
    preFileDir = preInfoEntry.pop('fileDir', '')
    
    # Download when it is free and not exceed 50 mb and (current version in apkInfo was not downloaded or app has been updated since last time update apkInfo version)
    if isFree and (not isSizeExceed) and ((not preIsCurrentVersionDownloaded) or isApkUpdated):
      try:
        data = api.download(packageName, vc, ot)
      except Exception as e:
        print >> sys.stderr,int(time.time()), packageName
        traceback.print_exc(file=sys.stderr)
        isCurrentVersionDownloaded = False
      else:
        print int(time.time()), packageName
        print "Downloading %s..." % sizeof_fmt(doc.details.appDetails.installationSize),
        if preFileDir != '':
          fileDir = preFileDir
          filename = preFileDir + '/' + packagename + ".apk"
        open(filename, "wb").write(data)
        print "Done"
        isCurrentVersionDownloaded = True
    else:
        if isApkUpdated == False and preIsCurrentVersionDownloaded == True:
            isCurrentVersionDownloaded = True
        print int(time.time()), packageName
        print "Escape downloading isFree: %s, isSizeExceed: %s, preIsCurrentVersionDownloaded: %s, isApkUpdated: %s"%( isFree, isSizeExceed, preIsCurrentVersionDownloaded, isApkUpdated)
    
    #update apkInfo entry if infoDict updated (a new entry is also counted as updated) or current version apkDownloaded first time
    if preInfoEntry != infoDict or (preIsCurrentVersionDownloaded == False and isCurrentVersionDownloaded == True):
        #apkInfo is collection for doc.details.appDetails, and also add isFree and isDownloaded
        infoDict['isFree'] = isFree
        #infoDict['isDownloaded'] only indicates whether we ever downloaded this apk.
        #isCurrentVersionDownloaded indicates whether current version download succeeds 
        #It is possible previous round of cralwing did download this version, although current round fails to download the same version.
        infoDict['isDownloaded'] = preIsDownloaded or isCurrentVersionDownloaded
        infoDict['isCurrentVersionDownloaded'] = isCurrentVersionDownloaded
        if isCurrentVersionDownloaded:
            #Only update fileDir when new file updated
            #first round crawling has one bug that all apps have a not empty fileDir 
            infoDict['fileDir'] = fileDir
        else:
            #Still using previous fileDir
            infoDict['fileDir'] = preFileDir 
        #This is for static analysis purpose. Add the flag when current version apk is sucessfully downloaded and apk version updated or pre version has not been analyzed. 
        #Everytime only analyze db.apkInfo.find({'isApkUpdated': True})
        #after analyze change the isApkUpdated to False
        infoDict['isApkUpdated'] = preIsApkUpdated or (isApkUpdated and isCurrentVersionDownloaded)
        if isSizeExceed != None:
            infoDict['isSizeExceed'] = isSizeExceed
        infoDict['updatedTimestamp'] = datetime.datetime.utcnow()
        #even the download is not successful, if the appDetails is updated, the db entry will be updated
        db.apkInfo.update({'packageName': packageName}, infoDict, upsert=True)

if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print "Usage: %s packagename [filename]"
        print "Download an app."
        print "If filename is not present, will write to packagename.apk."
        sys.exit(0)
    
    packagename = sys.argv[1]
    
    if (len(sys.argv) == 3):
        fileDir = sys.argv[2]
    else:
        fileDir = '.'
    
    client = MongoClient('localhost',27017)
    db = client['androidApp']
    
    api = connect()
    downloadApkAndUpdateDB(api, db, packagename, fileDir)
