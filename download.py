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
client = MongoClient('localhost',27017)
db = client['androidApp']

if (len(sys.argv) < 2):
    print "Usage: %s packagename [filename]"
    print "Download an app."
    print "If filename is not present, will write to packagename.apk."
    sys.exit(0)

packagename = sys.argv[1]

if (len(sys.argv) == 3):
    fileDir = sys.argv[2]
    filename = sys.argv[2] + '/' + packagename + ".apk"
else:
    filename = packagename + ".apk"

# Connect
api = GooglePlayAPI(ANDROID_ID)
try:
  api.login(GOOGLE_LOGIN, GOOGLE_PASSWORD, AUTH_TOKEN)
except:
  print >> sys.stderr, int(time.time()), packagename
  traceback.print_exc(file=sys.stderr)
  sys.exit(-1)

# Get the version code and the offer type from the app details
try:
  m = api.details(packagename)
except:
  print >> sys.stderr, int(time.time()), packagename
  traceback.print_exc(file=sys.stderr)
  sys.exit(-1)
  
doc = m.docV2
vc = doc.details.appDetails.versionCode
try:
  ot = doc.offer[0].offerType
except:
  print >> sys.stderr, int(time.time()), packagename
  print >> sys.stderr, doc
  traceback.print_exc(file=sys.stderr)
  sys.exit(-1)


packageName = doc.details.appDetails.packageName
docDict = eval(str(api.toDict(doc)))

isApkUpdated = False
#apkDetails is collection for doc + updated timestamp
#if docDict does change, update the db entry
#use more query instead of insertion to speed up
#Do not get fields not in docDict from apkDetails
preDetailsEntry = db.apkDetails.find_one({'details.appDetails.packageName': packageName}, {'updatedTimestamp':0, '_id':0})
if preDetailsEntry != docDict:
    #versionCode is used for determine whether apk has been updated
    #http://developer.android.com/tools/publishing/versioning.html
    isApkUpdated = docDict['details']['appDetails']['versionCode'] != preDetailsEntry['details']['appDetails']['versionCode']
    docDict['updatedTimestamp'] = datetime.datetime.utcnow()
    db.apkDetails.update({'details.appDetails.packageName': packageName}, docDict, upsert=True)
else:
    isApkUpdated = False


infoDict = docDict['details']['appDetails']

isFree = not doc.offer[0].checkoutFlowRequired
isDownloaded = False

#If exceed 50mb apk will not be downloaded, 50mb limit is set on play store by googleplay
#http://developer.android.com/distribute/googleplay/publish/preparing.html#size
isSizeExceed = None
if doc.details.appDetails.installationSize > 52428800:
  isSizeExceed = True
else:
  isSizeExceed = False

# Download
if isFree and not isSizeExceed and isApkUpdated:
  try:
    data = api.download(packageName, vc, ot)
  except Exception as e:
    print >> sys.stderr,int(time.time()), packageName
    traceback.print_exc(file=sys.stderr)
    isDownloaded = False
  else:
    print int(time.time()), packageName
    print "Downloading %s..." % sizeof_fmt(doc.details.appDetails.installationSize),
    open(filename, "wb").write(data)
    print "Done"
    isDownloaded = True
  
#Remove db entry fields which are not in infoDict
preInfoEntry = db.apkInfo.find_one({'packageName': packageName}, {'isFree':0, 'isSizeExceed': 0, 'isApkUpdated':0, 'updatedTimestamp':0, '_id':0})
preIsDownloaded = preInfoEntry.pop('isDownloaded', False)
preFileDir = preInfoEntry.pop('fileDir', '')

#update apkInfo entry if infoDict updated (a new entry is also counted as updated) or apkDownloaded first time
if preInfoEntry != infoDict or (preIsDownloaded == False and isDownloaded == True):
    #apkInfo is collection for doc.details.appDetails, and also add isFree and isDownloaded
    infoDict['isFree'] = isFree
    #infoDict['isDownloaded'] only indicates whether we ever downloaded this apk.
    #isDownloaded indicates whether current download succeeds 
    infoDict['isDownloaded'] = preIsDownloaded or isDownloaded
    if isDownloaded:
        #Only update fileDir when new file updated
        #first round crawling has one bug that all apps have a not empty fileDir 
        infoDict['fileDir'] = fileDir
    else:
        #Still using previous fileDir
        infoDict['fileDir'] = preFileDir 
    #This is for static analysis purpose. Add the flag when versionCode changed and apk is sucessfully downloaded. 
    #Everytime only analyze db.apkInfo.find({'isApkUpdated': True})
    #after analyze change the isApkUpdated to False
    infoDict['isApkUpdated'] = isApkUpdated and isDownloaded
    if isSizeExceed != None:
        infoDict['isSizeExceed'] = isSizeExceed
    infoDict['updatedTimestamp'] = datetime.datetime.utcnow()
    #even the download is not successful, if the appDetails is updated, the db entry will be updated
    db.apkInfo.update({'packageName': packageName}, infoDict, upsert=True)
