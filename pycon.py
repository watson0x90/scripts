from BeautifulSoup import BeautifulSoup
import mechanize
import random
import re
import subprocess
import os
import tqdm
import argparse
import time
import sys

'''
Dependencies:
    1) exiftool.exe must be placed in the same location as pycon.py
    2) pip install tqdm mechanize beautifulsoup
'''

class bcolors:

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

def banner():

    pyconBanner = "\n       ____" \
"\n      / __ \__  ___________  ____" \
"\n     / /_/ / / / / ___/ __ \/ __ \ "\
"\n    / ____/ /_/ / /__/ /_/ / / / /"\
"\n   /_/    \__, /\___/\____/_/ /_/"\
"\n         /____/ " \
"\n" \
"\n- Because recon doesnt have to suck -\n"

    print bcolors.Green + pyconBanner + bcolors.ENDC

def waitBanner():
    wait = "Discovering... this may take a moment...\r\n"
    print bcolors.BOLD + bcolors.Yellow + wait + bcolors.ENDC

def exampleUsage():

    print bcolors.BOLD + bcolors.Green + "\r\n[*]Usage Explained:" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t\r\n[*]Email search:" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t python pycon.py -email -d example.com" + bcolors.ENDC

    print bcolors.BOLD + bcolors.Yellow + "\r\n[*]Default document search (search for all document types):" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t python pycon.py -doc -d example.com" + bcolors.ENDC

    print bcolors.BOLD + bcolors.Yellow + "\r\n[*]Specific document search:" + bcolors.ENDC
    print bcolors.BOLD + bcolors.Yellow + "\t python pycon.py -doc -d example.com -t doc xlsx\r\n" + bcolors.ENDC


typeList = ["doc","docx","xls","xlsx","pdf","ppt","pptx","pps","ppsx","sxw","sxc","odt","ods","odg","odp","wdp","svg","svgs","indd","rdp","ica"]

parser = argparse.ArgumentParser(description=banner())

parser.add_argument("-doc","--documents",help='Specify document only search for metadata',action="store_true")
parser.add_argument("-email","--emailSearch",help='Specify email only search',action="store_true")

parser.add_argument("-c","--cached",help='Specify to only work with Google Cached Text only links. Might get captcha!',action="store_true")

parser.add_argument("-d","--domain",help='Domain you want to search for documents')
parser.add_argument("-e","--examine",help='Switch to download and examine documents.'
                                          'Documents are stored temporarily in the path the scrip was run from.',action="store_true")
parser.add_argument("-t","--type",nargs='+',help='Specify file types separated by a space (" ") else all default types will be checked.'
                                       'Default types:  doc,docx,xls,xlsx,pdf,ppt,pptx,pps,ppsx,sxw,sxc,odt,ods,odg,odp,wdp,svg,svgs,indd,rdp,ica',default=typeList)

parser.add_argument("-l","--logmeta",help='Log all metadata pulled from files. Saves .txt file in current directory',action="store_true")

args = parser.parse_args()

doc = args.documents
emailSearch = args.emailSearch
site = args.domain
examine = args.examine
fileTypeList = args.type
logData = args.logmeta
cache = args.cached

exiftool = 'exiftool.exe'

def mechBrowserBuild():

    #Basic Building Blocks
    browser = mechanize.Browser()
    cookieJar = mechanize.CookieJar()

    #BrowserOptions
    browser.set_cookiejar(cookieJar)
    browser.addheaders = [('user-agent', pickAgent())]
    browser.set_handle_equiv(True)
    browser.set_handle_redirect(True)
    browser.set_handle_referer(True)
    browser.set_handle_robots(False)
    browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

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

'''
// This is here just in case its needed in the future

def buildGoogleSearchURL(site,type):
    searchURL = "https://www.google.com/search?q=site:"+site+"+filetype:"+type+"&num=100"
    return searchURL
'''

