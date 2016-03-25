from BeautifulSoup import BeautifulSoup
import random
import re
import subprocess
import os
import tqdm
import argparse
import time
import sys
import urllib2
from cookielib import CookieJar

'''
Dependencies:
    1) exiftool.exe must be placed in the same location as python script
    2) pip install tqdm mechanize beautifulsoup tldextract dnspython
'''


class bcolors:
    '''Colors'''
    Default = '\033[99m'
    Cyan = '\033[96m'
    White = '\033[97m'
    Grey = '\033[90m'
    Black = '\033[90m'
    Magenta = '\033[95m'
    Blue = '\033[94m'
    Green = '\033[92m'
    Yellow = '\033[93m'
    Red = '\033[91m'
    '''Enhancers'''
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


asciiBanner = \
    "\n    ______               _  ______ "\
    "\n    |  ___|             | | | ___ \  "\
    "\n    | |_ _ __ ___  _ __ | |_| |_/ /   _ _ __  _ __   ___ _ __ " \
    "\n    |  _| '__/ _ \| '_ \| __|    / | | | '_ \| '_ \ / _ \ '__| " \
    "\n    | | | | | (_) | | | | |_| |\ \ |_| | | | | | | |  __/ |    " \
    "\n    \_| |_|  \___/|_| |_|\__\_| \_\__,_|_| |_|_| |_|\___|_|   " \
    "\n "\
    "\n\r\n"


def banner():
    print bcolors.Green + asciiBanner + bcolors.ENDC


def waitBanner():
    wait = "Discovering... this may take a moment...\r\n"
    print bcolors.BOLD + bcolors.Yellow + wait + bcolors.ENDC


def exampleUsage():
    print bcolors.BOLD + bcolors.Green + "\r\n[*]Usage Explained:" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t\r\n[*]Email search:" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t python frontrunner.py -email -d example.com" + bcolors.ENDC

    print bcolors.BOLD + bcolors.Yellow + "\r\n[*]Default document search (search for all document types):" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t python frontrunner.py -doc -d example.com" + bcolors.ENDC

    print bcolors.BOLD + bcolors.Yellow + "\r\n[*]Specific filetype document search:" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t python frontrunner.py -doc -d example.com -t doc xlsx\r\n" + bcolors.ENDC

    print bcolors.BOLD + bcolors.Yellow + "\r\n[*]Document & Email search:" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t python frontrunner.py -a -d example.com \r\n" + bcolors.ENDC

    print bcolors.BOLD + bcolors.Yellow + "\r\n[*]Document & Email search (specific filetype):" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t python frontrunner.py -a -d example.com -t doc xlsx\r\n" + bcolors.ENDC


typeList = ["doc", "docx", "xls", "xlsx", "pdf", "ppt", "pptx", "pps", "ppsx", "sxw", "sxc", "odt", "ods", "odg", "odp",
            "wdp", "svg", "svgs", "indd", "rdp", "ica"]

parser = argparse.ArgumentParser(description=banner())

parser.add_argument("-a", "--geteverything", help='This will perform document examination, email search, and dns lookup.', action="store_true")

parser.add_argument("-doc", "--documents", help='Specify document only search for metadata', action="store_true")
parser.add_argument("-email", "--emailSearch", help='Specify email only search', action="store_true")

parser.add_argument("-c", "--cached",
                    help='Specify to only work with Google Cached Text only links. Might get captcha! Currently only works for searching emails.',
                    action="store_true")

parser.add_argument("-d", "--domain", help='Domain you want to search for documents')

parser.add_argument("-t", "--type", nargs='+',
                    help='Specify file types separated by a space (" ") else all default types will be checked.'
                         'Default types:  doc,docx,xls,xlsx,pdf,ppt,pptx,pps,ppsx,sxw,sxc,odt,ods,odg,odp,wdp,svg,svgs,indd,rdp,ica',
                    default=typeList)

parser.add_argument("-dns", "--dnslookup",
                    help='Requests DNS Host Record information from hackertarget.com. Thanks @hackertarget!',
                    action="store_true")

