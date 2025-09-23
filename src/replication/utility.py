
import re
pattern = re.compile('<.*?>')

def cleanhtml(raw_html):
  cleantext = re.sub(pattern, '', raw_html)
  return cleantext


def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','')

def stringToList(string):
    #Deal with square brackets
    string = string.replace('[','').replace(']','')
    return string.split(',')