def googleFileSearchForm(browser,site,type):
    mechBrowser = browser
    openGoogle = mechBrowser.open('https://www.google.com')
    openGoogle.read()

    search = 'site:'+site+' filetype:'+type

    mechBrowser.select_form(nr=0)
    mechBrowser.form['q']=search
    mechBrowser.submit()
    response = mechBrowser.geturl()
    return response

def beatifulSoupNextLink(scrape):
    soupy = BeautifulSoup(scrape)
    nextpage = soupy.find("a", {"id": "pnnext"})
    if nextpage is not None:
        return "https://www.google.com"+nextpage['href']
    else:
        return None

def viewPage(browser,url):
    mechBrowser = browser
    page = mechBrowser.open(url)
    page_source = page.read()
    #print page_source
    return page_source

def downloadPage(browser,url):
    mechBrowser = browser
    fileName_regex = re.compile('(?=\w+\.\w{3,4}$).+')
    encodeUrl = url.replace('(','%28').replace(')','%29')
    fileName = fileName_regex.findall(encodeUrl)[0]
    try:
        mechBrowser.retrieve(encodeUrl,str(fileName))
    except:
        print "\r\n[-] Failed on: " + encodeUrl + "\r\n"

    return fileName

def pageItr(source):
    page_regex = re.compile('<div\s+id=\"resultStats\">.*?</div>')
    results = page_regex.findall(source)
    results_regex = re.compile(r'\d+\s\'|[0-9][0-9\,]+')
    itr = results_regex.findall(str(results))
    return round(int(itr[0]), -2)

def grabLinks(filetype,scrape,filelist):

    link_regex = re.compile('href="(.*?)"')
    site_regex = re.compile('^(http|https)://(.*).'+site+'')
    links = link_regex.findall(scrape)
    for link in links:
        if re.match(site_regex, link):
            if link.endswith('.'+filetype):
                filelist.append(link)

def getMetaData(filename,userlist,softwarelist,logToFile):
    basic = '-all ' + filename

    try:
        metaDataRaw = subprocess.check_output(executable=exiftool,args=basic)
        email_regex = re.compile('(\w+[.|\w]*@\w+[.]*\w+)')
        last_regex = re.compile('Last Modified By\s+:\s(.*)\r')
        author_regex = re.compile('Author\s+:\s(.*)\r')
        software_regex = re.compile('Software\s+:\s(.*)\r')
        software_regex2 = re.compile('Producer\s+:\s(.*)\r')
        software_regex3 = re.compile('Application\s+:\s(.*)\r')
        software_regex4 = re.compile('Creator\w+\s+:\s(.*)\r')
        lastModified = last_regex.findall(metaDataRaw)
        if lastModified:
            userlist.extend(lastModified)
        createdBy = author_regex.findall(metaDataRaw)
        if createdBy:
            userlist.extend(createdBy)
        emails = email_regex.findall(metaDataRaw)
        if emails:
            for email in emails:
                userlist.extend(email.lower())
        software = software_regex.findall(metaDataRaw)
        if software:
            softwarelist.extend(software)
        software2 = software_regex2.findall(metaDataRaw)
        if software2:
            softwarelist.extend(software2)
        software3 = software_regex3.findall(metaDataRaw)
        if software3:
            softwarelist.extend(software3)
        software4 = software_regex3.findall(metaDataRaw)
        if software4:
            softwarelist.extend(software4)
        if logToFile:
            dataToFile(metaDataRaw)
    except:
        print "\r\n[-] Metadata Error File: " + filename + "\r\n"


def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)