parser.add_argument("-z", "--zoneTransfer",
                    help='Requests a Zone Transfer performed by hackertarget.com. Thanks @hackertarget!',
                    action="store_true")

args = parser.parse_args()

everything = args.geteverything
doc = args.documents
emailSearch = args.emailSearch
site = args.domain
fileTypeList = args.type
cache = args.cached
dnslookup = args.dnslookup
zoneTransfer = args.zoneTransfer

curDate = time.strftime("%Y-%m-%d")

exiftool = 'exiftool.exe'


def urllib2BrowserBuild():
    cookies = CookieJar()
    browser = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
    browser.addheaders = [('User-Agent', pickAgent())]

    return browser


def pickAgent():
    userAgentList = [
        "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Geck",
        "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 7.0; InfoPath.3; .NET CLR 3.1.40767; Trident/6.0; en-IN)",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0"
    ]
    userAgent = random.choice(userAgentList)
    return userAgent


def buildGoogleDocSearchURL(browser, site, type):

    searchURL = "https://www.google.com/search?num=100&meta=&hl=enq&q=site%3A" + site + "%20filetype%3A" + type
    openGoogle = browser.open(searchURL)
    response = openGoogle.geturl()
    return response


def beatifulSoupNextLink(scrape):
    soupy = BeautifulSoup(scrape)
    nextpage = soupy.find("a", {"id": "pnnext"})
    if nextpage is not None:
        return "https://www.google.com" + nextpage['href']
    else:
        return None


def viewPage(browser, url):

    page = browser.open(url, timeout=2)
    page_source = page.read()
    return page_source


def downloadPage(browser, url):

    fileName_regex = re.compile('(?=\w+\.\w{3,4}$).+')
    encodeUrl = url.replace('(', '%28').replace(')', '%29')
    fileName = fileName_regex.findall(encodeUrl)[0]
    try:
        docDownload = browser.open(encodeUrl, timeout=5)
        data = docDownload.read()
        with open(str(fileName), "wb") as code:
            code.write(data)
    except:
        print "\r\n[-] Failed on: " + encodeUrl + "\r\n"

    return fileName


def pageItr(source):
    page_regex = re.compile('<div\s+id=\"resultStats\">.*?</div>')
    results = page_regex.findall(source)
    results_regex = re.compile(r'\d+\s\'|[0-9][0-9\,]+')
    itr = results_regex.findall(str(results))
    return round(int(itr[0]), -2)


def grabLinks(filetype, scrape, filelist):
    link_regex = re.compile('href="(.*?)"')
    site_regex = re.compile('^(http|https)://(.*).' + site + '')
    links = link_regex.findall(scrape)
    for link in links:
        if re.match(site_regex, link):
            if link.endswith('.' + filetype):
                filelist.append(link)


def getMetaData(filename, userlist, softwarelist):
    basic = '-all ' + filename

    try:
        metaDataRaw = subprocess.check_output(executable=exiftool, args=basic)
        # email_regex = re.compile('(\w+[.|\w]*@\w+[.]*\w+)')
        email_regex = re.compile('(\w+[.|\w]*@%s)' % site)
        user_regex = re.compile('(?:Author|"Last Modified By")\s+:\s(.*)\r')
        software_regex = re.compile('(?:Software|Producer|Application)\s+:\s(.*)\r')

        user = user_regex.findall(metaDataRaw)
        if user:
            userlist.extend(user)

        emails = email_regex.findall(metaDataRaw)
        if emails:
            for email in emails:
                userlist.append(email.lower())

        software = software_regex.findall(metaDataRaw)
        if software:
            softwarelist.extend(software)

    except:
        print "\r\n[-] Metadata Error File: " + filename + "\r\n"


def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


