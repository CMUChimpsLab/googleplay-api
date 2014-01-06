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
#apkDetails is collection for doc
#TODO add version control
db.apkDetails.update({'details.appDetails.packageName': packageName}, docDict, upsert=True)

infoDict = docDict['details']['appDetails']

isFree = not doc.offer[0].checkoutFlowRequired
isDownloaded = False

#If exceed 50mb do not download
isSizeExceed = None
if doc.details.appDetails.installationSize > 52428800:
  isSizeExceed = True
else:
  isSizeExceed = False
# Download
if isFree and not isSizeExceed:
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
  

#apkInfo is collection for doc.details.appDetails, and also add isFree and isDownloaded
infoDict['isFree'] = isFree
infoDict['isDownloaded'] = isDownloaded
infoDict['fileDir'] = fileDir
if isSizeExceed != None:
  infoDict['isSizeExceed'] = isSizeExceed

db.apkInfo.update({'packageName': packageName}, infoDict, upsert=True)