def googleFileFinder(site,examine,fileTypeList,logToFile):
    waitBanner()
    mechBrowser = mechBrowserBuild()
    fileList = []
    typeList = fileTypeList

    for filetype in typeList:
        search = googleFileSearchForm(mechBrowser,site,filetype)

        isNextPage = True

        while isNextPage == True:
            scrape = viewPage(mechBrowser,search)
            grabLinks(filetype,scrape,fileList)
            nextPage = beatifulSoupNextLink(scrape)
            if nextPage == None:
                isNextPage = False
            else:
                search = nextPage

    result = list(set(fileList))
    print "\r\n[*] Discovered Links: \r\n"
    for link in result:
        print "\t[+]: " +  link

    if examine:
        softwareList = []
        userList = []

        print "\r\n"
        for link in tqdm.tqdm(result):
            try:
                fileName = downloadPage(mechBrowser,link)
                getMetaData(fileName, userList, softwareList, logToFile)
                os.remove(fileName)
            except:
                continue

        result = list(set(userList))
        print "[*]Usernames\Emails: "
        for user in result:
            print "\t" + user

        result = list(set(softwareList))
        print "\r\n[*]Software: "
        for software in result:
            print "\t" + strip_non_ascii(software)

def dataToFile(data):
    curDate = time.strftime("%Y-%m-%d")
    filename = site+"-"+curDate+"-pyrecon.txt"
    f = open(filename,'a')
    f.write(data)
    f.write("**** PYRECON ****\r\n")
    f.close()

'''
definitions for email specific search
'''
def beatifulSoupCacheLink(scrape,linkList):
    findHTTP = re.compile('^http://webcache.googleusercontent.com.+')
    soupy = BeautifulSoup(scrape)
    cacheLinks = soupy.findAll("a", {"class": "fl"})
    for link in cacheLinks:
        link2 = link['href']+"&strip=1"
        if findHTTP.findall(link2):
            linkList.append(link2)

def beatifulSoupActiveLink(scrape,linkList):
    findHTTP = re.compile('(http.+)')
    soupy = BeautifulSoup(scrape)
    links = soupy.findAll("h3", {"class": "r"})
    noDocs_regex = re.compile('(.+(\.pdf|\.doc|\.docx))')
    noGoogleBooks = re.compile('books\.google\.com')
    for link in links:
        link2 = link.find("a")['href']
        if findHTTP.findall(link2):
            if not noDocs_regex.findall(link2):
                if not noGoogleBooks.findall(link2):
                    linkList.append(link2)

def getEmail(scrape,emaillist,site):
    email_regex = re.compile('(\w+[.|\w]*@%s)'%site)
    email2_regex = re.compile('(\w+[.][.]*@%s)'%site)
    emails = email_regex.findall(scrape)
    if emails:
        for email in emails:
            if not email2_regex.findall(email):
                emaillist.append(email.lower())

def buildGoogleSpecifcSearchURL(browser,site):
    mechBrowser = browser
    searchURL = 'https://www.google.com/search?q="'+site+'"&num=100'
    openGoogle = mechBrowser.open(searchURL)
    openGoogle.read()
    response = mechBrowser.geturl()
    return response


def googleEmailFinder(site):
    waitBanner()
    mechBrowser = mechBrowserBuild()
    linkList = []
    emailList = []

    search = buildGoogleSpecifcSearchURL(mechBrowser,site)

    isNextPage = True

    while isNextPage == True:
        scrape = viewPage(mechBrowser,search)

        if cache:
            beatifulSoupCacheLink(scrape,linkList)
        else:
            beatifulSoupActiveLink(scrape,linkList)

        nextPage = beatifulSoupNextLink(scrape)
        if nextPage == None:
            isNextPage = False
        else:
            search = nextPage

    result = list(set(linkList))
    print "\r\n[*] Discovered Links: \r\n"
    for link in result:
        print "\t[+]: " +  str(link)

    for link in tqdm.tqdm(result):
        try:
            scrape = viewPage(mechBrowser,link)
            getEmail(scrape,emailList,site)
            if logData:
                dataToFile(scrape)
        except:
            continue

    emails = list(set(emailList))
    print "\r\n[*]Emails Discovered (%d): "%len(emails)
    for email in emails:
        print "\t" + email

def main():
    if len(sys.argv) < 2:
        parser.print_help()
        exampleUsage()
    if doc:
        googleFileFinder(site,examine,fileTypeList,logData)
    if emailSearch:
        googleEmailFinder(site)

if __name__ == "__main__":
    main()