def discoverLinksForFiles(browser,fileListTmp,typeListTmp):
    for filetype in typeListTmp:
        search = buildGoogleDocSearchURL(browser, site, filetype)
        isNextPage = True
        while isNextPage == True:
            scrape = viewPage(browser, search)
            grabLinks(filetype, scrape, fileListTmp)
            nextPage = beatifulSoupNextLink(scrape)
            if nextPage == None:
                isNextPage = False
            else:
                search = nextPage

def processLinksForFiles(browser,linkListTmp,userListTmp,softwareListTmp):
    for link in tqdm.tqdm(linkListTmp):
        try:
            fileName = downloadPage(browser, link)
            getMetaData(fileName, userListTmp, softwareListTmp)
            os.remove(fileName)
        except:
            continue

def googleFileFinder(site, fileTypeList):
    waitBanner()
    urllib2Browser = urllib2BrowserBuild()
    fileList = []
    typeList = fileTypeList
    softwareList = []
    userList = []

    discoverLinksForFiles(urllib2Browser,fileList,typeList)

    links = list(set(fileList))
    print "\r\n[*] Discovered Links: \r\n"
    for link in links:
        print "\t[+]: " + link
    print "\r\n"

    processLinksForFiles(urllib2Browser,links,userList,softwareList)

    result = list(set(userList))
    print "[*]Document Usernames\Emails: "
    for user in result:
        print "\t" + user

    result = list(set(softwareList))
    print "\r\n[*]Software: "
    for software in result:
        print "\t" + strip_non_ascii(software)



def dataToFile(data):
    curDate = time.strftime("%Y-%m-%d")
    filename = site + "-" + curDate + "-track.txt"
    f = open(filename, 'a')
    f.write(data)
    f.write("**** Track ****\r\n")
    f.close()


'''
definitions for email specific search
'''


def beatifulSoupCacheLink(scrape, linkList):
    findHTTP = re.compile('^http://webcache.googleusercontent.com.+')
    soupy = BeautifulSoup(scrape)
    cacheLinks = soupy.findAll("a", {"class": "fl"})
    for link in cacheLinks:
        link2 = link['href'] + "&strip=1"
        if findHTTP.findall(link2):
            linkList.append(link2)


def beatifulSoupActiveLink(scrape, linkList):
    findHTTP = re.compile('(http.+)')
    soupy = BeautifulSoup(scrape)
    links = soupy.findAll("h3", {"class": "r"})
    noDocs_regex = re.compile('(.+(\.pdf|\.doc|\.docx))')
    # noGoogleBooks = re.compile('books\.google\.com')
    for link in links:
        link2 = link.find("a")['href']
        if findHTTP.findall(link2):
            if not noDocs_regex.findall(link2):
                linkList.append(link2)
                #    if not noGoogleBooks.findall(link2):


def getEmail(scrape, emaillist, site):
    email_regex = re.compile('(\w+[.|\w]*@%s)' % site)
    email2_regex = re.compile('(\w+[.][.]*@%s)' % site)
    emails = email_regex.findall(scrape)
    if emails:
        for email in emails:
            if not email2_regex.findall(email):
                emaillist.append(email.lower())


def buildGoogleSpecifcSearchURL(browser, site):
    searchURL = 'https://www.google.com/search?q="' + site + '"&num=100'
    openGoogle = browser.open(searchURL)
    response = openGoogle.geturl()
    return response


def discoverLinksForEmails(browser,search,linkListTmp):
    isNextPage = True
    while isNextPage == True:
        scrape = viewPage(browser, search)

        if cache:
            beatifulSoupCacheLink(scrape, linkListTmp)
        else:
            beatifulSoupActiveLink(scrape, linkListTmp)
        nextPage = beatifulSoupNextLink(scrape)
        if nextPage == None:
            isNextPage = False
        else:
            search = nextPage

def processLinksForEmails(browser,emailListTmp,linkListTmp):
    for link in tqdm.tqdm(linkListTmp):
        try:
            scrape = viewPage(browser, link)
            getEmail(scrape, emailListTmp, site)
        except:
            continue


