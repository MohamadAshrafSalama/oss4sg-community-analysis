#This file is for getting the contributors for a repo


import requests
import base64
import csv
import re
import datetime
from datetime import datetime
import random
from repoScraping import clearCSV
from datetime import datetime, timedelta
# from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
from header import *

# accessToken = 'REDACTED_TOKEN_1'
# headers = {'Authorization': 'token ' + accessToken}
# jsonHeaders = {
#     'Accept': 'application/vnd.github.v3+json',
#     'Authorization': 'token' + accessToken,
# }
activeOSS4SGCSV = 'Datasets/Active-OSS4SG-Project-Info.csv'
activeOSSCSV = 'Datasets/Active-OSS-Project-Info.csv'
inactiveOSS4SGCSV = 'Datasets/Inactive-OSS4SG-Project-Info.csv'
inactiveOSSCSV = 'Datasets/Inactive-OSS-Project-Info.csv'
activeReposForStudy = 'Datasets/activeReposForStudy.csv'
inactiveReposForStudy = 'Datasets/inactiveReposForStudy.csv'
OSSReposForStudy = 'Datasets/Filtered-OSS-Project-Info.csv'
OSS4SGReposForStudy = 'Datasets/Filtered-OSS4SG-Project-Info.csv'
testFile = 'Datasets/test.csv'
buffer = 5 #months of inactivity to consider a user inactive

#Cannot get info on contributors to these repos using graphql
# brokenRepos = ["NREL/energyplus", "mozilla/bedrock", "OptiKey/OptiKey","optikey/optikey", "onaio/onadata", "huridocs/uwazi", "kobotoolbox/kobocat", "demarches-simplifiees/demarches-simplifiees.fr", "VOLTTRON/volttron", "scratchfoundation/scratch-vm", "openstates/openstates-scrapers", "Growstuff/growstuff", "http4s/http4s", "WebAssembly/binaryen", "bitcoinbook/bitcoinbook", "EbookFoundation/free-programming-books", "aws/s2n-tls", "heroku/heroku-buildpack-ruby", "presidentbeef/brakeman", "hibernate/hibernate-orm", "OpenEnergyDashboard/OED", "ifmeorg/ifme", "learningequality/kolibri", "rubyforgood/human-essentials", "RefugeRestrooms/refugerestrooms-ios","get-alex/alex", "luke-jr/bfgminer", "dankogai/js-base64", "sfbrigade/adopt-a-drain", "google/blockly", "pwyf/aid-transparency-tracker", "sozialhelden/accessibility-cloud", "coveo/platform-client","zostera/django-bootstrap3","gjtorikian/isBinaryFile","farmOS/farmOS","sindresorhus/maxmin", "heroku/heroku-buildpack-nodejs", "bokeh/bokeh", "instedd/surveda", "public-accountability/littlesis-rails", "coralproject/talk", "code-dot-org/code-dot-org", "instedd/planwise", "ushahidi/platform-client", "code-dot-org/blockly", "splitrb/split"]
brokenRepos = []
originalBrokenRepos = brokenRepos





