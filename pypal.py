import sys,os
import pandas as pd
import regex as re
import argparse

class bcolors:

    # Colors
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

    # Enhancers
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

asciiBanner = \
"\n      ____        ____        __   " \
"\n     / __ \__  __/ __ \____ _/ /   " \
"\n    / /_/ / / / / /_/ / __ `/ /    " \
"\n   / ____/ /_/ / ____/ /_/ / /     " \
"\n  /_/    \__, /_/    \__,_/_/      " \
"\n        /____/                     " \
"\n " \
"\n\r\n"

def banner():
    print(bcolors.Green + asciiBanner + bcolors.ENDC)

def exampleUsage():
    print(bcolors.BOLD + bcolors.Green + "\r\n[*]Usage Explained:" + bcolors.ENDC)
    print(bcolors.BOLD + bcolors.Yellow + "\t python3 pypal.py -in passfile.txt -out analyzed.csv" + bcolors.ENDC)

parser = argparse.ArgumentParser(description=banner())
parser.add_argument("-in", "--infile", help='Specify password file to analyze in format username:password')
parser.add_argument("-out", "--outfile", help='Specify csv file to output results to, example: analyzed.csv')
args = parser.parse_args()

def main():

    if args.infile is None or args.outfile is None:
        parser.print_help()
        exit()

    analyzeFile = args.infile
    outFile = args.outfile

    complexityTable = {
        'complexity':['loweralpha','upperalpha','numeric','special','loweralphanum','upperalphanum','mixedalpha','loweralphaspecial','upperalphaspecial','specialnum','mixedalphanum','loweralphaspecialnum','mixedalphaspecial','upperalphaspecialnum','mixedalphaspecialnum'],
        'regex':['^[a-z]+$','^[A-Z]+$','^[0-9]+$','^[\p{posix_punct}]+$','^[a-z0-9]+$','^[A-Z0-9]+$','^[a-zA-Z]+$','^[a-z\p{posix_punct}]+$','^[A-Z\p{posix_punct}]+$','^[\p{posix_punct}0-9]+$','^[a-zA-Z0-9]+$','^[a-z\p{posix_punct}0-9]+$','^[A-Za-z\p{posix_punct}]+$','^[A-Z\p{posix_punct}0-9]+$','^[A-Za-z\p{posix_punct}0-9]+$'],
        'count':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}


    resultsTable = {
        'username':[],
        'password':[],
        'length':[],
        'complexity':[]
    }

    compTable = pd.DataFrame(complexityTable)
    resTable = pd.DataFrame(resultsTable)

    def countLength(password):
        length = len(password)
        return length

    print("[+] Working on file {}".format(analyzeFile))

    passFile = open(analyzeFile,"r")

    for line in passFile:
        temp = line.split(':')
        for index, row in compTable.iterrows():
            if(re.match(compTable.at[index,'regex'],temp[1].rstrip('\n'))):
                #compTable.set_value(index,'count',compTable.at[index,'count']+1)
                compTable.at[index, 'count']=compTable.at[index, 'count'] + 1
                line = pd.DataFrame({'username':[temp[0].rstrip('\n')],'password':[temp[1].rstrip('\n')],'length':[int(countLength(temp[1].rstrip('\n')))],'complexity':[compTable.at[index,'complexity']]})
                resTable = resTable.append(line)
                break

    try:
        resTable[['username','password','length','complexity']].to_csv(outFile,index=False)
    except:
        print("\nUnable to write to file: {} \nDo you have it opened? Or is there a handle to it by another process?".format(outFile))
        passFile.close()
        exit(1)

    print("[+] Wrote results to file {}".format(outFile))
    passFile.close()

if __name__ == "__main__":
    main()