def googleEmailFinder(site):
    waitBanner()
    urllib2Browser = urllib2BrowserBuild()
    linkList = []
    emailList = []
    searchlink = buildGoogleSpecifcSearchURL(urllib2Browser, site)

    discoverLinksForEmails(urllib2Browser,searchlink,linkList)

    links = list(set(linkList))
    print "\r\n[*] Discovered Links (%d): \r\n" % len(links)
    for link in links:
        print "\t[+]: " + str(link)

    processLinksForEmails(urllib2Browser,emailList,links)

    emails = list(set(emailList))
    print "\r\n[*]Emails Discovered (%d): " % len(emails)
    for email in emails:
        print "\t" + email



def dnslookupHT(browser, site):

    htLink = 'http://api.hackertarget.com/hostsearch/?q=' + site
    openHT = browser.open(htLink)
    dnsDataRaw = openHT.read()

    dnsData = dnsDataRaw.replace(',', ':').split('\n')

    print "[+] DNS Host Records (%d):" % len(dnsData)
    for record in dnsData:
        print "\t" + record

    print bcolors.BOLD + bcolors.Red + "(DNS host records provided by HackerTarget.com)" + bcolors.ENDC


def hackerTargetDNS(site):
    urllib2Browser = urllib2BrowserBuild()
    dnslookupHT(urllib2Browser, site)


def zoneTransferHT(browser, site):

    htLink = 'http://api.hackertarget.com/zonetransfer/?q=' + site
    openHT = browser.open(htLink)
    zoneTransferRaw = openHT.read()

    # htmlData('<h3>Zone Transfer</h3>'+zoneTransferRaw)

    print "[+] Zone Transfer Results:"
    print zoneTransferRaw

    print bcolors.BOLD + bcolors.Red + "(Zone Transfer provided by HackerTarget.com)" + bcolors.ENDC


def hackerTargetZone(site):
    urllib2Browser = urllib2BrowserBuild()
    zoneTransferHT(urllib2Browser, site)


def emailAndDocumentSearch(site, fileTypeList):
    waitBanner()
    urllib2Browser = urllib2BrowserBuild()
    linkList = []
    emailList = []
    fileList = []
    typeList = fileTypeList
    softwareList = []
    userList = []

    searchlink = buildGoogleSpecifcSearchURL(urllib2Browser, site)

    discoverLinksForEmails(urllib2Browser,searchlink,linkList)
    discoverLinksForFiles(urllib2Browser,fileList,typeList)


    links = list(set(linkList + fileList))
    print "\r\n[*] Discovered Links (%d): \r\n" % len(links)
    for link in links:
        print "\t[+]: " + str(link)

    print bcolors.BOLD + bcolors.Yellow + "\r\n[#] Processing Email Links: \r\n" + bcolors.ENDC
    processLinksForEmails(urllib2Browser,emailList,list(set(linkList)))

    print bcolors.BOLD + bcolors.Yellow + "\r\n[#] Processing File Links: \r\n" + bcolors.ENDC
    processLinksForFiles(urllib2Browser,list(set(fileList)),userList,softwareList)

    emails = list(set(emailList))
    print "\r\n[*]Emails Discovered (%d): " % len(emails)
    for email in emails:
        print "\t" + email

    result = list(set(userList))
    print "\r\n[*]Document Usernames\Emails: "
    for user in result:
        print "\t" + user

    result = list(set(softwareList))
    print "\r\n[*]Software: "
    for software in result:
        print "\t" + strip_non_ascii(software)

    print "\r\n"
    hackerTargetDNS(site)


def main():
    if len(sys.argv) < 2:
        parser.print_help()
        exampleUsage()
    if doc:
        googleFileFinder(site, fileTypeList)
    if emailSearch:
        googleEmailFinder(site)
    if dnslookup:
        waitBanner()
        hackerTargetDNS(site)
    if zoneTransfer:
        waitBanner()
        hackerTargetZone(site)
    if everything:
        emailAndDocumentSearch(site, fileTypeList)

if __name__ == "__main__":
    main()
