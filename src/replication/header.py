import requests
import base64
import csv
import re
import datetime

import statistics
import numpy as np
from scipy.stats import ttest_ind, mannwhitneyu, wilcoxon
import math
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time


numSigTests = 8

accessToken = 'REDACTED_TOKEN_1'
secondToken = 'REDACTED_TOKEN_2'
firstheaders = {'Authorization': 'token ' + accessToken}
secondHeaders = {'Authorization': 'token ' + secondToken}
headers = firstheaders
#want to cycle through these tokens using fifo queue

headersQueue = [secondHeaders, firstheaders]

def cycleHeaders():
    print("Cycling Headers")
    global headers
    #pop first element and append to end
    headers = headersQueue.pop(0)
    headersQueue.append(headers)



# jsonHeaders = {
#     'Accept': 'application/vnd.github.v3+json',
#     'Authorization': 'token' + accessToken,
# }
# headers = {
#     'Authorization': f'token {accessToken}',
#     'Accept': 'application/vnd.github.v4+json',
# }

#List of repositories
repoListCSVForSG = 'Datasets/OSS4SG-Project-List.csv'
repoListCSVNotForSG = 'Datasets/OSS-Project-List.csv'

cleanRepoListCSVForSG = 'Datasets/OSS4SG-Project-List-Clean.csv'
cleanRepoListCSVNotforSG = 'Datasets/OSS-Project-List-Clean.csv'

additionalRepoListCSVNotForSG = 'Datasets/Additional-OSS-Project-List.csv'

#CSV with all info on OSS4SG repositories
repoInfoCSVForSG = 'Datasets/OSS4SG-Project-Info.csv'
repoInfoCSVNotForSG = 'Datasets/OSS-Project-Info.csv'

cleanRepoInfoForSG = 'Datasets/OSS4SG-Project-Info-Clean.csv'
cleanRepoInfoNotForSG = 'Datasets/OSS-Project-Info-Clean.csv'

activeRepoInfoCSVForSG = 'Datasets/Active-OSS4SG-Project-Info.csv'
activeRepoInfoCSVNotForSG = 'Datasets/Active-OSS-Project-Info.csv'

inactiveRepoInfoCSVForSG = 'Datasets/Inactive-OSS4SG-Project-Info.csv'
inactiveRepoInfoCSVNotForSG = 'Datasets/Inactive-OSS-Project-Info.csv'

filteredRepoInfoCSVForSG = 'Datasets/Filtered-OSS4SG-Project-Info.csv'
filteredRepoInfoCSVNotForSG = 'Datasets/Filtered-OSS-Project-Info.csv'

listTitles = ['Repository', 'SG']

# OSSInfoTitles = ['Repository', 'Description', 'Readme Content', 'Topics', 'Date Started', 'Last Contribution', 'Number of Contributors','Authenticated Contributors',  'Number of Stars', 'Number of Subscribers', 'Contributors', 'Number of One-Time Contributors', 'Number of Authenticated One-Time Contributors']
# #OSS4SGInfoTitles = OSSInfoTitles.append('OSS4SG')
# OSS4SGInfoTitles = ['Repository', 'Description', 'Readme Content', 'Topics', 'Date Started', 'Last Contribution', 'Number of Contributors','Authenticated Contributors',  'Number of Stars', 'Number of Subscribers', 'Contributors', 'Number of One-Time Contributors', 'Number of Authenticated One-Time Contributors', 'SG']

#use same titles as dict keys
OSSInfoTitles = ["name", "description", "topics", "language", "startDate", "lastContribution", "lifespan", "numStars", "numSubscribers", "numForks", "numContributors", "numAuthenticatedContributors", "numAnonymousContributors", "numNotAuthenticatedContributors", "numOneTimeContributors", "numAuthenticatedOneTimeContributors", "numCoreContributors", "contributors", "authenticatedContributors", "coreContributors", "numCommits", "numOpenIssues", "numClosedIssues", "numOpenPullRequests", "numClosedPullRequests", "numMergedPullRequests"]
OSS4SGInfoTitles = ["name", "description", "topics", "language", "startDate", "lastContribution", "lifespan", "numStars", "numSubscribers", "numForks", "numContributors", "numAuthenticatedContributors", "numAnonymousContributors", "numNotAuthenticatedContributors", "numOneTimeContributors", "numAuthenticatedOneTimeContributors", "numCoreContributors", "contributors", "authenticatedContributors", "coreContributors", "numCommits", "numOpenIssues", "numClosedIssues", "numOpenPullRequests", "numClosedPullRequests","numMergedPullRequests", "SDG"]

#index for the different columns in the CSV
#based on titles above

nameIndex = 0
descriptionIndex = 1
topicsIndex = 2
languageIndex = 3
startDateIndex = 4
lastContributionIndex = 5
lifespanIndex = 6
numStarsIndex = 7
numSubscribersIndex = 8
numForksIndex = 9
numContributorsIndex = 10
numAuthenticatedContributorsIndex = 11
numAnonymousContributorsIndex = 12
numNotAuthenticatedContributorsIndex = 13
numOneTimeContributorsIndex = 14
numAuthenticatedOneTimeContributorsIndex = 15
numCoreContributorsIndex = 16
contributorsIndex = 17
authenticatedContributorsIndex = 18
coreContributorsIndex = 19
numCommitsIndex = 20
numOpenIssuesIndex = 21
numClosedIssuesIndex = 22
numOpenPullRequestsIndex = 23
numClosedPullRequestsIndex = 24
numMergedPullRequestsIndex = 25
SDGIndex = 26



deletedRepos = []
pattern = re.compile('<.*?>')
threshold = 0.5

brokenRepos = []

MAXINT = 1000000000

#indices for the different columns in the CSV