#Pick 5 OSS4SG repos and 5 OSS repos (only active repos)
def chooseRepos():
    count = 0
    activeOSS4SGRepos = []
    activeOSSRepos = []
    inactiveOSS4SGRepos = []
    inactiveOSSRepos = []
    totalActiveRepos = []
    totalInactiveRepos = []
    with open(activeOSS4SGCSV, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        activeOSS4SGRepos = list(reader)

    with open(activeOSSCSV, 'r',encoding='utf-8') as file:
        reader = csv.reader(file)
        activeOSSRepos = list(reader)

    with open(inactiveOSS4SGCSV, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        inactiveOSS4SGRepos = list(reader)

    with open(inactiveOSSCSV, 'r',encoding='utf-8') as file:
        reader = csv.reader(file)
        inactiveOSSRepos = list(reader)

    #remove first line for titles
    activeOSS4SGRepos = activeOSS4SGRepos[1:]
    activeOSSRepos = activeOSSRepos[1:]
    inactiveOSS4SGRepos = inactiveOSS4SGRepos[1:]
    inactiveOSSRepos = inactiveOSSRepos[1:]


    #Get the number of repos in different ranges
    numActiveReposForSG = len(activeOSS4SGRepos)
    numActiveReposNotForSG = len(activeOSSRepos)
    numInactiveReposForSG = len(inactiveOSS4SGRepos)
    numInactiveReposNotForSG = len(inactiveOSSRepos)

    print("Number of Active OSS4SG Repos: ", numActiveReposForSG)
    print("Number of Active OSS Repos: ", numActiveReposNotForSG)
    print("Number of Inactive OSS4SG Repos: ", numInactiveReposForSG)
    print("Number of Inactive OSS Repos: ", numInactiveReposNotForSG)



    #Get minimum number of contributors from user
    print("Enter the minimum number of authenticated contributors")
    minContributors = int(input())
    

    #Get years active from user
    print("Enter the number of years the repo has been active")
    years = int(input())
    days = years * 365


    #remove all repos that have less than the minimum number of contributors
    activeOSS4SGRepos = [repo for repo in activeOSS4SGRepos if int(repo[6]) >= minContributors and repo[0] not in brokenRepos]
    activeOSSRepos = [repo for repo in activeOSSRepos if int(repo[6]) >= minContributors and repo[0] not in brokenRepos]
    inactiveOSS4SGRepos = [repo for repo in inactiveOSS4SGRepos if int(repo[6]) >= minContributors and repo[0] not in brokenRepos]
    inactiveOSSRepos = [repo for repo in inactiveOSSRepos if int(repo[6]) >= minContributors and repo[0] not in brokenRepos]

    #remove all repos that have been active for less than the given years
    activeOSS4SGRepos = [repo for repo in activeOSS4SGRepos if getActiveTime(repo) >= days and repo[0] not in brokenRepos]
    activeOSSRepos = [repo for repo in activeOSSRepos if getActiveTime(repo) >= days and repo[0] not in brokenRepos]
    inactiveOSS4SGRepos = [repo for repo in inactiveOSS4SGRepos if getActiveTime(repo) >= days and repo[0] not in brokenRepos]
    inactiveOSSRepos = [repo for repo in inactiveOSSRepos if getActiveTime(repo) >= days and repo[0] not in brokenRepos]

    print("Number of active OSS4SG Repos active for ", years, " years: ", len(activeOSS4SGRepos))
    print("Number of active OSS Repos active for ", years, " years: ", len(activeOSSRepos))
    print("Number of inactive OSS4SG Repos active for ", years, " years: ", len(inactiveOSS4SGRepos))
    print("Number of inactive OSS Repos active for ", years, " years: ", len(inactiveOSSRepos))

    #Chose active, inatcive or both
    print("Do you want to choose active, inactive or both? (or cancel) (a/i/b/c)")
    choice = input()




    num = 0
    if choice == 'a' or choice == 'b' or choice == 'i':
        print("How many repos do you want to choose?")
        num = int(input())

    if choice == 'a' or choice == 'b':
        totalActiveRepos = chooseReposFromLists(activeOSS4SGRepos, activeOSSRepos, num)
        clearCSV(activeReposForStudy)
        saveRepoList(totalActiveRepos, activeReposForStudy)

    if choice == 'i' or choice == 'b':
        totalInactiveRepos = chooseReposFromLists(inactiveOSS4SGRepos, inactiveOSSRepos, num)
        clearCSV(inactiveReposForStudy)
        saveRepoList(totalInactiveRepos, inactiveReposForStudy)

    return totalActiveRepos, totalInactiveRepos


def chooseReposFromLists(repoListSG, repoListNotSG, num):
    #Choose 5 random OSS4SG repos and 5 random OSS repos
    randomOSS4SGRepos = random.sample(repoListSG, num)
    randomOSSRepos = random.sample(repoListNotSG, num)
    totalRepos = []
    count = 0

    #Add labels to the list to differentiate between the two (SG vs Not SG)
    print("Random Active OSS4SG Repos: ")
    for repo in randomOSS4SGRepos:
        count += 1
        print("Repo ", count, ": ", repo[0])
        repo.append("SG")
        totalRepos.append((repo[0], 1))

    
    print("\nRandom Active OSS Repos: ")
    for repo in randomOSSRepos:
        count += 1
        print("Repo ", count, ": ", repo[0])
        repo.append("Not SG")
        totalRepos.append((repo[0], 0))


    return totalRepos

def removeBrokenRepos(repoList):
    #Remove any repos that are in the list of broken repos
    #print when a repo is rmeoved
    count = 0
    for repo in repoList[:]:
        if repo[0] in brokenRepos:
            #print("Removing broken repo: ", repo[0])
            repoList.remove(repo)
            count += 1

    
    print("Number of broken repos removed: ", count)
    return repoList

def countReposInRange(repoList, lower, upper):
    count = 0
    for repo in repoList:
        numAuthenticatedContributors = int(repo[6])
        if numAuthenticatedContributors >= lower and numAuthenticatedContributors <= upper:
            if repo[0] not in brokenRepos:
                count += 1


    return count


def saveRepoList(repoList, fileName):
    # Save the list of repositories to a CSV file

    with open(fileName, 'w', newline='',encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Repository", "SG"])
        for repo in repoList:
            writer.writerow(repo)

def loadRepoList(fileName):
    # Read the list of repositories from the CSV file

    repoList = None

    #Make sure file opens correctly
    with open(fileName, 'r',encoding="utf-8") as file:
        
        reader = csv.reader(file)
        repoList = list(reader)

        #skip first line for titles
        repoList = repoList[1:]

    return repoList


def getContributors(repo):
    
    # Make a GET request to fetch repository information
    response = requests.get('https://api.github.com/repos/'+repo, headers=headers)

    contributorList = []
    #oneTimeContributorList = []

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        
        params = {'per_page': 100, 'page': 1, 'anon': 'true'}

        contributorsResponse = requests.get('https://api.github.com/repos/'+repo+'/contributors', headers=headers, params=params)
        if contributorsResponse.status_code == 200:
            contributorsInfo = contributorsResponse.json()


            while 'next' in contributorsResponse.links:
                # Make a GET request for the next page of contributors
                next_page_url = contributorsResponse.links['next']['url']
                contributorsResponse = requests.get(next_page_url, headers=headers)
                
                # Check if the request was successful
                if contributorsResponse.status_code == 200:
                    # Parse the JSON response
                    additional_contributors = contributorsResponse.json()
                    
                    # Add contributors from the next page to the list
                    contributorsInfo.extend(additional_contributors)
                else:
                    print(f"Failed to fetch contributors (next page). Status code: {contributorsResponse.status_code}")
                    print("Rate Limit Remaining: ", contributorsResponse.headers['X-RateLimit-Remaining'])
                    print("Rate Limit Reset: ", datetime.fromtimestamp(contributorsResponse.headers['X-RateLimit-Reset']))
                    break

            for contributor in contributorsInfo:
                #get rid of bots
                if contributor['type'] != 'Bot' and contributor['type'] != 'Anonymous':
                    contributorList.append((contributor['login'], contributor['contributions']))

                # if contributor['contributions'] == 1:
                #     oneTimeContributorList.append((contributor['login'], contributor['contributions']))

            numContributors = len(contributorsInfo)

        else:
            print(f"Failed to fetch contributors. Status code: {contributorsResponse.status_code}")
            print("Rate Limit Remaining: ", contributorsResponse.headers['X-RateLimit-Remaining'])
            print("Rate Limit Reset: ", datetime.fromtimestamp(contributorsResponse.headers['X-RateLimit-Reset']))


    else:
        print(f"Failed to fetch repository information. Status code: {response.status_code}")
        print("Rate Limit Remaining: ", response.headers['X-RateLimit-Remaining'])
        print("Rate Limit Reset: ", datetime.fromtimestamp(response.headers['X-RateLimit-Reset']))

    return contributorList

def getDefaultBranch(repo):
    url = f"https://api.github.com/repos/{repo}"
    #headers = {"Authorization": f"Bearer {accessToken}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        repo_info = response.json()
        return repo_info['default_branch']
    else:
        print("Failed to fetch repository information with code {}. {}".format(response.status_code, response.text))
        return None

def checkRateLimit():
    # Check the rate limit for the GitHub API
    response = requests.get('https://api.github.com/rate_limit', headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        rateLimit = data['rate']['limit']
        remainingRequests = data['rate']['remaining']
        resetTime = datetime.fromtimestamp(data['rate']['reset'])
        #print(f"Rate limit: {rateLimit}")
        print(f"Remaining requests: {remainingRequests}")
        print(f"Reset time: {resetTime}")

        return rateLimit, remainingRequests, resetTime
    else:
        print(f"Failed to fetch rate limit. Status code: {response.status_code}")

        return None, None, None


def getUserInfoFromGithubGraphQL(user, repo, branchName, quartileDates):

    #rateLimit, remainingRequests, ResetTime = checkRateLimit()
    # if remainingRequests < 10:
    #     print("Switching headers/token")
    #     cycleHeaders()

    #rateLimit, remainingRequests, ResetTime = checkRateLimit()
    # if remainingRequests < 10:
    #     sleepTime = ResetTime - datetime.now()
    #     print(f"Sleeping for {sleepTime} seconds")
    #     time.sleep(sleepTime.total_seconds())

    # if user is anonymous, return None
    if user == 'anonymous':
        return None

    #print("Getting info for user ", user, " in repo ", repo)
    userName = user
    repoName = repo.split('/')[1]
    owner = repo.split('/')[0]
    active = False
    #need to make datetime type
    firstCommitDate = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    firstCommitDate = datetime.strptime(firstCommitDate, "%Y-%m-%dT%H:%M:%SZ")
    lastCommitDate = "1970-01-01T00:00:00Z"
    lastCommitDate = datetime.strptime(lastCommitDate, "%Y-%m-%dT%H:%M:%SZ")
    commitsWindows = [0,0,0,0]
    issuesWindows = [0,0,0,0]
    pullRequestsWindows = [0,0,0,0]
    totalCommits = 0
    totalIssues = 0
    totalPullRequests = 0

    

    graphqlEndpoint = 'https://api.github.com/graphql'

    userIdQuery = '''
    query {
      user(login: "USERNAME") {
        id
      }
      rateLimit {
        limit
        cost
        remaining
        resetAt
      }
    }
    '''

    userIdQuery = userIdQuery.replace('USERNAME', userName)
    print("Getting user ID for user: ", userName)
    response = requests.post(graphqlEndpoint, json={'query': userIdQuery}, headers=headers)

    if response.status_code == 200:
        userData = response.json()
        #print("User Data: ", userData)

        if 'errors' in userData:
            print("Error: ", userData)
            print("response: ", response)
            print("status code: ", response.status_code)
            return None
        

        
        rateLimit = userData['data']['rateLimit']['limit']
        remainingRequests = userData['data']['rateLimit']['remaining']

        print(f"Remaining requests: {remainingRequests}")

        if remainingRequests < 10:
            print("Switching headers/token")
            cycleHeaders()

        userId = userData['data']['user']['id']




        print("Getting commits for user: ", userName)
        commitsQuery = '''
query($owner: String!, $repoName: String!, $userId: ID!, $branchName: String!, $after: String) {
  repository(owner: $owner, name: $repoName) {
    object(expression: $branchName) {
      ... on Commit {
        history(author: {id: $userId}, first: 100, after: $after) {
          totalCount
          pageInfo {
            endCursor
            hasNextPage
          }
          nodes {
            committedDate
            author {
              user {
                login
              }
            }
          }
        }
      }
    }
  }
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
}
'''

        commitsVariables = {
            "owner": owner,
            "repoName": repoName,
            "userId": userId,
            "branchName": branchName,
            "after": None

        }

        hasNextPage = True
        nextPageCursor = None

        while hasNextPage:
            #print("Looped")
            if nextPageCursor:
                commitsVariables['after'] = nextPageCursor


            commitResponse = requests.post(graphqlEndpoint, json={'query': commitsQuery, 'variables': commitsVariables}, headers=headers)

            if commitResponse.status_code == 200:
                json = commitResponse.json()
                if json:
                    
                    if 'errors' in json:
                        print("Error: ", json)
                        print("response: ", commitResponse)
                        print("status code: ", commitResponse.status_code)
                        #most recent error:
                        # Sim4n6  in repo  dimagi/commcare-hq
                        #Error:  {'errors': [{'message': 'Something went wrong while executing your query. Please include `CDC6:B6718:1DC5676:38BEC17:66994E53` when reporting this issue.'}]}
                        return None

                    
                    history = json['data']['repository']['object']['history']

                    
                    #get total number of commits
                    totalCommits = history['totalCount']

                    hasNextPage = history['pageInfo']['hasNextPage']
                    nextPageCursor = history['pageInfo']['endCursor']


                    commitDates = []

                    for commit in history['nodes']:
                        commitDate = commit['committedDate']
                        commitDates.append(commitDate)
                        #authorLogin = commit['author']['user']['login']
                        #print(f"Contribution Date: {committedDate}, Author: {authorLogin}")

                        commitDate = re.sub(r"T|Z", " ", commitDate)
                        commitDate = commitDate[:-4]
                        commitDate = datetime.strptime(commitDate, "%Y-%m-%d %H:%M")

                        if commitDate < quartileDates[0]:
                            commitsWindows[0] += 1
                        elif commitDate < quartileDates[1]:
                            commitsWindows[1] += 1
                        elif commitDate < quartileDates[2]:
                            commitsWindows[2] += 1
                        else:
                            commitsWindows[3] += 1
                    
                        # print("Commit Date: ", commitDate)
                        # print("First Commit Date: ", firstCommitDate)
                        # print("Last Commit Date: ", lastCommitDate)


                        if commitDate < firstCommitDate:
                            firstCommitDate = commitDate
                        
                        if commitDate > lastCommitDate:
                            lastCommitDate = commitDate


                else:
                    print("Json is none for {userName} in {repoName}")
                    print("response: ", commitResponse)
                    print("response.text: ", commitResponse.text)
                    print("response.status_code: ", commitResponse.status_code())
                    firstCommitDate = None
                    lastCommitDate = None
                    active = False               

            else:
                print(f"Failed to fetch contribution history for {userName} in {repoName}. Status code: {commitResponse.status_code}")
                print("response: ", commitResponse)
                #get rate limit remaining
                rateLimit, remainingRequests, ResetTime = checkRateLimit()

                firstCommitDate = None
                lastCommitDate = None
                active = False

        print("Getting issues for user: ", userName)

        issuesQuery = '''
        query($owner: String!, $repoName: String!, $authorLogin: String!, $after: String) {
        repository(owner: $owner, name: $repoName) {
            issues(first: 100, filterBy: {createdBy: $authorLogin}, after: $after) {
            totalCount
            pageInfo {
                endCursor
                hasNextPage
            }
            nodes {
                createdAt
                author {
                login
                }
            }
            }
        }
        rateLimit {
            limit
            cost
            remaining
            resetAt
        }
        }
        '''


        issuesVariables = {
            "owner": owner,
            "repoName": repoName,
            "authorLogin": userName,
            "after": None
        }

        hasNextPage = True
        nextPageCursor = None

        while hasNextPage:

            if nextPageCursor:
                issuesVariables['after'] = nextPageCursor

            issueResponse = requests.post(graphqlEndpoint, json={'query': issuesQuery, 'variables': issuesVariables}, headers=headers)
            if issueResponse.status_code == 200:
                json = issueResponse.json()
                if json:

                    if 'errors' in json:
                        print("Error: ", json)
                        return None


                    issues = json['data']['repository']['issues']
                    #print("Issues: ", issues)
                    totalIssues = issues['totalCount']

                    hasNextPage = issues['pageInfo']['hasNextPage']
                    nextPageCursor = issues['pageInfo']['endCursor']
                    
                    issueDates = []
                    for issue in issues['nodes']:
                        createdAt = issue['createdAt']
                        issueDates.append(createdAt)

                        #convert committed date to datetime
                        createdAt = re.sub(r"T|Z", " ", createdAt)
                        createdAt = createdAt[:-4]
                        createdAt = datetime.strptime(createdAt, "%Y-%m-%d %H:%M")

                        #find which of the windows the commit is in
                        if createdAt < quartileDates[0]:
                            issuesWindows[0] += 1
                        elif createdAt < quartileDates[1]:
                            issuesWindows[1] += 1
                        elif createdAt < quartileDates[2]:
                            issuesWindows[2] += 1
                        else:
                            issuesWindows[3] += 1



                    if issueDates:
                        firstIssueDate = min(issueDates)
                        lastIssueDate = max(issueDates)
                    else:
                        firstIssueDate = None
                        lastIssueDate = None
                else:
                    print("No issues found")
                    firstIssueDate = None
                    lastIssueDate = None

            else:
                print(f"Failed to fetch issue history for {userName} in {repoName}. Status code: {response.status_code}")
                firstIssueDate = None
                lastIssueDate = None
    

        print("Getting pull requests for user: ", userName)

        pullRequestsQuery = '''
query($owner: String!, $repoName: String!, $after: String) {
  repository(owner: $owner, name: $repoName) {
    pullRequests(first: 100, after: $after) {
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        createdAt
        author {
          login
        }
      }
    }
  }
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
}
'''

        pullRequestsVariables = {
            "owner": owner,
            "repoName": repoName,
            "after": None
        }

        hasNextPage = True
        nextPageCursor = None

        while hasNextPage:

            if nextPageCursor:
                pullRequestsVariables['after'] = nextPageCursor
            


            pullRequestResponse = requests.post(graphqlEndpoint, json={'query': pullRequestsQuery, 'variables': pullRequestsVariables}, headers=headers)
            if pullRequestResponse.status_code == 200:
                json = pullRequestResponse.json()
                if json:
                    #print("Data: ", data)


                    if 'errors' in json:
                        print("Error: ", json)
                        return None

                    pullRequests = json['data']['repository']['pullRequests']

                    #totalPullRequests = pullRequests['totalCount']

                    hasNextPage = history['pageInfo']['hasNextPage']
                    nextPageCursor = history['pageInfo']['endCursor']

                    pullRequestDates = []
                    for pullRequest in pullRequests['nodes']:

                        #couldn't filter by username in request, filter them out now

                        #this failed because pullrequest['author'] is None, why?
                        if pullRequest['author'] == None:
                            print("Author is None")
                            print("Pull Request: ", pullRequest)
                            continue

                        if pullRequest['author']['login'] != userName:
                            # print("Author is not the same as user")
                            # print("username: ", userName)
                            # print("author: ", pullRequest['author']['login'])

                            continue
                        # else:
                        #     print("Author is the same as user")
                        #     print("username: ", userName)
                        #     print("author: ", pullRequest['author']['login'])


                        createdAt = pullRequest['createdAt']
                        pullRequestDates.append(createdAt)

                        #convert committed date to datetime
                        createdAt = re.sub(r"T|Z", " ", createdAt)
                        createdAt = createdAt[:-4]
                        createdAt = datetime.strptime(createdAt, "%Y-%m-%d %H:%M")

                        #find which of the windows the commit is in
                        if createdAt < quartileDates[0]:
                            pullRequestsWindows[0] += 1
                        elif createdAt < quartileDates[1]:
                            pullRequestsWindows[1] += 1
                        elif createdAt < quartileDates[2]:
                            pullRequestsWindows[2] += 1
                        else:
                            pullRequestsWindows[3] += 1



                    if pullRequestDates:
                        firstPullRequestDate = min(pullRequestDates)
                        lastPullRequestDate = max(pullRequestDates)
                    else:
                        firstPullRequestDate = None
                        lastPullRequestDate = None
                else:
                    print("No pull requests found")
                    firstPullRequestDate = None
                    lastPullRequestDate = None
            else:
                print(f"Failed to fetch pull request history for {userName} in {repoName}. Status code: {response.status_code}")
                firstPullRequestDate = None
                lastPullRequestDate = None



            fiveMonthsAgo = datetime.now() - timedelta(days=150)
            if lastCommitDate > fiveMonthsAgo:
                active = True
            else:
                active = False
        
        print("-"*50)
        print("User: ", userName)
        print("Total Commits: ", totalCommits)
        print("Total Issues: ", totalIssues)
        print("First Commit Date: ", firstCommitDate)
        print("Last Commit Date: ", lastCommitDate)
        print("Active: ", active)
        print("Commits Windows: ", commitsWindows)
        print("Issues Windows: ", issuesWindows)
        print("Pull Requests Windows: ", pullRequestsWindows)
        print("-"*50)
        print("\n")
        return firstCommitDate, lastCommitDate, active, commitsWindows, issuesWindows, pullRequestsWindows

        #RETURN DOWN HERE
    else:
        print(f"Failed to fetch user ID for {userName}. Status code: {response.status_code}")
        return None


def analyzeWindow(userList, startDate, endDate):

    #print("Analyzing window")

    # print("Window Size: ", windowSize)
    # print("Window Offset: ", windowOffset)


    #windowsize is in years and offset is in days
    joinCount = 0
    leaveCount = 0
    activeCount = 0

    #print("Window: ", startDate, " to ", endDate)

    for user in userList:
        firstContribution = user[2]
        lastContribution = user[3]
        if firstContribution and lastContribution:
            firstContribution = datetime.strptime(firstContribution, "%Y-%m-%d %H:%M:%S")
            lastContribution = datetime.strptime(lastContribution, "%Y-%m-%d %H:%M:%S")

            if firstContribution < endDate and firstContribution > startDate:
                joinCount += 1

            #if their last contribution is in the window
            if lastContribution < endDate and lastContribution > startDate:
                #make sure that it isnt in the last 5 months
                fiveMonthsAgo = datetime.now() - timedelta(days=150)
                if lastContribution < fiveMonthsAgo:
                    leaveCount += 1



            #if last contribution is in the last 5 months, can't count it as when they left, so use now instead
            fiveMonthsAgo = datetime.now() - timedelta(days=150)
            if lastContribution > fiveMonthsAgo:
                lastContribution = datetime.now()
            
            #check if user is active in this window
            #SHould this be two values? active at start, active at end? maybe average them?

            #if user joined before or during this window and if they l;eft after or during this window
            if firstContribution < endDate and lastContribution > startDate:
            #if firstContribution < startDate and lastContribution > endDate:
                activeCount += 1
                    

            #     print("User: ", user[0], " is active in this window")
            # else:
            #     print("User: ", user[0], " is not active in this window")


    return joinCount, leaveCount, activeCount



#gets how long a rpeo has been active
def getActiveTime(repo):
    startDate = repo[4]
    startDate = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%SZ')
    lastContribution = repo[5]
    lastContribution = datetime.strptime(lastContribution, '%Y-%m-%dT%H:%M:%SZ')
    timeActive = lastContribution - startDate
    timeActive = timeActive.days
    return timeActive


#This isn't working quite right
def getMissingRepos(repoList, quartiles):

    count = 0
    total = len(repoList)
        #Fill in missing repo (any repo without a contributors file)
    for repo in repoList:
        #print(repo)
        #print("Getting info for repo ", repo[0], " (", count, "/", total, ")")
        repoURL = repo[0]
        repoName = repoURL.split('/')[1]
        fileLocation = 'Datasets/ContributorInfo/'+repoName+'Contributors.csv'

        startDate = repo[4]
        startDate = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%SZ')


        #Get quartile dates
        quartileDates = []
        for quartile in quartiles:
            quartileDays = quartile * 365
            quartileDate = startDate + timedelta(days=quartileDays)
            quartileDates.append(quartileDate)
        
        

        try:
            with open(fileLocation, 'r',encoding='utf-8') as file:
                reader = csv.reader(file)
                userList = list(reader)
        except:
            print("No file found for repo: ", repoURL, " (", count, "/", total, ")")
            print("Getting contributors")
            userList = getContributors(repoURL)
            branchName = getDefaultBranch(repoURL)

            with open(fileLocation, 'w', newline='',encoding='utf-8') as file:
                writer = csv.writer(file)
                writer
                writer.writerow(["User", "Number of Contributions","First Contribution", "Last Contribution", "Active", "Commits First Window", "Commits Second Window", "Commits Third Window", "Commits Fourth Window", "Issues First Window", "Issues Second Window", "Issues Third Window", "Issues Fourth Window", "Pull Requests First Window", "Pull Requests Second Window", "Pull Requests Third Window", "Pull Requests Fourth Window"])

                for user in userList:
                    userName = user[0]
                    
                    print("Getting info for user ", userName, " in repo ", repoURL)
                    userInfo = getUserInfoFromGithubGraphQL(userName, repoURL, branchName, quartileDates)
                    if userInfo:
                        name = user[0]
                        contributions = user[1]
                        firstContribution = userInfo[0]
                        lastContribution = userInfo[1]
                        active = userInfo[2]
                        commitWindows = userInfo[3]
                        issueWindows = userInfo[4]
                        pullRequestWindows = userInfo[5]
                        commitsFirstWindow = commitWindows[0]
                        commitsSecondWindow = commitWindows[1]
                        commitsThirdWindow = commitWindows[2]
                        commitsFourthWindow = commitWindows[3]
                        issuesFirstWindow = issueWindows[0]
                        issuesSecondWindow = issueWindows[1]
                        issuesThirdWindow = issueWindows[2]
                        issuesFourthWindow = issueWindows[3]
                        pullRequestsFirstWindow = pullRequestWindows[0]
                        pullRequestsSecondWindow = pullRequestWindows[1]
                        pullRequestsThirdWindow = pullRequestWindows[2]
                        pullRequestsFourthWindow = pullRequestWindows[3]
                        writer.writerow([name, contributions, firstContribution, lastContribution, active, commitsFirstWindow, commitsSecondWindow, commitsThirdWindow, commitsFourthWindow, issuesFirstWindow, issuesSecondWindow, issuesThirdWindow, issuesFourthWindow, pullRequestsFirstWindow, pullRequestsSecondWindow, pullRequestsThirdWindow, pullRequestsFourthWindow])


#Goes through all repos and gets all contributors
#should maybe rename this, unclear
def getAllRepos(repoList, quartiles):
    repoCount = 0
    for repo in repoList:
        repoCount += 1
        print("Getting info for repo ", repo[0], " (", repoCount, "/", len(repoList), ")")

        
        #Should do this differently (using list from before, not using contributions)
        numOneTimeContributors = 0
        repoURL = repo[0]
        print("Repo: ", repoURL, " (", repoCount, "/", len(repoList), ")")
        repoName = repoURL.split('/')[1]

        startDate = repo[4]
        startDate = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%SZ')
        lastContribution = repo[5]
        lastContribution = datetime.strptime(lastContribution, '%Y-%m-%dT%H:%M:%SZ')

        branchName = getDefaultBranch(repoURL)
        userList = getContributors(repoURL)



        #Get quartile dates
        quartileDates = []
        for quartile in quartiles:
            quartileDays = quartile * 365
            quartileDate = startDate + timedelta(days=quartileDays)
            quartileDates.append(quartileDate)

        print("quartileDates: ", quartileDates)

        fileLocation = 'Datasets/ContributorInfo/'+repoName+'Contributors.csv'

        with open(fileLocation, 'w', newline='',encoding='utf-8') as file:
            writer = csv.writer(file)


            #There is no fourth stage really
            titles = ["User", "Number of Contributions","First Contribution", "Last Contribution", "Active", "Stage", "Commits First Stage", "Commits Second Stage", "Commits Third Stage", "Commits Fourth Stage", "Issues First Stage", "Issues Second Stage", "Issues Third Stage", "Issues Fourth Stage", "Pull Requests First Stage", "Pull Requests Second Stage", "Pull Requests Third Stage", "Pull Requests Fourth Stage"]


            writer.writerow(titles)
            #writer.writerow(["User", "Number of Contributions","First Contribution", "Last Contribution", "Active"])

            failCount = 0
            failStreak = 0
            userCount = 0
            for user in userList:
                userName = user[0]
                userCount += 1
                #userInfo = getUserInfoFromGithub(user[0], repo)
                print("Getting info for user ", userName, " in repo ", repoURL, " (", userCount, "/", len(userList), ")")
                userInfo = getUserInfoFromGithubGraphQL(userName, repoURL, branchName, quartileDates)
                #print(userInfo)
                if userInfo == (None, None, None) or userInfo == None:
                    failCount += 1
                    failStreak += 1
                elif userInfo:
                    name = user[0]
                    contributions = user[1]
                    firstContribution = userInfo[0]
                    lastContribution = userInfo[1]
                    active = userInfo[2]
                    commitWindows = userInfo[3]
                    issueWindows = userInfo[4]
                    pullRequestWindows = userInfo[5]
                    if commitWindows:
                        commitsFirstWindow = commitWindows[0]
                        commitsSecondWindow = commitWindows[1]
                        commitsThirdWindow = commitWindows[2]
                        commitsFourthWindow = commitWindows[3]
                    else:
                        print("Commit windows returned None")
                        commitsFirstWindow = None
                        commitsSecondWindow = None
                        commitsThirdWindow = None
                        commitsFourthWindow = None

                    if issueWindows:
                        issuesFirstWindow = issueWindows[0]
                        issuesSecondWindow = issueWindows[1]
                        issuesThirdWindow = issueWindows[2]
                        issuesFourthWindow = issueWindows[3]
                    else:
                        print("Issue windows returned None")
                        issuesFirstWindow = None
                        issuesSecondWindow = None
                        issuesThirdWindow = None
                        issuesFourthWindow = None

                    if pullRequestWindows:
                        pullRequestsFirstWindow = pullRequestWindows[0]
                        pullRequestsSecondWindow = pullRequestWindows[1]
                        pullRequestsThirdWindow = pullRequestWindows[2]
                        pullRequestsFourthWindow = pullRequestWindows[3]
                    else:
                        print("Pull Request windows returned None")
                        pullRequestsFirstWindow = None
                        pullRequestsSecondWindow = None
                        pullRequestsThirdWindow = None
                        pullRequestsFourthWindow = None



                    writer.writerow([name, contributions, firstContribution, lastContribution, active, commitsFirstWindow, commitsSecondWindow, commitsThirdWindow, commitsFourthWindow, issuesFirstWindow, issuesSecondWindow, issuesThirdWindow, issuesFourthWindow, pullRequestsFirstWindow, pullRequestsSecondWindow, pullRequestsThirdWindow, pullRequestsFourthWindow])

                    failStreak = 0
                # if user[1] == 1:
                #     numOneTimeContributors += 1


                #if too many failures in a row, repo is broken
                if failStreak > 10:
                    print("Too many failures, breaking")
                    #append to list of broken repos
                    if repoURL not in brokenRepos:
                        brokenRepos.append(repoURL)
                    failStreak = 0

                    break

    if len(brokenRepos) != 0:
        print("Number of broken repos: ", len(brokenRepos))
    if brokenRepos != originalBrokenRepos:
        print("Broken Repos: ", brokenRepos)



def getInfoForPlots(repoList, windowSize, startOffset, endOffset, includeOneTime=True, onlyCore = False):

    allRepoRatios = []
    allRepoDifferences = []
    allLeaves = []
    allJoins = []
    allJoinRates = []
    allLeaveRates = []
    averageJoinRates = []
    averageLeaveRates = []
    allActivePerWindow = []

    brokenCount = 0

    startOffsetDays = startOffset*365
    endOffsetDays = endOffset*365
    windowSizeDays = windowSize*365

    needBufferCount = 0

    hasStage = 0
    noStage = 0

    hasStageSG = 0
    noStageSG = 0

    hasStageNonSG = 0
    noStageNonSG = 0

    totalContributors = 0
    totalOneTimeContributors = 0
    TotalCoreContributors = 0

    totalSGContributors = 0
    totalNonSGContributors = 0
    totalSGOneTimeContributors = 0
    totalNonSGOneTimeContributors = 0
    totalSGCoreContributors = 0
    totalNonSGCoreContributors = 0
    
    numRepos = len(repoList)
    numSGRepos = 0
    numNonSGRepos = 0

    print("Number of Repos to get info for: ", numRepos)

    for repo in repoList:
        #print("Getting info for repo ", repo[0], " (", repoList.index(repo)+1, "/", numRepos, ")")
        # print("repo: ", repo)   #comment this out
        repoURL = repo[0]
        repoName = repoURL.split('/')[1]
        fileLocation = 'Datasets/ContributorInfo/'+repoName+'Contributors.csv'
        numCommits = int(repo[numCommitsIndex])
        #coreContributorList = repo[coreContributorsIndex].split(',')

        SDG = repo[SDGIndex]
        if SDG == None or SDG == "None" or SDG == "" or SDG == " ":
            SG = 0
            numNonSGRepos += 1
        else:
            SG = 1
            numSGRepos += 1




        with open(fileLocation, 'r',encoding='utf-8') as file:
            reader = csv.reader(file)
            userList = list(reader)
        #skip first line for titles
        userList = userList[1:]

        if onlyCore:
            userList, numCoreContributors = getCoreContributors(userList, numCommits)
            #print("Number of Core Contributors: ", numCoreContributors)
            TotalCoreContributors += numCoreContributors

        if userList == []:
            print("[BROKEN REPO]: No users found for repo: ", repoURL)
            # if repoURL not in brokenRepos:
            #     brokenRepos.append(repoURL)
            # else:
            #     print("Repo already in broken repos")

            brokenCount += 1

            continue
        numContributors = 0
        numOneTimeContributors = 0
        numSGContributors = 0
        numNonSGContributors = 0
        numSGOneTimeContributors = 0
        numNonSGOneTimeContributors = 0

        numActive = 0
        numInactive = 0

        totalContributions = 0
        totalActiveTime = 0
        totalInactiveTime = 0
        averageActiveTime = 0
        joinCount = 0
        leaveCount = 0

        #number of contributors active in this window


        joinLeaveRatios = []
        joinLeaveDifferences = []
        leaves = []
        joins = []
        joinRates = []
        leaveRates = []
        numActivePerWindow = []
        #lastRepoContribution = datetime(1970,1,1)
        lastRepoContribution = datetime.strptime(repo[lastContributionIndex], '%Y-%m-%dT%H:%M:%SZ')

        oneTimeContributors = []
        
        # if includeOneTime == False:
        #     for user in userList[:]:
        #         if user[1] == 1:
        #             oneTimeContributors.append(user)
        #             userList.remove(user)


        #Go through all users and get their first and last contribution from the csv file
        for user in userList[:]:


            userContributions = int(user[1])

            if userContributions == 1:
                numOneTimeContributors += 1
                oneTimeContributors.append(user)

                if SG == 1:
                    numSGOneTimeContributors += 1
                else:
                    numNonSGOneTimeContributors += 1


                #skip one time contributors
                if includeOneTime == False:
                    #print("Skipping one time contributor #",numOneTimeContributors,": ", user[0])
                    userList.remove(user)
                    continue
                    

            numContributors += 1
            if SG == 1:
                numSGContributors += 1
            else:
                numNonSGContributors += 1

            totalContributions += userContributions #Get this a better way?
            #isCore = isCoreContributor(userContributions, totalContributions)

            if user[2]:
                firstContribution = datetime.strptime(user[2], "%Y-%m-%d %H:%M:%S")
            else: 
                firstContribution = None
            
            if user[3]:
                lastContribution = datetime.strptime(user[3], "%Y-%m-%d %H:%M:%S")
                # if lastContribution > lastRepoContribution:
                #     lastRepoContribution = lastContribution
            else:
                lastContribution = None




            #increment number of actove or inactive users
            if user[4] == 'True':
                numActive += 1
            else:
                numInactive += 1
            
            #get difference between first and last contribution
            if firstContribution and lastContribution:
                totalActiveTime += (lastContribution - firstContribution).days


   
        totalOneTimeContributors += numOneTimeContributors
        totalContributors += numContributors
        totalSGContributors += numSGContributors
        totalNonSGContributors += numNonSGContributors
        totalSGOneTimeContributors += numSGOneTimeContributors
        totalNonSGOneTimeContributors += numNonSGOneTimeContributors




        if numContributors != 0:
            averageActiveTime = totalActiveTime/numContributors
            averageContributions = totalContributions/numContributors
        else:
            averageActiveTime = 0
            averageContributions = 0

        #print("Repo: ", repoName)
        # print("Active: ", active)
        # print("SG: ", SG)
        #print("Number of Contributors Analyzed: ", numContributors)
        # print("Number of Active Contributors: ", numActive)
        # print("Number of Inactive Contributors: ", numInactive)
        #print("Number of One Time Contributors: ", numOneTimeContributors)
        # print("Total Contributions: ", totalContributions)
        # print("Average Contributions per contributor: ", averageContributions)
        # print("Average Active Time: ", averageActiveTime, " days")
        # print("Last Contribution: ", lastRepoContribution)
        # print("\n")



        #HERE
        #split time between start and end date into windows of size windowSize
        #get the number of joins and leaves in each window

        #get stqrt and end dates

        #startOffset is in years
        #convert to days


        lifespan = int(repo[lifespanIndex])
        repoStartDate = datetime.strptime(repo[startDateIndex], '%Y-%m-%dT%H:%M:%SZ')
        stageStartDate = repoStartDate + timedelta(days=startOffsetDays)
        stageEndDate = repoStartDate + timedelta(days=endOffsetDays)

        #if this repo has the stage being analyzed
        #lastContribution = datetime.strptime(repo[5], '%Y-%m-%dT%H:%M:%SZ')
        if stageEndDate > lastRepoContribution or stageEndDate > datetime.now():
            #This project doesn't have the stage being analyzed
            # print("Repo: ", repoName, " does not have the stage being analyzed")
            # print("Stage Start Date: ", stageStartDate)
            # print("Stage End Date: ", stageEndDate)
            # print("stage end - start: ", stageEndDate - stageStartDate)
            # print("repo start date: ", repoStartDate)
            # print("repo end date: ", lastRepoContribution)
            # print("repo end - start: ", lastRepoContribution - repoStartDate)
            # print("repo Lifepsan: ", lifespan, " days (", lifespan/365, " years)")
            # print("Start offset: ", startOffset)
            # print("End offset: ", endOffset)
            noStage += 1
            if SG == 1:
                noStageSG += 1
            else:
                noStageNonSG += 1

            continue
        else:
            hasStage += 1
            if SG == 1:
                hasStageSG += 1
            else:
                hasStageNonSG += 1

        #split into windows

        #round down (no part windows)
        numWindows = int((endOffsetDays - startOffsetDays)//windowSizeDays)

        # print("Stage Start Date: ", stageStartDate, "(", startOffsetDays, ")")
        # print("Stage End Date: ", stageEndDate, "(", endOffsetDays, ")")
        # print("Window Size: ", windowSizeDays)
        # print("Number of Windows: ", numWindows)


        fiveMonthsAgo = datetime.now() - timedelta(days=5*30)
        if stageEndDate > fiveMonthsAgo:
            effectiveBuffer = datetime.now() - stageEndDate
            needBufferCount += 1
            #use 5 month buffer
    
        #Go through each window and count joins, leaves, actives, etc.
        #for i in range(numWindows-1,-1,-1): #why was i doing it backwards??
        for i in range(0, numWindows):

            windowOffset = i*windowSize

            windowStartDate = stageStartDate + timedelta(days=windowOffset*365)
            windowEndDate = windowStartDate + timedelta(days=windowSize*365)

            joinCount, leaveCount, numActiveInWindow = analyzeWindow(userList, windowStartDate, windowEndDate) #Offset is in years

            windowNumber = i + 1

            if numActiveInWindow != 0:
                joinRate = joinCount/numActiveInWindow
                leaveRate = leaveCount/numActiveInWindow
            else:
                joinRate = joinCount
                leaveRate = leaveCount

            joinRates.append([joinRate, windowNumber])
            leaveRates.append([leaveRate, windowNumber])
            numActivePerWindow.append([numActiveInWindow, windowNumber])

            if leaveCount != 0:
                joinLeaveRatios.append([joinCount/leaveCount, windowNumber])
            else:
                joinLeaveRatios.append([joinCount, windowNumber])

            joinLeaveDifferences.append([joinCount-leaveCount, windowNumber])
            joins.append([joinCount, windowNumber])
            leaves.append([leaveCount, windowNumber])

        allRepoRatios.append([joinLeaveRatios, SG, repoName])
        allRepoDifferences.append([joinLeaveDifferences, SG, repoName])
        allJoins.append([joins, SG, repoName])
        allLeaves.append([leaves, SG, repoName])
        allJoinRates.append([joinRates, SG, repoName])
        allLeaveRates.append([leaveRates, SG, repoName])
        allActivePerWindow.append([numActivePerWindow, SG, repoName])

        if len(joinRates) != 0:
            averageJoinRate = sum([i[0] for i in joinRates])/len(joinRates)
        else:
            averageJoinRate = 0
            print("repo with no join rates: ", repoName)
            print("Join Rates: ", joinRates)


        if len(leaveRates) != 0:
            averageLeaveRate = sum([i[0] for i in leaveRates])/len(leaveRates)
        else:
            averageLeaveRate = 0
            print("repo with no leave rates: ", repoName)
            print("Leave Rates: ", leaveRates)

        averageJoinRates.append([averageJoinRate, SG, repoName])
        averageLeaveRates.append([averageLeaveRate, SG, repoName])


        # if averageJoinRate == 0:
        #     print("Average Join Rate is 0")
        #     print("Join Rates: ", joinRates)

        # if averageLeaveRate == 0:
        #     print("Average Leave Rate is 0")
        #     print("Leave Rates: ", leaveRates)
        #print("\n\n\n")

    print("Number of Repos with stage: ", hasStage)

    print("Number of SG Repos with stage: ", hasStageSG)

    print("Number of Non SG Repos with stage: ", hasStageNonSG)



    if brokenCount != 0:
        print("Number of broken repos: ", brokenCount)
    if brokenRepos != originalBrokenRepos:
        print("Broken Repos: ", brokenRepos)

    #print("Number of repos needing buffer: ", needBufferCount)


    averageOneTimeContributors = totalOneTimeContributors/numRepos
    averageContributors = totalContributors/numRepos
    averageCoreContributors = TotalCoreContributors/numRepos
    averageSGContributors = totalSGContributors/numSGRepos
    averageNonSGContributors = totalNonSGContributors/numNonSGRepos
    averageSGOneTimeContributors = totalSGOneTimeContributors/numSGRepos
    averageNonSGOneTimeContributors = totalNonSGOneTimeContributors/numNonSGRepos
    # averageSGCoreContributors = totalSGCoreContributors/numSGRepos
    # averageNonSGCoreContributors = totalNonSGCoreContributors/numNonSGRepos




    print("Average num Contributors per repo: ", averageContributors)
    print("Average SG Contributors per SG repo: ", averageSGContributors)
    print("Average Non SG Contributors per Non SG repo: ", averageNonSGContributors)

    print("Average One Time Contributors per repo: ", averageOneTimeContributors)
    print("Average SG One Time Contributors per SG repo: ", averageSGOneTimeContributors)
    print("Average Non SG One Time Contributors per Non SG repo: ", averageNonSGOneTimeContributors)
    # if onlyCore:
    #     print("Average Core Contributors: ", averageCoreContributors)


    #print all data for final window

    #print("\nAll Join Rates: ", allJoinRates)

    

    #allRepoRatios: list of lists, each list corresponds to a repo and contains a list of ratios for each window
    #allRepoDifferences: list of lists, each list corresponds to a repo and contains a list of differences for each window
    #allJoins: list of lists, each list corresponds to a repo and contains a list of joins for each window
    #allLeaves: list of lists, each list corresponds to a repo and contains a list of leaves for each window
    #allJoinRates: list of lists, each list corresponds to a repo and contains a list of join rates for each window
    #allLeaveRates: list of lists, each list corresponds to a repo and contains a list of leave rates for each window
    #averageJoinRates: list of values, each value corresponds to the average join rate for a repo
    #averageLeaveRates: list of values, each value corresponds to the average leave rate for a repo



    return allRepoRatios, allRepoDifferences, allJoins, allLeaves, allJoinRates, allLeaveRates, averageJoinRates, averageLeaveRates, allActivePerWindow


def getInfoForPlotsAllStages(repoList, windowSize, quartiles, includeOneTime = True, onlyCore = False):

    firstGroup = []
    secondGroup = []
    thirdGroup = []
    fourthGroup = []

    for repo in repoList:

        lifespan = int(repo[lifespanIndex])

        if lifespan < quartiles[0]*365:
            firstGroup.append(repo)
        elif lifespan < quartiles[1]*365:
            secondGroup.append(repo)
        elif lifespan < quartiles[2]*365:
            thirdGroup.append(repo)
        else:
            fourthGroup.append(repo)
    
    print("\nGetting info for first group (For all stages function)")
    secondRatios, secondDifferences, secondJoins, secondLeaves, secondJoinRates, secondLeaveRates, secondAverageJoinRates, secondAverageLeaveRates, secondActivePerWindow = getInfoForPlots(secondGroup, windowSize, 0, quartiles[0], includeOneTime, onlyCore)

    print(secondActivePerWindow[0])

    print("\nGetting info for second group (For all stages function)")
    thirdRatios, thirdDifferences, thirdJoins, thirdLeaves, thirdJoinRates, thirdLeaveRates, thirdAverageJoinRates, thirdAverageLeaveRates, thirdActivePerWindow = getInfoForPlots(thirdGroup, windowSize, 0, quartiles[1], includeOneTime, onlyCore)



    print("\nGetting info for third group (For all stages function)")
    fourthRatios, fourthDifferences, fourthJoins, fourthLeaves, fourthJoinRates, fourthLeaveRates, fourthAverageJoinRates, fourthAverageLeaveRates, fourthActivePerWindow = getInfoForPlots(fourthGroup, windowSize, 0, quartiles[2], includeOneTime, onlyCore)

    allRatios = secondRatios + thirdRatios + fourthRatios
    allDifferences = secondDifferences + thirdDifferences + fourthDifferences
    allJoins = secondJoins + thirdJoins + fourthJoins
    allLeaves = secondLeaves + thirdLeaves + fourthLeaves
    allJoinRates = secondJoinRates + thirdJoinRates + fourthJoinRates
    allLeaveRates = secondLeaveRates + thirdLeaveRates + fourthLeaveRates
    allAverageJoinRates = secondAverageJoinRates + thirdAverageJoinRates + fourthAverageJoinRates
    allAverageLeaveRates = secondAverageLeaveRates + thirdAverageLeaveRates + fourthAverageLeaveRates
    allActivePerWindow = secondActivePerWindow + thirdActivePerWindow + fourthActivePerWindow

    # print("ALl Active Per Window: ", allActivePerWindow)
    # print("All Active Per Window[0]: ", allActivePerWindow[0])
    print("All Active Per Window Length: ", len(allActivePerWindow))

    return allRatios, allDifferences, allJoins, allLeaves, allJoinRates, allLeaveRates, allAverageJoinRates, allAverageLeaveRates, allActivePerWindow


    #combine these, all different repos

def getCoreContributors(contributorList, numCommits):

    runningTotal = 0
    coreContributorList = []
    numCoreContributors = 0
    for contributor in contributorList:
        name = contributor[0]
        userCommits = int(contributor[1])
        if userCommits < 0.05 * numCommits:
            #print(f"Contributor {contributor[0]} has made less than 5% of commits. They will not be included in the core contributors list.")
            #continue
            break #since it is sorted, no one else will have made more than 5% of commits


        #if name contains [bot]
        if '[bot]' in name:
            continue
        
        coreContributorList.append(contributor)
        numCoreContributors += 1
        runningTotal += userCommits

        if runningTotal >= 0.8*numCommits:
            break

    return coreContributorList, numCoreContributors



def testBrokenRepos():
    #Test broken repos
    #print("Broken Repos: ", brokenRepos)
    print("Number of broken repos: ", len(brokenRepos))
    print("Broken Repos: ", brokenRepos)

    repoCount = 0
    #Check if broken repos are in active repos
    for repo in brokenRepos:
        #print("Repo: ", repo)
        getContributors(repo)
        branchName = getDefaultBranch(repo)
        repoCount += 1
        
        #Should do this differently (using list from before, not using contributions)
        numOneTimeContributors = 0
        repoURL = repo
        print("Repo: ", repoURL, " (", repoCount, "/", len(brokenRepos), ")")
        
        repoName = repoURL.split('/')[1]


        userList = getContributors(repoURL)

        #print("contributorList: ", userList)

        fileLocation = 'Datasets/ContributorInfo/'+repoName+'Contributors.csv'

        with open(fileLocation, 'w', newline='',encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["User", "Number of Contributions","First Contribution", "Last Contribution", "Active"])

            failCount = 0
            failStreak = 0
            userCount = 0
            for user in userList:
                userName = user[0]
                userCount += 1
                #userInfo = getUserInfoFromGithub(user[0], repo)
                print("Getting info for user ", userName, " in repo ", repoURL, " (", userCount, "/", len(userList), ")")
                userInfo = getUserInfoFromGithubGraphQL(userName, repoURL, branchName)
                #print(userInfo)
                if userInfo == (None, None, None) or userInfo == None:
                    failCount += 1
                    failStreak += 1
                elif userInfo:
                    writer.writerow([user[0],user[1], userInfo[0], userInfo[1], userInfo[2]])
                    failStreak = 0

    if len(brokenRepos) != 0:
        print("Number of broken repos: ", len(brokenRepos))
    if brokenRepos != originalBrokenRepos:
        print("Broken Repos: ", brokenRepos)

def getQuartiles(repoInfo):
    #split repos into 4 groups based on lifespan with an equal number of repos per group
    #get the number of repos in each group
    groupSize = len(repoInfo)//4
    print("Group size: ", groupSize)

    if groupSize == 0:
        print("Not enough repos to split into 4 groups")
        print("Number of repos: ", len(repoInfo))
        print(repoInfo)
        return

    #sort repos by lifespan
    sortedRepos = sorted(repoInfo, key=lambda x: int(x[lifespanIndex]))

    #get the lifespan of the repos in each group
    firstGroup= sortedRepos[:groupSize]
    secondGroup = sortedRepos[groupSize:groupSize*2]
    thirdGroup = sortedRepos[groupSize*2:groupSize*3]
    foruthGroup = sortedRepos[groupSize*3:]

    #find the minimum and maxium lifespan for each group (the range)
    minFirst = int(firstGroup[0][lifespanIndex])
    maxFirst = int(firstGroup[-1][lifespanIndex])

    minSecond = int(secondGroup[0][lifespanIndex])
    maxSecond = int(secondGroup[-1][lifespanIndex])

    minThird = int(thirdGroup[0][lifespanIndex])
    maxThird = int(thirdGroup[-1][lifespanIndex])

    minFourth = int(foruthGroup[0][lifespanIndex])
    maxFourth = int(foruthGroup[-1][lifespanIndex])

    #onvert to years
    minFirst = minFirst/365
    maxFirst = maxFirst/365
    
    minSecond = minSecond/365
    maxSecond = maxSecond/365

    minThird = minThird/365
    maxThird = maxThird/365

    minFourth = minFourth/365
    maxFourth = maxFourth/365

    firstQuartile = round((maxFirst + minSecond)/2,3)

    secondQuartile = round((maxSecond + minThird)/2,3)
    
    thirdQuartile = round((maxThird + minFourth)/2,3)

    print("First Quartile: ", firstQuartile)
    print("Second Quartile: ", secondQuartile)
    print("Third Quartile: ", thirdQuartile)

    #get how many repos are in each group based on the custom ranges
    #lower than first quartile
    firstGroup = [x for x in repoInfo if int(x[lifespanIndex]) < firstQuartile*365]
    firstGroupSG = [x for x in firstGroup if x[SDGIndex] != 'None' and x[SDGIndex]]
    firstGroupNotSG = [x for x in firstGroup if x[SDGIndex] == 'None' or not x[SDGIndex]]
    #between first and second quartile
    secondGroup = [x for x in repoInfo if int(x[lifespanIndex]) >= firstQuartile*365 and int(x[lifespanIndex]) < secondQuartile*365]
    secondGroupSG = [x for x in secondGroup if x[SDGIndex] != 'None' and x[SDGIndex]]
    secondGroupNotSG = [x for x in secondGroup if x[SDGIndex] == 'None' or not x[SDGIndex]]

    #between second and third quartile
    thirdGroup = [x for x in repoInfo if int(x[lifespanIndex]) >= secondQuartile*365 and int(x[lifespanIndex]) < thirdQuartile*365]
    thirdGroupSG = [x for x in thirdGroup if x[SDGIndex] != 'None' and x[SDGIndex]]
    thirdGroupNotSG = [x for x in thirdGroup if x[SDGIndex] == 'None' or not x[SDGIndex]]

    #greater than third quartile
    fourthGroup = [x for x in repoInfo if int(x[lifespanIndex]) >= thirdQuartile*365]
    fourthGroupSG = [x for x in fourthGroup if x[SDGIndex] != 'None' and x[SDGIndex]]
    fourthGroupNotSG = [x for x in fourthGroup if x[SDGIndex] == 'None' or not x[SDGIndex]]


    print("First Group: ", len(firstGroup), " SG: ", len(firstGroupSG), " Not SG: ", len(firstGroupNotSG))
    print("Second Group: ", len(secondGroup), " SG: ", len(secondGroupSG), " Not SG: ", len(secondGroupNotSG))
    print("Third Group: ", len(thirdGroup), " SG: ", len(thirdGroupSG), " Not SG: ", len(thirdGroupNotSG))
    print("Fourth Group: ", len(fourthGroup), " SG: ", len(fourthGroupSG), " Not SG: ", len(fourthGroupNotSG))

    #print time lentgh of each window
    
    print("Early Stage Length: ", firstQuartile)
    print("Middle Stage Length: ", secondQuartile - firstQuartile)
    print("Late Stage Length: ", thirdQuartile - secondQuartile)

    return firstQuartile, secondQuartile, thirdQuartile
    
def loadRepoInfo(csvName):
    # Read the repository information from the CSV file
    repoInfo = None

    #Make sure file opens correctly
    try:
        with open(csvName, 'r',encoding="utf-8") as file:
            
            reader = csv.reader(file)
            repoInfo = list(reader)
            #skip first line for titles
            repoInfo = repoInfo[1:]
    except:
        print("Error opening file: ", csvName)

    return repoInfo



def plotLines(ratios, Title, xLabel, yLabel, yLower = None, yUpper = None, legend=0):
    #Plot the join leave ratios for each window, do this for all 10 repos
    #colour code the SG and \Not SG repos differently
    #also need a legend
    #also need average lines for sg and not sg



    for repo in ratios:
        #print("Repo: ", repo)
        SG = int(repo[1])
        dataPoints = repo[0]
        x = [i[1] for i in dataPoints]
        y = [i[0] for i in dataPoints]
        if SG == 1:
            plt.plot(x, y, 'r-')
        elif SG == 0:
            plt.plot(x, y, 'b-')
        else:
            print("Error: SG value not 0 or 1")
    
    #Legend all names
    if legend:
        plt.legend([repo[2] for repo in ratios])

    if xLabel:
        plt.xlabel(xLabel)
    if yLabel:
        plt.ylabel(yLabel)
    if Title:
        plt.title(Title)

    #if they have values (including 0)
    if yLower != None and yUpper != None:
        print("Setting y limits")
        plt.ylim([yLower,yUpper])
    
    plt.show()



def plotRates(joinRates, leaveRates, Title = "Average Join Rate vs Average Leave Rate", xLabel = "Average Lave Rate", yLabel = "Average Join Rate"):
    #Plot a point for each repo, with the average join rate on the x axis and the average leave rate on the y axis
    #colour code the SG and \Not SG repos differently

    #get median values for leave and join rates
    sortedJoinRates = sorted(joinRates, key=lambda x: x[0])
    sortedLeaveRates = sorted(leaveRates, key=lambda x: x[0])

    joinRateMedian = sortedJoinRates[len(sortedJoinRates)//2][0]
    leaveRateMedian = sortedLeaveRates[len(sortedLeaveRates)//2][0]

    print ("Join Rate Median: ", joinRateMedian)
    print ("Leave Rate Median: ", leaveRateMedian)

    points = []
    maxX = 0
    maxY = 0
    minX = 100
    minY = 100
    plottedCount = 0    
    SGCount = 0
    nonSGCount = 0
    SGLocations = [[0, 0], [0, 0]]
    nonSGLocations = [[0, 0], [0, 0]]
    #Attractive: top Left
    #Stable: bottom left
    #Unstable: top right
    #Unattractive: bottom right

    allData = []

    for i in range(len(joinRates)):
        repo = joinRates[i]
        if repo[2] != leaveRates[i][2]:
            print("Error: Repos don't match")
            print("Repo: ", repo)
            print("Leave Rate: ", leaveRates[i])
            print("Join rate: ", repo)
        joinRate = repo[0]
        leaveRate = leaveRates[i][0]

        # if joinRate == 0 and leaveRate == 0: 
        #     print("Zero join and leave rate for repo: ", repo[2])

        SG = int(repo[1])
        x = leaveRate
        y = joinRate

        allData.append([repo[2], SG, x,y])
        


        if x > maxX:
            maxX = x
        if y > maxY:
            maxY = y
        if x < minX:
            minX = x
        if y < minY:
            minY = y




        if leaveRate < leaveRateMedian:
            if joinRate < joinRateMedian:
                #Stable (bottom left)
                if SG == 1:
                    SGLocations[1][0] += 1
                elif SG == 0:
                    nonSGLocations[1][0] += 1
            elif joinRate >= joinRateMedian:
                #Attractive (top left)
                if SG == 1:
                    SGLocations[0][0] += 1
                elif SG == 0:
                    nonSGLocations[0][0] += 1
        elif leaveRate >= leaveRateMedian:  
            if joinRate < joinRateMedian:
                #Unattractive (bottom right)
                if SG == 1:
                    SGLocations[1][1] += 1
                elif SG == 0:
                    nonSGLocations[1][1] += 1
                
            elif joinRate >= joinRateMedian:
                #Unstable (top right)
                if SG == 1:
                    SGLocations[0][1] += 1
                elif SG == 0:
                    nonSGLocations[0][1] += 1
            


        #point = (x,y)
        # if point in points:
        #     print("Duplicate point: ", point)
        #     #How many duplicates
        #     count = points.count(point)
        #     print("Count: ", count)
        # points.append((x,y))

        if SG == 1:
            plt.plot(x, y, 'ro')
            plottedCount += 1
            SGCount += 1
        elif SG == 0:
            plt.plot(x, y, 'bo')
            plottedCount += 1
            nonSGCount += 1
        else:
            print("Error: SG value not 0 or 1")

    saveScatterplotInfo(allData, Title, ["Repo", "SG", "Average Leave Rate", "Average Join Rate"])

    #get max and min values for x and y

    #print formatted into a 2x2 table
    # print("SGLocations: ")
    # print("-------------------------")
    # print("Attractive: ", SGLocations[0][0])
    # print("Unstable: ", SGLocations[0][1])
    # print("Stable: ", SGLocations[1][0])
    # print("Unattractive: ", SGLocations[1][1])
    # print("")



    # print("NonSGLocations: ")
    # print("-------------------------")
    # print("Attractive: ", nonSGLocations[0][0])
    # print("Unstable: ", nonSGLocations[0][1])
    # print("Stable: ", nonSGLocations[1][0])
    # print("Unattractive: ", nonSGLocations[1][1])
    # print("")


    #Convert locations to percentages
    SGPercentages = [[round(100*i/SGCount,1) for i in j] for j in SGLocations]
    nonSGPercentages = [[round(100*i/nonSGCount,1) for i in j] for j in nonSGLocations]


    print("SG Percentages: ")
    print("-------------------------")
    print("Attractive: ", SGPercentages[0][0], "% (" , SGLocations[0][0], "/", SGCount, ")")
    print("Unstable: ", SGPercentages[0][1], "% (" , SGLocations[0][1], "/", SGCount, ")")
    print("Stable: ", SGPercentages[1][0], "% (" , SGLocations[1][0], "/", SGCount, ")")
    print("Unattractive: ", SGPercentages[1][1], "% (" , SGLocations[1][1], "/", SGCount, ")")
    print("Sticky: ", SGPercentages[0][0] + SGPercentages[1][0], "% (" , SGLocations[0][0] + SGLocations[1][0], "/", SGCount, ")")
    print("Magnetic: ", SGPercentages[0][0] + SGPercentages[0][1], "% (" , SGLocations[0][0] + SGLocations[0][1], "/", SGCount, ")")


    print("")

    print("Non SG Percentages: ")
    print("-------------------------")
    print("Attractive: ", nonSGPercentages[0][0], "% (" , nonSGLocations[0][0], "/", nonSGCount, ")")
    print("Unstable: ", nonSGPercentages[0][1], "% (" , nonSGLocations[0][1], "/", nonSGCount, ")")
    print("Stable: ", nonSGPercentages[1][0], "% (" , nonSGLocations[1][0], "/", nonSGCount, ")")
    print("Unattractive: ", nonSGPercentages[1][1], "% (" , nonSGLocations[1][1], "/", nonSGCount, ")")
    print("Sticky: ", nonSGPercentages[0][0] + nonSGPercentages[1][0], "% (" , nonSGLocations[0][0] + nonSGLocations[1][0], "/", nonSGCount, ")")
    print("Magnetic: ", nonSGPercentages[0][0] + nonSGPercentages[0][1], "% (" , nonSGLocations[0][0] + nonSGLocations[0][1], "/", nonSGCount, ")")
    print("")

    if plottedCount != len(joinRates):
        print("Error: Not all repos plotted")

    maxVal = max(maxX, maxY) + 0.05
    minVal = min(minX, minY) - 0.05

    plt.xlim([minVal, maxVal])
    plt.ylim([minVal, maxVal])
    plt.scatter(x, y)
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.title(Title)
    plt.axvspan(-1, leaveRateMedian, color='green', alpha=0.5)
    plt.axhspan(-1, joinRateMedian, color='red', alpha=0.5)
    plt.show()



def plotAverageLines(data, Title, xLabel, yLabel, yLower=None, yUpper=None, legend=0):
    #Get two lines, one for SG and one for not SG
    #For each repo in data
    #repo[0] has the datapoints(x and y)
    #repo[1] has the SG value
    #repo[2] has the repo name

    #SGX, notSGX, SGY, notSGY = [], [], [], []
    #print("Data: ", data)
    SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSG(data)

    #Combine back into one list to save

    allData = [SGX, SGY, notSGY]
    saveGraphinfo(allData, Title, ["Window", "SG", "Not SG"])



    #coutn number of repos passed in
    numRepos = len(data)
    print("Number of repos: ", numRepos)

    if len(SGX) != len(notSGX) or len(SGY) != len(notSGY) or len(SGX) != len(SGY):
        print("Error: Lengths of SG and Not SG data not equal")
        return
    
    #get num data points
    numDataPoints = len(SGX)
    print("Number of data points: ", numDataPoints)


    # print("SGX: ", SGX)
    # print("notSGX: ", notSGX)
    # print("SGY: ", SGY)
    # print("notSGY: ", notSGY)

    #print points in a table
    #value for each window
    # for i in range(0,len(SGX)):
    #     print("Window: ", i+1, " SG: ", round(SGY[i],2), " Not SG: ", round(notSGY[i],2))



    plt.plot(SGX, SGY, 'r-')
    plt.plot(notSGX, notSGY, 'b-')

    if legend:
        plt.legend(["SG", "Not SG"])
    if xLabel:
        plt.xlabel(xLabel)
    if yLabel:
        plt.ylabel(yLabel)
    if Title:
        plt.title(Title)
    if yLower != None and yUpper != None:
        plt.ylim([yLower,yUpper])
    
    plt.show()


def plotAllStages(earlyRates, midRates, lateRates, title, xLabel, yLabel):
    #same as the plot average lines function but plots 6 lines:
    #early SG, early not SG, mid SG, mid not SG, late SG, late not SG
    #in different colors

    #plot average join rates
    earlySGData = []
    earlyNotSGData = []
    midSGData = []
    midNotSGData = []
    lateSGData = []
    lateNotSGData = []

    #get highest window number
    highestWindow = 0
    for repo in earlyRates:
        SG = int(repo[1])


        dataPoints = repo[0]
        if SG == 1:
            earlySGData.append(dataPoints)
        elif SG == 0:
            earlyNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")


    #Need to change window numbers to come after the early window numbers
    for repo in midRates:
        SG = int(repo[1])

        dataPoints = repo[0]
        if SG == 1:
            midSGData.append(dataPoints)
        elif SG == 0:
            midNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")

    for repo in lateRates:
        SG = int(repo[1])
        dataPoints = repo[0]
        if SG == 1:
            lateSGData.append(dataPoints)
        elif SG == 0:
            lateNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")

    earlySGX = [i[1] for i in earlySGData[0]]
    earlyNotSGX = [i[1] for i in earlyNotSGData[0]]

    #get highest window number for early

    highestWindow = earlySGX[-1]
    
    #mid window numbers start at highest window number + 1
    midSGX = [i[1] + highestWindow for i in midSGData[0]]
    midNotSGX = [i[1] + highestWindow for i in midNotSGData[0]]
    # midSGX = [i[1] for i in midSGData[0]]
    # midNotSGX = [i[1] for i in midNotSGData[0]]

    highestWindow = midSGX[-1]

    lateSGX = [i[1] + highestWindow for i in lateSGData[0]]
    lateNotSGX = [i[1] + highestWindow for i in lateNotSGData[0]]

    # lateSGX = [i[1] for i in lateSGData[0]]
    # lateNotSGX = [i[1] for i in lateNotSGData[0]]

    earlySGY = []
    earlyNotSGY = []
    midSGY = []
    midNotSGY = []
    lateSGY = []
    lateNotSGY = []

    print("Plotting all stages")


    print("Early stage Data")
    for i in range(0,len(earlySGData[0])):
        earlySGY.append(sum([j[i][0] for j in earlySGData])/len(earlySGData))
        earlyNotSGY.append(sum([j[i][0] for j in earlyNotSGData])/len(earlyNotSGData))
        #print("Window: ", i+1, " SG: ", round(earlySGY[i],2), " Not SG: ", round(earlyNotSGY[i],2))

    print("Mid stage Data")
    for i in range(0,len(midSGData[0])):
        midSGY.append(sum([j[i][0] for j in midSGData])/len(midSGData))
        midNotSGY.append(sum([j[i][0] for j in midNotSGData])/len(midNotSGData))
        #print("Window: ", i+1, " SG: ", round(midSGY[i],2), " Not SG: ", round(midNotSGY[i],2))

    print("Late stage Data")
    for i in range(0,len(lateSGData[0])):
        lateSGY.append(sum([j[i][0] for j in lateSGData])/len(lateSGData))
        lateNotSGY.append(sum([j[i][0] for j in lateNotSGData])/len(lateNotSGData))
        #print("Window: ", i+1, " SG: ", round(lateSGY[i],2), " Not SG: ", round(lateNotSGY[i],2))

    plt.plot(earlySGX, earlySGY, 'r-')
    plt.plot(midSGX, midSGY, 'r-')
    plt.plot(lateSGX, lateSGY, 'r-')

    plt.plot(earlyNotSGX, earlyNotSGY, 'b-')
    plt.plot(midNotSGX, midNotSGY, 'b-')
    plt.plot(lateNotSGX, lateNotSGY, 'b-')
    
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.title(title)

    plt.show()


def plotAllStagesTwoLines(earlyJoins, midJoins, lateJoins, earlyLeaves, midLeaves, lateLeaves, title, xLabel, yLabel):
    #same as the plot average lines function but plots 6 lines:
    #early SG, early not SG, mid SG, mid not SG, late SG, late not SG
    #in different colors

    #plot average join rates
    earlyJoinsSGData = []
    earlyJoinsNotSGData = []
    midJoinsSGData = []
    midJoinsNotSGData = []
    lateJoinsSGData = []
    lateJoinsNotSGData = []

    earlyLeavesSGData = []
    earlyLeavesNotSGData = []
    midLeavesSGData = []
    midLeavesNotSGData = []
    lateLeavesSGData = []
    lateLeavesNotSGData = []
    

    #get highest window number
    highestWindow = 0
    for repo in earlyJoins:
        SG = int(repo[1])
        dataPoints = repo[0]
        if SG == 1:
            earlyJoinsSGData.append(dataPoints)
        elif SG == 0:
            earlyJoinsNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")


    for repo in midJoins:
        SG = int(repo[1])

        dataPoints = repo[0]
        if SG == 1:
            midJoinsSGData.append(dataPoints)
        elif SG == 0:
            midJoinsNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")

    for repo in lateJoins:
        SG = int(repo[1])
        dataPoints = repo[0]
        if SG == 1:
            lateJoinsSGData.append(dataPoints)
        elif SG == 0:
            lateJoinsNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")

    for repo in earlyLeaves:
        SG = int(repo[1])
        dataPoints = repo[0]
        if SG == 1:
            earlyLeavesSGData.append(dataPoints)
        elif SG == 0:
            earlyLeavesNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")

    for repo in midLeaves:
        SG = int(repo[1])

        dataPoints = repo[0]
        if SG == 1:
            midLeavesSGData.append(dataPoints)
        elif SG == 0:
            midLeavesNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")
    
    for repo in lateLeaves:
        SG = int(repo[1])
        dataPoints = repo[0]
        if SG == 1:
            lateLeavesSGData.append(dataPoints)
        elif SG == 0:
            lateLeavesNotSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")

    

    earlyJoinsSGX = [i[1] for i in earlyJoinsSGData[0]]
    earlyJoinsNotSGX = [i[1] for i in earlyJoinsNotSGData[0]]
    earlyLeavesSGX = [i[1] for i in earlyLeavesSGData[0]]
    earlyLeavesNotSGX = [i[1] for i in earlyLeavesNotSGData[0]]

    #get highest window number for early

    highestWindow = earlyJoinsSGX[-1]
    print("Highest window: ", highestWindow)
    
    #mid window numbers start at highest window number + 1
    midJoinsSGX = [i[1] + highestWindow for i in midJoinsSGData[0]]
    midJoinsNotSGX = [i[1] + highestWindow for i in midJoinsNotSGData[0]]
    midLeavesSGX = [i[1] + highestWindow for i in midLeavesSGData[0]]
    midLeavesNotSGX = [i[1] + highestWindow for i in midLeavesNotSGData[0]]
    # midSGX = [i[1] for i in midSGData[0]]
    # midNotSGX = [i[1] for i in midNotSGData[0]]

    highestWindow = midJoinsSGX[-1]
    print("Highest window: ", highestWindow)

    lateJoinsSGX = [i[1] + highestWindow for i in lateJoinsSGData[0]]
    lateJoinsNotSGX = [i[1] + highestWindow for i in lateJoinsNotSGData[0]]
    lateLeavesSGX = [i[1] + highestWindow for i in lateLeavesSGData[0]]
    lateLeavesNotSGX = [i[1] + highestWindow for i in lateLeavesNotSGData[0]]

    # lateSGX = [i[1] for i in lateSGData[0]]
    # lateNotSGX = [i[1] for i in lateNotSGData[0]]

    earlyJoinsSGY = []
    earlyJoinsNotSGY = []
    midJoinsSGY = []
    midJoinsNotSGY = []
    lateJoinsSGY = []
    lateJoinsNotSGY = []

    earlyLeavesSGY = []
    earlyLeavesNotSGY = []
    midLeavesSGY = []
    midLeavesNotSGY = []
    lateLeavesSGY = []
    lateLeavesNotSGY = []

    for i in range(0,len(earlyJoinsSGData[0])):
        earlyJoinsSGY.append(sum([j[i][0] for j in earlyJoinsSGData])/len(earlyJoinsSGData))
        earlyJoinsNotSGY.append(sum([j[i][0] for j in earlyJoinsNotSGData])/len(earlyJoinsNotSGData))

    for i in range(0,len(midJoinsSGData[0])):
        midJoinsSGY.append(sum([j[i][0] for j in midJoinsSGData])/len(midJoinsSGData))
        midJoinsNotSGY.append(sum([j[i][0] for j in midJoinsNotSGData])/len(midJoinsNotSGData))

    for i in range(0,len(lateJoinsSGData[0])):
        lateJoinsSGY.append(sum([j[i][0] for j in lateJoinsSGData])/len(lateJoinsSGData))
        lateJoinsNotSGY.append(sum([j[i][0] for j in lateJoinsNotSGData])/len(lateJoinsNotSGData))

    for i in range(0,len(earlyLeavesSGData[0])):
        earlyLeavesSGY.append(sum([j[i][0] for j in earlyLeavesSGData])/len(earlyLeavesSGData))
        earlyLeavesNotSGY.append(sum([j[i][0] for j in earlyLeavesNotSGData])/len(earlyLeavesNotSGData))

    for i in range(0,len(midLeavesSGData[0])):
        midLeavesSGY.append(sum([j[i][0] for j in midLeavesSGData])/len(midLeavesSGData))
        midLeavesNotSGY.append(sum([j[i][0] for j in midLeavesNotSGData])/len(midLeavesNotSGData))

    for i in range(0,len(lateLeavesSGData[0])):
        lateLeavesSGY.append(sum([j[i][0] for j in lateLeavesSGData])/len(lateLeavesSGData))
        lateLeavesNotSGY.append(sum([j[i][0] for j in lateLeavesNotSGData])/len(lateLeavesNotSGData))

    plt.plot(earlyJoinsSGX, earlyJoinsSGY, 'r-')
    plt.plot(midJoinsSGX, midJoinsSGY, 'r-')
    plt.plot(lateJoinsSGX, lateJoinsSGY, 'r-')

    plt.plot(earlyJoinsNotSGX, earlyJoinsNotSGY, 'b-')
    plt.plot(midJoinsNotSGX, midJoinsNotSGY, 'b-')
    plt.plot(lateJoinsNotSGX, lateJoinsNotSGY, 'b-')

    plt.plot(earlyLeavesSGX, earlyLeavesSGY, 'r--')
    plt.plot(midLeavesSGX, midLeavesSGY, 'r--')
    plt.plot(lateLeavesSGX, lateLeavesSGY, 'r--')

    plt.plot(earlyLeavesNotSGX, earlyLeavesNotSGY, 'b--')
    plt.plot(midLeavesNotSGX, midLeavesNotSGY, 'b--')
    plt.plot(lateLeavesNotSGX, lateLeavesNotSGY, 'b--')

    plt.ylabel(yLabel)
    plt.xlabel(xLabel)
    plt.title(title)

    plt.show()










def plotTwoAverageLines(joinData, leaveData, Title, xLabel, yLabel, yLower=None, yUpper=None, legend=0):


    joinSGX, joinNotSGX, joinSGY, joinNotSGY = getAverageForSGAndNotSG(joinData)
    leaveSGX, leaveNotSGX, leaveSGY, leaveNotSGY = getAverageForSGAndNotSG(leaveData)


    #coutn number of repos passed in
    numJoinRepos = len(joinData)
    numLeaveRepos = len(leaveData)

    if numJoinRepos != numLeaveRepos:
        print("Error: Different number of repos for join and leave data")
        return
    else:
        numRepos = numJoinRepos

    print("Number of repos: ", numRepos)

    
    if len(joinSGX) != len(joinNotSGX) or len(joinSGY) != len(joinNotSGY) or len(joinSGX) != len(joinSGY):
        print("Error: Lengths of join sg and not sg data not equal")
        return
    
    if len(leaveSGX) != len(leaveNotSGX) or len(leaveSGY) != len(leaveNotSGY) or len(leaveSGX) != len(leaveSGY):
        print("Error: Lengths of leave sg and not sg data not equal")
        return
    
    if len(joinSGX) != len(leaveSGX) or len(joinSGY) != len(leaveSGY) or len(joinSGX) != len(joinSGY):
        print("Error: Lengths of join and leave data not equal")
        return
    

    
    #get num data points
    numDataPoints = len(joinSGX)
    print("Number of data points: ", numDataPoints)


    plt.plot(joinSGX, joinSGY, 'r-')
    plt.plot(joinNotSGX, joinNotSGY, 'b-')

    plt.plot(leaveSGX, leaveSGY, 'r--')
    plt.plot(leaveNotSGX, leaveNotSGY, 'b--')

    if legend:
        plt.legend(["SG", "Not SG"])
    if xLabel:
        plt.xlabel(xLabel)
    if yLabel:
        plt.ylabel(yLabel)
    if Title:
        plt.title(Title)
    if yLower != None and yUpper != None:
        plt.ylim([yLower,yUpper])
    
    plt.show()



    
def performMannWhitneyTest(firstList, secondList):

    n1 = len(firstList)
    n2 = len(secondList)
    

    print("size of first list: ", n1)
    print("size of second list: ", n2)


    #perform T-test
    results = mannwhitneyu(firstList, secondList, False)
    statistic = results.statistic
    pValue = results.pvalue

    alpha = 0.05

    U_mean = (n1*n2)/2
    U_variance = (n1*n2*(n1+n2+1))/12
    U_std = math.sqrt(U_variance)

    Z = (statistic - U_mean)/U_std

    effectSize = Z/math.sqrt(n1 + n2)


    #effect size = Z statistic/sqrt(n)

    print("Mann Whitney Test results: ")
    print("Statistic: ", statistic)
    print("P-value: ", pValue)
    print("Effect Size: ", effectSize)



    if pValue < alpha:
        print("Reject the null hypothesis")
        print("There is a significant difference between the two groups")
    else:
        print("Fail to reject the null hypothesis")
        print("There is no significant difference between the two groups")


    if abs(effectSize) < 0.3:
        print("Effect size is small: there is a small difference between the two groups")
    elif abs(effectSize) < 0.5:
        print("Effect size is medium: there is a medium difference between the two groups")
    else:
        print("Effect size is large: there is a large difference between the two groups")
    
    return statistic, pValue

import numpy as np
from scipy.stats import wilcoxon

def performWilcoxonTest(firstList, secondList):
    # Perform the Wilcoxon signed-rank test (for paired data)
    results = wilcoxon(firstList, secondList)
    statistic = results.statistic
    pValue = results.pvalue
    alpha = 0.05

    # Calculate the number of non-zero differences, which is N
    n = len(firstList)

    # Calculate mean and standard deviation of the Wilcoxon statistic
    W_mean = n * (n + 1) / 4
    W_std = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)

    # Calculate Z-statistic
    Z = (statistic - W_mean) / W_std

    # Calculate effect size (r)
    effectSize = Z / np.sqrt(n)

    print("Wilcoxon Test results: ")
    print("Statistic: ", statistic)
    print("P-value: ", pValue)
    print("Effect Size (r): ", effectSize)

    if pValue < alpha:
        print("Reject the null hypothesis")
        print("There is a significant difference between the two groups")
    else:
        print("Fail to reject the null hypothesis")
        print("There is no significant difference between the two groups")

    if abs(effectSize) < 0.3:
        print("Effect size is small: there is a small difference between the two groups")
    elif abs(effectSize) < 0.5:
        print("Effect size is medium: there is a medium difference between the two groups")
    else:
        print("Effect size is large: there is a large difference between the two groups")
    
    return statistic, pValue, effectSize



def getAverageForSGAndNotSG(data):


    SGData = []
    notSGData = []
    SGX = []
    notSGX = []
    SGY = []
    notSGY = []

    #split data into SG and not SG
    for repo in data:

        SG = int(repo[1])
        dataPoints = repo[0]
        #print("Data Points: ", dataPoints)
        if SG == 1:
            SGData.append(dataPoints)
        elif SG == 0:
            notSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")

    #Get x values (window numbers)
    SGX = [i[1] for i in SGData[0]]
    #print("SGX (WIndow Numbers): ", SGX)

    notSGX = [i[1] for i in notSGData[0]]
    #print("NotSG X (Window Numbers): ", notSGX)

    if SGX != notSGX:
        print("Error: SG and not SG x values are not the same")
        print("SGX: ", SGX)
        print("NotSGX: ", notSGX)

    #Get average y value for each x value
    #issue here?
    #print('SGData[0] length: ', len(SGData[0]))

    #for each window)
    #for i in range(0,len(SGData[0])):
        # SGY.append(sum([j[i][0] for j in SGData])/len(SGData))
        # notSGY.append(sum([j[i][0] for j in notSGData])/len(notSGData))

    sums = [0]*len(SGX)
    counts = [0]*len(SGX)

    #for each repo
    for repo in SGData:
        #for each data point in the repo, 
        for dataPoint in repo:
            windowNumber = dataPoint[1]
            value = dataPoint[0]
            sums[windowNumber-1] += value
            counts[windowNumber-1] += 1

    for i in range(0,len(sums)):
        if counts[i] != 0:
            SGY.append(sums[i]/counts[i])
        else:
            SGY.append(sums[i])

    sums = [0]*len(notSGX)
    counts = [0]*len(notSGX)

    for repo in notSGData:
        for dataPoint in repo:
            windowNumber = dataPoint[1]
            value = dataPoint[0]
            sums[windowNumber-1] += value
            counts[windowNumber-1] += 1
    
    for i in range(0,len(sums)):
        if counts[i] != 0:
            notSGY.append(sums[i]/counts[i])
        else:
            notSGY.append(sums[i])
    




    return SGX, notSGX, SGY, notSGY


def separateSGAndNotSG(repoList):
    #this takes out the value as well
    SGList = []
    nonSGList = []
    for repo in repoList:
        SG = int(repo[1])
        if SG == 1:
            SGList.append(repo[0])
        elif SG == 0:
            nonSGList.append(repo[0])
        else:
            print("Error: SG value not 0 or 1")
    
    return SGList, nonSGList











def getAverageForSGAndNotSGAllStages(data):
    
    SGData = []
    notSGData = []
    SGX = []
    notSGX = []
    SGY = []
    notSGY = []

    #split data into SG and not SG
    for repo in data:

        SG = int(repo[1])
        dataPoints = repo[0]
        #print("Data Points: ", dataPoints)
        if SG == 1:
            SGData.append(dataPoints)
        elif SG == 0:
            notSGData.append(dataPoints)
        else:
            print("Error: SG value not 0 or 1")

    #Get x values (window numbers)
    SGX = [i[1] for i in SGData[0]]
    notSGX = [i[1] for i in notSGData[0]]

    # #Get average y value for each x value
    # for i in range(0,len(SGData[0])):

        #SGY.append(sum([j[i][0] for j in SGData])/len(SGData))
        #notSGY.append(sum([j[i][0] for j in notSGData])/len(notSGData))

    #get longest list in sgData
    longestSGList = max(SGData, key=len)
    longestNotSGList = max(notSGData, key=len)
    longestList = max(longestSGList, longestNotSGList, key=len)

    numWindows = len(longestList)
    #print("Number of windows: ", numWindows)
    for window in range(1, numWindows+1):
        #print("Window: ", window)
        sum = 0
        count = 0
        for repo in SGData:
           #print("Repo: ", repo)
           for repoWindow in repo:
                #print("Repo Window: ", repoWindow)
                if repoWindow[1] == window:
                    #print("Adding to sum: ", repoWindow[0])
                    sum += repoWindow[0]
                    count += 1

        if count != 0:
            SGY.append(sum/count)
        else:
            SGY.append(sum)
            print("Repo with no data for window: ", window)


        sum = 0
        count = 0
        for repo in notSGData:
            #print ("Repo: ", repo)
            for repoWindow in repo:
                #print("Repo Window: ", repoWindow)
                if repoWindow[1] == window:
                    sum += repoWindow[0]
                    count += 1


        if count != 0:
            notSGY.append(sum/count)
        else:
            notSGY.append(sum)
            print("Repo with no data for window: ", window)



    return SGX, notSGX, SGY, notSGY



def combineStages(earlyData, midData, lateData):
    #data is a list of lists, each list corresponds to a repo
    # each repo list has three elements
    #1st: list of data points
    #2nd: SG value
    #3rd: repo name

    #we need to combine the list for any repo with the same name

    combinedData = []

    
    #Need to change window numbers to come after the early window numbers

    #first 0 gets to the first repo
    #aecond [0] gets to list of data 
    
    #third [-1] gets the last element of the list of data points
    #fourth [1] gets the window number
    highestWindow = earlyData[0][0][-1][1]
    
    #mid window numbers start at highest window number + 1
    for repo in midData:
        for data in repo[0]:
            data[1] += highestWindow

    highestWindow = midData[0][0][-1][1]
    for repo in lateData:
        for data in repo[0]:
            data[1] += highestWindow

    #get all repo names
    earlyRepoNames = [i[2] for i in earlyData]
    midRepoNames = [i[2] for i in midData]
    lateRepoNames = [i[2] for i in lateData]

    allRepoNames = earlyRepoNames + midRepoNames + lateRepoNames

    allRepoNames = list(set(allRepoNames))

    #print("All Repo Names: ", allRepoNames)

    for repoName in allRepoNames:
        #get data for each stage
        earlyRepoData = [i for i in earlyData if i[2] == repoName]
        midRepoData = [i for i in midData if i[2] == repoName]
        lateRepoData = [i for i in lateData if i[2] == repoName]

        #combine data
        combinedData.append([earlyRepoData[0][0] + midRepoData[0][0] + lateRepoData[0][0], earlyRepoData[0][1], repoName])
        
    print ("Combined Data: ", combinedData)

    return combinedData




#for testing
def getSeparatedEarlyInfoForPlots(repoList, windowSize, quartiles, includeOneTime = True, onlyCore = False):

    firstGroup = []
    secondGroup = []
    thirdGroup = []
    fourthGroup = []

    earlySecondLength = 0

    earlyThirdLength = 0
    midThirdLength = 0

    earlyFourthLength = 0
    midFourthLength = 0
    lateFourthLength = 0




    for repo in repoList:

        lifespan = int(repo[lifespanIndex])

        if lifespan < quartiles[0]*365:
            firstGroup.append(repo)
        elif lifespan < quartiles[1]*365:
            secondGroup.append(repo)
        elif lifespan < quartiles[2]*365:
            thirdGroup.append(repo)
        else:
            fourthGroup.append(repo)

    print("Quartiles: ", quartiles)
    print("First Group: ", len(firstGroup))
    print("Second Group: ", len(secondGroup))
    print("Third Group: ", len(thirdGroup))
    print("Fourth Group: ", len(fourthGroup))

    #early stage

    #need to get
    #Early stage for all 3
    #Mid stage for second two
    #late stage for last group
    #all stages combined for late
    #first two stages combined for mid?
    #8 total 

    #First group is discarded

    print("\nGetting early info for second group")
    earlySecondGroup = getInfoForPlots(secondGroup, windowSize, 0, quartiles[0], includeOneTime, onlyCore)
    

    # print("Early Second Group: ", earlySecondGroup[8])
    # print("Length of early second group: ", len(earlySecondGroup[8]))

    print("\nGetting early info for third group")
    earlyThirdGroup = getInfoForPlots(thirdGroup, windowSize, 0, quartiles[0], includeOneTime, onlyCore)
    print("\nGetting early info for fourth group")
    earlyFourthGroup = getInfoForPlots(fourthGroup, windowSize, 0, quartiles[0], includeOneTime, onlyCore)

    print("\nGetting mid info for third group")
    midThirdGroup = getInfoForPlots(thirdGroup, windowSize, quartiles[0], quartiles[1], includeOneTime, onlyCore)
    print("\nGetting mid info for fourth group")
    midFourthGroup = getInfoForPlots(fourthGroup, windowSize, quartiles[0], quartiles[1], includeOneTime, onlyCore)

    print("\nGetting late info for fourth group")
    lateFourthGroup = getInfoForPlots(fourthGroup, windowSize, quartiles[1], quartiles[2], includeOneTime, onlyCore)

    #combine all stages for early

    allEarly = [None, None, None, None, None, None, None, None, None]
    allEarly[0] = earlySecondGroup[0] + earlyThirdGroup[0] + earlyFourthGroup[0] #ratios
    allEarly[1] = earlySecondGroup[1] + earlyThirdGroup[1] + earlyFourthGroup[1] #differences
    allEarly[2] = earlySecondGroup[2] + earlyThirdGroup[2] + earlyFourthGroup[2] #joins
    allEarly[3] = earlySecondGroup[3] + earlyThirdGroup[3] + earlyFourthGroup[3] #leaves
    allEarly[4] = earlySecondGroup[4] + earlyThirdGroup[4] + earlyFourthGroup[4] #join rates
    allEarly[5] = earlySecondGroup[5] + earlyThirdGroup[5] + earlyFourthGroup[5] #leave rates
    allEarly[6] = earlySecondGroup[6] + earlyThirdGroup[6] + earlyFourthGroup[6] #average join rates
    allEarly[7] = earlySecondGroup[7] + earlyThirdGroup[7] + earlyFourthGroup[7] #average leave rates
    allEarly[8] = earlySecondGroup[8] + earlyThirdGroup[8] + earlyFourthGroup[8] #active per window



    #combine all stages for mid
    allMid = [None, None, None, None, None, None, None, None, None]

    allMid[0] = midThirdGroup[0] + midFourthGroup[0] #ratios
    allMid[1] = midThirdGroup[1] + midFourthGroup[1] #differences
    allMid[2] = midThirdGroup[2] + midFourthGroup[2] #joins
    allMid[3] = midThirdGroup[3] + midFourthGroup[3] #leaves
    allMid[4] = midThirdGroup[4] + midFourthGroup[4] #join rates
    allMid[5] = midThirdGroup[5] + midFourthGroup[5] #leave rates
    allMid[6] = midThirdGroup[6] + midFourthGroup[6] #average join rates
    allMid[7] = midThirdGroup[7] + midFourthGroup[7] #average leave rates
    allMid[8] = midThirdGroup[8] + midFourthGroup[8] #active per window



    earlySecondLength = len(earlySecondGroup[8])

    earlyThirdLength = len(earlyThirdGroup[8])
    midThirdLength = len(midThirdGroup[8])

    earlyFourthLength = len(earlyFourthGroup[8])
    midFourthLength = len(midFourthGroup[8])
    lateFourthLength = len(lateFourthGroup[8])

    print("Early Second Length: ", earlySecondLength)
    print("Early Third Length: ", earlyThirdLength)
    print("Mid Third Length: ", midThirdLength)
    print("Early Fourth Length: ", earlyFourthLength)
    print("Mid Fourth Length: ", midFourthLength)
    print("Late Fourth Length: ", lateFourthLength)





    return earlySecondGroup, earlyThirdGroup, earlyFourthGroup, midThirdGroup, midFourthGroup, lateFourthGroup, allEarly, allMid

#Takes in the same info as any of the functions that make plots/graphs, but saves the info to a csv instead of plotting it
def saveGraphinfo(data, filename, titles):

    fileLocation = "Datasets/GraphInfo/" + filename + ".csv"

    with open(fileLocation, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(titles)
        #writer.writerows(data)
        writer.writerows(zip(*data))



def saveScatterplotInfo(data, filename, titles):
    
        fileLocation = "Datasets/GraphInfo/" + filename + ".csv"
    
        with open(fileLocation, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(titles)
            writer.writerows(data)
            #writer.writerows(zip(*data))




def main():

    # print("testing broken repos")
    # testBrokenRepos()


    #numYears = 7
    windowSize = 0.25 #in years (3 months)
    #numWindows = int(numYears / windowSize)

    repoList = []
    OSSRepoInfo = []
    OSS4SGRepoInfo = []
    repoInfo = []
    userList = []

    #Get list of repos
    OSS4SGRepoInfo = loadRepoInfo(filteredRepoInfoCSVForSG)
    OSSRepoInfo = loadRepoInfo(filteredRepoInfoCSVNotForSG)
    #combine them
    repoInfo = OSS4SGRepoInfo + OSSRepoInfo
    repoList = [i[0] for i in repoInfo]


    #Test specififc user and repo
    # userInfo = getUserInfoFromGithubGraphQL('ywwhack', 'google/blockly')
    # print("userInfo: ", userInfo)
    # print("Removing broken repos from active list")
    # activeRepoList = removeBrokenRepos(activeRepoList)
    # print("New active repo list size: ", len(activeRepoList))
    # print("")
    
    # print("Removing broken repos from inactive list")
    # inactiveRepoList = removeBrokenRepos(inactiveRepoList)
    # print("New inactive repo list size: ", len(inactiveRepoList))
    # print("")
    quartiles = getQuartiles(repoInfo)





    print("Do you want to rescrape all contributors for the repos? (WARNING: May take a long time) (y/n)")
    if input() == 'y':

        getAllRepos(repoInfo, quartiles)


    
    #Sim4n6  in repo  dimagi/commcare-hq
    # print("Getting info for user Sim4n6 in repo dimagi/commcare-hq")
    # getUserInfoFromGithubGraphQL('Sim4n6', 'dimagi/commcare-hq', 'master', quartiles)

    #Fill in missing repo (any repo without a contributors file)
    print("Getting missing repos")
    getMissingRepos(repoInfo, quartiles)


    #Get one time contributors
    # for repo in activeRepoList:
    #     numOneTimeContributors = repo




    #include one time?
    print("Include one time contributors? (y/n)")
    if input() == 'y':
        includeOneTime = True
    else:
        includeOneTime = False


    print("Only core contributors? (y/n)")
    if input() == 'y':  
        coreContributors = True
    else:
        coreContributors = False   

    #For EarlY stage
    print("\nGetting info for Early Stage")
    earlyRatios, earlyDifferences, earlyJoins, earlyLeaves, earlyJoinRates, earlyLeaveRates, earlyAverageJoinRates, earlyAverageLeaveRates, earlyActivePerWindow = getInfoForPlots(repoInfo, windowSize, 0, quartiles[0], includeOneTime, coreContributors)

    #For Mid stage
    print("\nGetting info for Mid Stage")
    midRatios, midDifferences, midJoins, midLeaves, midJoinRates, midLeaveRates, midAverageJoinRates, midAverageLeaveRates, midActivePerWindow = getInfoForPlots(repoInfo, windowSize, quartiles[0], quartiles[1], includeOneTime, coreContributors)

    #For Late stage
    print("\nGetting info for Late Stage")
    lateRatios, lateDifferences, lateJoins, lateLeaves, lateJoinRates, lateLeaveRates, lateAverageJoinRates, lateAverageLeaveRates, lateActivePerWindow = getInfoForPlots(repoInfo, windowSize, quartiles[1], quartiles[2], includeOneTime, coreContributors)

    #Combine all stages
    print("\nGetting info for all stages combined")
    allRatios, allDifferences, allJoins, allLeaves, allJoinRates, allLeaveRates, allAverageJoinRates, allAverageLeaveRates, allAverageActiveUsers = getInfoForPlotsAllStages(repoInfo, windowSize, quartiles, includeOneTime, coreContributors)

    #Separated by group
    print("\nGetting separated stage info")
    earlyFirstGroup, earlySecondGroup, earlyThirdGroup, midSecondGroup, midThirdGroup, lateThirdGroup, earlyAllGroups, midAllGroups = getSeparatedEarlyInfoForPlots(repoInfo, windowSize, quartiles, includeOneTime, coreContributors)

    earlyNoFirstGroup = [None, None, None, None, None, None, None, None, None]
    earlyNoFirstGroup[0] = earlySecondGroup[0] + earlyThirdGroup[0] #ratios
    earlyNoFirstGroup[1] = earlySecondGroup[1] + earlyThirdGroup[1] #differences
    earlyNoFirstGroup[2] = earlySecondGroup[2] + earlyThirdGroup[2] #joins
    earlyNoFirstGroup[3] = earlySecondGroup[3] + earlyThirdGroup[3] #leaves
    earlyNoFirstGroup[4] = earlySecondGroup[4] + earlyThirdGroup[4] #join rates
    earlyNoFirstGroup[5] = earlySecondGroup[5] + earlyThirdGroup[5] #leave rates
    earlyNoFirstGroup[6] = earlySecondGroup[6] + earlyThirdGroup[6] #average join rates
    earlyNoFirstGroup[7] = earlySecondGroup[7] + earlyThirdGroup[7] #average leave rates
    earlyNoFirstGroup[8] = earlySecondGroup[8] + earlyThirdGroup[8] #active per window

    # #plot all as one big line
    # firstGroupAllAverageActiveUsers = []
    # secondGroupAllAverageActiveUsers = []
    # thirdGroupAllAverageActiveUsers = []
    # for repo in allAverageActiveUsers:
    #     if len(repo[0]) > 36:
    #         thirdGroupAllAverageActiveUsers.append(repo)
    #     elif len(repo[0]) < 30:
    #         firstGroupAllAverageActiveUsers.append(repo)
    #     else:
    #         secondGroupAllAverageActiveUsers.append(repo)



    # #should be the same and aren't
    #plotAverageLines(thirdGroupAllAverageActiveUsers, "Average Active Users for all stages (third Group)", "Window", "Average Active Users")
    #plotAllStages(earlyThirdGroup[8], midThirdGroup[8], lateThirdGroup[8], "Active Users for all stages (third Group)", "Window", "Active Users")


    print("Plot Rates? (y/n) ")
    if input() == 'y':



        print("Plotting Early users per window")
        plotAverageLines(earlyActivePerWindow, "Average Active Users for each window (Early Repos)", "Window", "Average Active Users")
        print("Plotting Early Join Rates")
        plotAverageLines(earlyJoinRates, "Average Join Rate for each window (Early Repos)", "Window", "Average Join Rate") 
        print("Plotting Early Leave Rates")
        plotAverageLines(earlyLeaveRates, "Average Leave Rate for each window (Early Repos)", "Window", "Average Leave Rate") 
        print("Plotting Early Join and Leave Rates")
        plotRates(earlyAverageJoinRates, earlyAverageLeaveRates,  "Join Rate vs Leave Rate for early stages")
        print("Plotting Early Join and Leave Rates in the same graph")
        plotTwoAverageLines(earlyJoinRates, earlyLeaveRates, "Join and Leave Rates for Early Repos", "Window", "Rate", legend=1)

        

        print("Plotting Mid users per window")
        plotAverageLines(midActivePerWindow, "Average Active Users for each window (Mid Repos)", "Window", "Average Active Users")
        print("Plotting Mid Join Rates")
        plotAverageLines(midJoinRates, "Average Join Rate for each window (Mid Repos)", "Window", "Average Join Rate")
        print("Plotting Mid Leave Rates")
        plotAverageLines(midLeaveRates, "Average Leave Rate for each window (Mid Repos)", "Window", "Average Leave Rate") 
        print("Plotting Mid Join and Leave Rates")
        plotRates(midAverageJoinRates, midAverageLeaveRates, "Join Rate vs Leave Rate for mid stages")
        print("Plotting Mid Join and Leave Rates in the same graph")
        plotTwoAverageLines(midJoinRates, midLeaveRates, "Join and Leave Rates for Mid Repos", "Window", "Rate", legend=1)

        print("Plotting Late users per window")
        plotAverageLines(lateActivePerWindow, "Average Active Users for each window (Late Repos)", "Window", "Average Active Users")
        print("Plotting Late Join Rates")
        plotAverageLines(lateJoinRates, "Average Join Rate for each window (Late Repos)", "Window", "Average Join Rate")
        print("Plotting Late Leave Rates")
        plotAverageLines(lateLeaveRates, "Average Leave Rate for each window (Late Repos)", "Window", "Average Leave Rate") 
        print("Plotting Late Join and Leave Rates")
        plotRates(lateAverageJoinRates, lateAverageLeaveRates, "Join Rate vs Leave Rate for late stages")
        print("Plotting Late Join and Leave Rates in the same graph")
        plotTwoAverageLines(lateJoinRates, lateLeaveRates, "Join and Leave Rates for Late Repos", "Window", "Rate", legend=1)



        #plot join and leave rates alkl toegther

        print("Plotting All users per window")
        #saveGraphinfo(allAverageActiveUsers, "allActivePerWindow.csv", ["Active Users", "Window"])
        plotAllStages(earlyActivePerWindow, midActivePerWindow, lateActivePerWindow, "Active Users for all stages", "Window", "Active Users")
        print("Plotting All Join Rates")
        #saveGraphinfo(allJoinRates, "allJoinRates.csv", ["Join Rate", "Window"])
        plotAllStages(earlyJoinRates, midJoinRates, lateJoinRates, "Join Rate for all stages", "Window", "Join Rate")
        print("Plotting All Leave Rates")
        #saveGraphinfo(allLeaveRates, "allLeaveRates.csv", ["Leave Rate", "Window"])
        plotAllStages(earlyLeaveRates, midLeaveRates, lateLeaveRates, "Leave Rate for all stages", "Window", "Leave Rate")
        # print("Plotting All Join and Leave Rates")
        plotRates(allAverageJoinRates, allAverageLeaveRates, "Join Rate vs Leave Rate for all stages")


        #plot all stages on one graph
        print("Plotting All Join and Leave Rates on one graph")
        plotAllStagesTwoLines(earlyJoinRates, midJoinRates, lateJoinRates, earlyLeaveRates, midLeaveRates, lateLeaveRates, "Join Rate vs Leave Rate for all stages", "Window", "Join/Leave Rate")


    print("Do you want to test the rates? (y/n)")
    if input() == 'y' or input() == 'Y':
        print("\ntesting Join rates")
        SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSGAllStages(allJoinRates)
        #performMannWhitneyTest(SGY, notSGY)
        performWilcoxonTest(SGY, notSGY)

        print("\ntesting Leave rates")
        SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSGAllStages(allLeaveRates)
        #performMannWhitneyTest(SGY, notSGY)
        performWilcoxonTest(SGY, notSGY)

        print("\nTesting average join rates (scatterplot)")
        joinRateSG, joinRateNotSG = separateSGAndNotSG(allAverageJoinRates)
        performMannWhitneyTest(joinRateSG, joinRateNotSG)

        print("\nTesting average leave rates (scatterplot)")
        leaveRateSG, leaveRateNotSG = separateSGAndNotSG(allAverageLeaveRates)
        performMannWhitneyTest(leaveRateSG, leaveRateNotSG)
        #don't want to use wilcoxon since the points dont correspond (point for each repo, instead of each window)

        #test early
        print("\ntesting early Join rates")
        SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSG(earlyJoinRates)
        #performMannWhitneyTest(SGY, notSGY)
        performWilcoxonTest(SGY, notSGY)

        print("\ntesting early Leave rates")
        SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSG(earlyLeaveRates)
        #performMannWhitneyTest(SGY, notSGY)
        performWilcoxonTest(SGY, notSGY)

        print("\ntesting early average Join rates (scatterplot)")
        joinRateSG, joinRateNotSG = separateSGAndNotSG(earlyAverageJoinRates)
        performMannWhitneyTest(joinRateSG, joinRateNotSG)

        print("\ntesting early average Leave rates (scatterplot)")
        leaveRateSG, leaveRateNotSG = separateSGAndNotSG(earlyAverageLeaveRates)
        performMannWhitneyTest(leaveRateSG, leaveRateNotSG)




        #test mid
        print("\ntesting mid Join rates")
        SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSG(midJoinRates)
        #performMannWhitneyTest(SGY, notSGY)
        performWilcoxonTest(SGY, notSGY)

        print("\ntesting mid Leave rates")
        SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSG(midLeaveRates)
        #performMannWhitneyTest(SGY, notSGY)
        performWilcoxonTest(SGY, notSGY)

        print("\ntesting mid average Join rates (scatterplot)")
        joinRateSG, joinRateNotSG = separateSGAndNotSG(midAverageJoinRates)
        performMannWhitneyTest(joinRateSG, joinRateNotSG)

        print("\ntesting mid average Leave rates (scatterplot)")
        leaveRateSG, leaveRateNotSG = separateSGAndNotSG(midAverageLeaveRates)
        performMannWhitneyTest(leaveRateSG, leaveRateNotSG)


        #test late
        print("\ntesting late Join rates")
        SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSG(lateJoinRates)
        #performMannWhitneyTest(SGY, notSGY)
        performWilcoxonTest(SGY, notSGY)

        print("\ntesting late Leave rates")
        SGX, notSGX, SGY, notSGY = getAverageForSGAndNotSG(lateLeaveRates)
        #performMannWhitneyTest(SGY, notSGY)
        performWilcoxonTest(SGY, notSGY)


        print("\ntesting late average Join rates (scatterplot)")
        joinRateSG, joinRateNotSG = separateSGAndNotSG(lateAverageJoinRates)
        performMannWhitneyTest(joinRateSG, joinRateNotSG)

        print("\ntesting late average Leave rates (scatterplot)")
        leaveRateSG, leaveRateNotSG = separateSGAndNotSG(lateAverageLeaveRates)
        performMannWhitneyTest(leaveRateSG, leaveRateNotSG)



    


if __name__ == "__main__":
    main()