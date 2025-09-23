#This file scrapes inform,ation for the list of repos, narrows down the list and gets descriptive info.
#Saves all opf this into CSVs




from header import *
from utility import *

# def removeBrokenRepos(repoList):
#     #Remove any repos that are in the list of broken repos
#     #print when a repo is rmeoved
#     count = 0
#     for repo in repoList[:]:
#         if repo[0] in brokenRepos:
#             #print("Removing broken repo: ", repo[0])
#             repoList.remove(repo)
#             count += 1

    
#     print("Number of broken repos removed: ", count)
#     return repoList

def loadRepoList(csvName):
    # Read the list of repositories from the CSV file

    repoList = None

    #Make sure file opens correctly
    with open(csvName, 'r',encoding="utf-8") as file:
        
        reader = csv.reader(file)
        repoList = list(reader)
        #skip first line for titles
        repoList = repoList[1:]

    return repoList

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

def getRepoInfoFromGithub(repo):

    repoName = repo[0]
    repoLink = repoName
    SDG = None

    if len(repo) <= 1:
        SDG = "None"
    else:
        if repo[1]:
            SDG = repo[1]
        else:
            SDG = "Unknown"

    #Check if reponame has the entire link or just the name
    if repoName.startswith('https://api.github.com/repos/'):
        repoLink = repoName
        repoName = repoName.replace('https://api.github.com/repos/','')
    else:
        repoLink = 'https://api.github.com/repos/'+repoName
        repoName = repoName

    print("Repository Name is: ", repoName)

    # Make a GET request to fetch repository information
    response = requests.get(repoLink, headers=headers)
    #print("Response: ", response)


    description = ""
    decodedContent = ""
    topics = []
    lastContribution = ""

    numStars = 0
    numSubscribers = 0
    contributorList = []
    numContributors = 0
    numAnonymousContributors = 0
    numAuthenticatedContributors = 0
    numNotAuthenticatedContributors = 0
    authenticatedContributorList = []
    numOneTimeContributors = 0
    numAuthenticatedOneTimeContributors = 0
    startDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    numLinesOfCode = 0
    numOpenIssues = 0
    numClosedIssues = 0
    numLabelledIssues = 0

    numOpenPullRequests = 0
    numClosedPullRequests = 0
    numMergedPullRequests = 0
    numLabelledPullRequests = 0


    numForks = 0
    numCommits = 0
    mainLanguage = ""
    languagesURL = ""
    languages = []
    pullRequestsURL = ""
    commitsURL = ""
    lifespan = 0
    numCoreContributors = 0
    coreContributorsList = []



    # Check if the request was successful
    if response.status_code == 200:

        print("request was successful")
        # Parse the JSON response
        repoInfo = response.json()
        
        # Extract relevant information from repoInfo
        repoName = repoInfo['full_name']
        description = repoInfo['description']
        topics = list(repoInfo['topics'])
        startDate = repoInfo['created_at']
        lastContribution = repoInfo['pushed_at']
        #convert from string to datetime in order to get difference
        lifespan = (datetime.strptime(lastContribution, '%Y-%m-%dT%H:%M:%SZ') - datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%SZ')).days
        numStars = repoInfo['stargazers_count']
        numSubscribers = repoInfo['subscribers_count']

        repoSize = repoInfo['size']
        #numLinesOfCode = 

        issuesURL = repoInfo['issues_url']
        issuesURL = issuesURL.replace('{/number}','')
        numOpenIssues = repoInfo['open_issues_count']
        #numClosedIssues = repoInfo['closed_issues_count'] #Doesn't work
        #numLabelledIssues = 


        numForks = repoInfo['forks_count']

        mainLanguage = repoInfo['language']
        languagesURL = repoInfo['languages_url']


        pullRequestsURL = repoInfo['pulls_url']
        pullRequestsURL = repoInfo['pulls_url'].replace('{/number}','')



        commitsURL = repoInfo['commits_url']
        commitsURL = repoInfo['commits_url'].replace('{/sha}','')
        
        #numCommits = repoInfo['commits_url']

        #Get contributors
        print("Getting contributors")
        contributorParams = {'per_page': 100, 'page': 1, 'anon': 'true'} #True means include anonymous contributors
        contributorsResponse = requests.get(repoLink+'/contributors', headers=headers, params=contributorParams)
        #print("Contributors response: ", contributorsResponse)
        if contributorsResponse.status_code == 200:

            print("request was successful")

            contributorsInfo = contributorsResponse.json()
            pageNum = 1

            while 'next' in contributorsResponse.links:

                print("Attempt to get next page of contributors")

                # Make a GET request for the next page of contributors
                next_page_url = contributorsResponse.links['next']['url']
                print("Next page url: ", next_page_url)
                contributorsResponse = requests.get(next_page_url, headers=headers)
                #print("Contributors response: ", contributorsResponse)

                # Check if the request was successful
                if contributorsResponse.status_code == 200:

                    print("Fetching next page of contributors ("+str(pageNum)+")")
                    pageNum += 1

                    # Parse the JSON response
                    print("Getting json for additonal contributors")
                    additional_contributors = contributorsResponse.json()
                    
                    # Add contributors from the next page to the list
                    print("Extending info")
                    contributorsInfo.extend(additional_contributors)

                    print("done")

                    #print("Contributors Info: ", contributorsInfo)
                else:
                    print(f"Failed to fetch contributors (next page). Status code: {contributorsResponse.status_code}")
                    break

            print("Finished fetching pages of contributors")

            print("Going through contributors")
            #numContributors = len(contributorsInfo)
            for contributor in contributorsInfo:
                numContributors += 1
                if contributor['contributions'] == 1:  
                    numOneTimeContributors += 1

                #Get core contributors


                #If contributor isn't anonymous
                if 'login' in contributor:
                    numAuthenticatedContributors += 1
                    contributorList.append((contributor['login'], contributor['contributions']))
                    authenticatedContributorList.append((contributor['login'], contributor['contributions']))

                    if contributor['contributions'] == 1:
                        numAuthenticatedOneTimeContributors += 1

                else:
                    #How to not count the contirbutors who are set to anonymous after 500?
                    if numContributors < 500:
                        numNotAuthenticatedContributors += 1
                    numAnonymousContributors += 1
                    
                    #contributorList.append((contributor['name'], contributor['contributions']))
                    contributorList.append(('Anonymous', contributor['contributions']))


            # print(f"Number of contributors: {numContributors}")
            # print(f"Number of authenticated contributors: {numAuthenticatedContributors}")
            # print(f"Number of anonymous contributors: {numAnonymousContributors}")
            # print(f"Number of not authenticated contributors: {numNotAuthenticatedContributors}")

            print("Finished going through contributors")

        else:
            print(f"Failed to fetch contributors. Status code: {contributorsResponse.status_code}")

        print("Getting languages")

        #Get languages
        languagesResponse = requests.get(languagesURL, headers=headers)
        if languagesResponse.status_code == 200:
            languagesInfo = languagesResponse.json()
            languages = list(languagesInfo.keys())
        else:
            print(f"Failed to fetch languages. Status code: {languagesResponse.status_code}")

        print("Getting pull requests")
        
        #Get closed pull requests
        closedPullRequestsParams = {'per_page': 100, 'page': 1, 'state': 'closed'}
        closedPullRequestsResponse = requests.get(pullRequestsURL, headers=headers,params=closedPullRequestsParams)
        
        print("Requesting closed pull requests")
        if closedPullRequestsResponse.status_code == 200:
            closedPullRequestsInfo = closedPullRequestsResponse.json()
            while 'next' in closedPullRequestsResponse.links:
                print("looping for next page of closed pull requests")
                # Make a GET request for the next page of closed pull requests
                nextPageURL = closedPullRequestsResponse.links['next']['url']
                closedPullRequestsResponse = requests.get(nextPageURL, headers=headers)
                print("requesting next page of closed pull requests")
                
                # Check if the request was successful
                if closedPullRequestsResponse.status_code == 200:
                    print("Page request was successful for additional closed pull requests")
                    # Parse the JSON response
                    nextClosedPullRequests = closedPullRequestsResponse.json()
                    
                    
                    # Add closed pull requests from the next page to the list
                    print("Extending closed pull requests")
                    closedPullRequestsInfo.extend(nextClosedPullRequests)
                    print("Done extending closed pull requests")
                else:
                    print(f"Failed to fetch closed pull requests (next page). Status code: {closedPullRequestsResponse.status_code}")
                    break
            
            print("Finished getting closed pull requests")

            numClosedPullRequests = len(closedPullRequestsInfo)
        else:
            print(f"Failed to fetch closed pull requests. Status code: {closedPullRequestsResponse.status_code}")


        print("Getting open pull requests")


        openPullRequestsParams = {'per_page': 100, 'page': 1, 'state': 'open'}
        #Get open pull requests
        openPullRequestsResponse = requests.get(pullRequestsURL, headers=headers,params=openPullRequestsParams)
        
        if openPullRequestsResponse.status_code == 200:
            openPullRequestsInfo = openPullRequestsResponse.json()
            while 'next' in openPullRequestsResponse.links:
                # Make a GET request for the next page of open pull requests
                nextPageURL = openPullRequestsResponse.links['next']['url']
                openPullRequestsResponse = requests.get(nextPageURL, headers=headers)
                
                # Check if the request was successful
                if openPullRequestsResponse.status_code == 200:
                    # Parse the JSON response
                    nextOpenPullRequests = openPullRequestsResponse.json()
                    
                    # Add open pull requests from the next page to the list
                    openPullRequestsInfo.extend(nextOpenPullRequests)
                else:
                    print(f"Failed to fetch open pull requests (next page). Status code: {openPullRequestsResponse.status_code}")
                    break
            numOpenPullRequests = len(openPullRequestsInfo)
        else:
            print(f"Failed to fetch open pull requests. Status code: {openPullRequestsResponse.status_code}")


        print("Getting merged pull requests")

        #Get merged pull requests
        mergedPullRequestsParams = {'per_page': 100, 'page': 1, 'state': 'merged'}
        mergedPullRequestsResponse = requests.get(pullRequestsURL, headers=headers,params=mergedPullRequestsParams)
        if mergedPullRequestsResponse.status_code == 200:
            mergedPullRequestsInfo = mergedPullRequestsResponse.json()
            while 'next' in mergedPullRequestsResponse.links:
                # Make a GET request for the next page of merged pull requests
                nextPageURL = mergedPullRequestsResponse.links['next']['url']
                mergedPullRequestsResponse = requests.get(nextPageURL, headers=headers)
                
                # Check if the request was successful
                if mergedPullRequestsResponse.status_code == 200:
                    # Parse the JSON response
                    nextMergedPullRequests = mergedPullRequestsResponse.json()
                    
                    # Add merged pull requests from the next page to the list
                    mergedPullRequestsInfo.extend(nextMergedPullRequests)
                else:
                    print(f"Failed to fetch merged pull requests (next page). Status code: {mergedPullRequestsResponse.status_code}")
                    break
            numMergedPullRequests = len(mergedPullRequestsInfo)
        else:
            print(f"Failed to fetch merged pull requests. Status code: {mergedPullRequestsResponse.status_code}")
        
        #Get labelled pull requests

        

        #get closed issues

        print("Getting closed issues")

        closedIssuesParams = {'per_page': 100, 'page': 1, 'state': 'closed'}
        closedIssuesResponse = requests.get(repoLink+'/issues', headers=headers,params=closedIssuesParams)
        if closedIssuesResponse.status_code == 200:
            closedIssuesInfo = closedIssuesResponse.json()
            while 'next' in closedIssuesResponse.links:
                # Make a GET request for the next page of closed issues
                nextPageURL = closedIssuesResponse.links['next']['url']
                closedIssuesResponse = requests.get(nextPageURL, headers=headers)
                
                # Check if the request was successful
                if closedIssuesResponse.status_code == 200:
                    # Parse the JSON response
                    nextClosedIssues = closedIssuesResponse.json()
                    
                    # Add closed issues from the next page to the list
                    closedIssuesInfo.extend(nextClosedIssues)
                else:
                    print(f"Failed to fetch closed issues (next page). Status code: {closedIssuesResponse.status_code}")
                    break
            numClosedIssues = len(closedIssuesInfo)
        else:
            print(f"Failed to fetch closed issues. Status code: {closedIssuesResponse.status_code}")




        #Get commits\

        print("Getting commits")

        commitsParams = {'per_page': 100, 'page': 1}
        commitsResponse = requests.get(commitsURL, headers=headers,params=commitsParams)
        if commitsResponse.status_code == 200:
            commitsInfo = commitsResponse.json()
            while 'next' in commitsResponse.links:
                # Make a GET request for the next page of commits
                nextPageURL = commitsResponse.links['next']['url']
                commitsResponse = requests.get(nextPageURL, headers=headers)
                
                # Check if the request was successful
                if commitsResponse.status_code == 200:
                    # Parse the JSON response
                    nextCommits = commitsResponse.json()
                    
                    # Add commits from the next page to the list
                    commitsInfo.extend(nextCommits)
                else:
                    print(f"Failed to fetch commits (next page). Status code: {commitsResponse.status_code}")
                    break
            numCommits = len(commitsInfo)
        else:
            print(f"Failed to fetch commits. Status code: {commitsResponse.status_code}")

        #Core contributors is the set of contributors who have made 80% of the contributions/commits
        #contributors are in order of commits, so add them until 80% of commits are reached

        coreContributorsList, numCoreContributors = getCoreContributors(contributorList, numCommits)
        

        # readmeResponse = requests.get(repoLink+'/readme', headers=headers)
        # if readmeResponse.status_code == 200:
        #     readmeInfo = readmeResponse.json()
        #     content = readmeInfo['content']
        #     decodedContent = base64.b64decode(content).decode('utf-8')
        #     decodedContent = cleanhtml(decodedContent)
        # else:
        #     print(f"Failed to fetch README. Status code: {readmeResponse.status_code}")
    else:
        print(f"Failed to fetch repository information for {repoName}. Status code: {response.status_code}")
        deletedRepos.append(repoName)
        return None

    return [repoName, description, topics, mainLanguage, startDate, lastContribution, lifespan, numStars, numSubscribers, numForks, numContributors, numAuthenticatedContributors, numAnonymousContributors, numNotAuthenticatedContributors, numOneTimeContributors, numAuthenticatedOneTimeContributors, numCoreContributors, contributorList, authenticatedContributorList, coreContributorsList, numCommits, numOpenIssues, numClosedIssues, numOpenPullRequests, numClosedPullRequests, numMergedPullRequests, SDG]
#titles macthing the order of the list above




def getCoreContributors(contributorList, numCommits):
    runningTotal = 0
    coreContributorList = []
    numCoreContributors = 0
    for contributor in contributorList:

        if contributor[1] < 0.05 * numCommits:
            #print(f"Contributor {contributor[0]} has made less than 5% of commits. They will not be included in the core contributors list.")
            #continue
            break #since it is sorted, no one else will have made more than 5% of commits


        #if name contains [bot]
        if '[bot]' in contributor[0]:
            continue
        
        coreContributorList.append(contributor)
        numCoreContributors += 1
        runningTotal += contributor[1]

        if runningTotal >= 0.8*numCommits:
            break

    return coreContributorList, numCoreContributors

def getAllRepoInfoFromGithub(csvName):
    # Get the list of repositories
    repoList = loadRepoList(csvName)
    entries = []
    count = 0
    length = len(repoList)
    
    # Get the information for each repository
    for repo in repoList:
        count += 1
        print(f"Fetching information for repository {count} of {length}")
        entry = getRepoInfoFromGithub(repo)
        if entry:
            entries.append(entry)
            #name = entry[0]
    
    return entries

def deleteEntry(entry, csvFile):
    #delete an entry from the csv file
    with open(csvFile, 'r', newline='') as infile:
        reader = csv.reader(infile)
        rows = [row for row in reader if row != entry]

    with open(csvFile, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)        

def deleteEntries(entries, csvFile):
    #delete multiple entries from the csv file
    with open(csvFile, 'r', newline='',encoding="utf-8") as infile:
        reader = csv.reader(infile)
        rows = [row for row in reader if row not in entries]

    with open(csvFile, 'w', newline='',encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)

def clearCSV(csvFile):
    #clear the csv file
    with open(csvFile, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        print(OSS4SGInfoTitles)
        writer.writerow(OSS4SGInfoTitles)


def saveRepoInfo(repoInfo, csvName, titles, clear=True):
    # Save the repository information to the CSV file
    if clear:
        fileMode = 'w'
    else:
        fileMode = 'a'

    #Make sure to delete any duplicates
    try:
        with open(csvName, 'r', newline='',encoding="utf-8") as inFile:
            reader = csv.reader(inFile)
            duplicateRows = None
            duplicateRows = [row for row in reader if row in repoInfo]
            if duplicateRows:
                deleteEntries(duplicateRows, repoInfoCSVForSG)
    
    except:
        print("No duplicates found")

    with open(csvName, fileMode, newline='',encoding="utf-8") as outFile:
        
        writer = csv.writer(outFile)
        if clear:
            writer.writerow(OSS4SGInfoTitles)
        formattedRepoInfo = []
        for repo in repoInfo:

            #print("Repo: ", repo)

            # temp = []
            # temp.append(repo[0]) #repo name
            # temp.append(repo[1]) #description

            # #csv cant handle longer than 32000 characters
            # # readme = repo[2]
            # # if  len(readme) > 32000:
            # #     readme = repo[2][:32000]
            # #     print(f"Readme content for {repo[0]} is too long. Truncated to 32000 characters.")
            # # temp.append(readme) #readme content\
            # temp.append("README PLACEHOLDER")
            
            # temp.append(listToStringWithoutBrackets(repo[3])) #topics
            # temp.append(repo[4]) #repo start date
            # temp.append(repo[5]) #last contribution
            # #print("num contrib: ",repo[6])
            # temp.append(repo[6]) #num contributors
            # temp.append(repo[7]) #Num authenticated contributors
            # temp.append(repo[8]) #num stars
            # temp.append(repo[9]) #num subscribers

            # contributorList = listToStringWithoutBrackets(repo[10])
            # if len(contributorList) > 32000:
            #     contributorList = contributorList[:32000]
            #     print(f"Contributors for {repo[0]} is too long. Truncated to 32000 characters.")
            # temp.append(listToStringWithoutBrackets(contributorList)) #contributors

            # temp.append(repo[11]) #num one time contributors
            # temp.append(repo[12])

            # #If there is an sgd, add it
            # if len(repo) > 13:
            #     temp.append(repo[13])


            temp = []
            name = repo[nameIndex]
            description = repo[descriptionIndex]
            topics = listToStringWithoutBrackets(repo[topicsIndex])
            language = repo[languageIndex]
            startDate = repo[startDateIndex]
            lastContribution = repo[lastContributionIndex]
            lifespan = repo[lifespanIndex]
            numStars = repo[numStarsIndex]
            numSubscribers = repo[numSubscribersIndex]
            numForks = repo[numForksIndex]
            numContributors = repo[numContributorsIndex]
            numAuthenticatedContributors = repo[numAuthenticatedContributorsIndex]
            numAnonymousContributors = repo[numAnonymousContributorsIndex]
            numNotAuthenticatedContributors = repo[numNotAuthenticatedContributorsIndex]
            numOneTimeContributors = repo[numOneTimeContributorsIndex]
            numAuthenticatedOneTimeContributors = repo[numAuthenticatedOneTimeContributorsIndex]
            numCoreContributors = repo[numCoreContributorsIndex]

            contributors = listToStringWithoutBrackets(repo[contributorsIndex])
            if len(contributors) > 32000:
                contributors = contributors[:32000]
                print(f"Contributors for {name} is too long. Truncated to 32000 characters.")
            

            authenticatedContributors = listToStringWithoutBrackets(repo[authenticatedContributorsIndex])

            coreContributors = listToStringWithoutBrackets(repo[coreContributorsIndex])
            
            numCommits = repo[numCommitsIndex]
            numOpenIssues = repo[numOpenIssuesIndex]
            numClosedIssues = repo[numClosedIssuesIndex]
            numOpenPullRequests = repo[numOpenPullRequestsIndex]
            numClosedPullRequests = repo[numClosedPullRequestsIndex]
            numMergedPullRequests = repo[numMergedPullRequestsIndex]

            if len(repo) > SDGIndex:
                SDG = repo[SDGIndex]
            else:
                SDG = "None"

            #add all to temp
            temp.append(name)
            temp.append(description)
            temp.append(topics)
            temp.append(language)
            temp.append(startDate)
            temp.append(lastContribution)
            temp.append(lifespan)
            temp.append(numStars)
            temp.append(numSubscribers)
            temp.append(numForks)
            temp.append(numContributors)
            temp.append(numAuthenticatedContributors)
            temp.append(numAnonymousContributors)
            temp.append(numNotAuthenticatedContributors)
            temp.append(numOneTimeContributors)
            temp.append(numAuthenticatedOneTimeContributors)
            temp.append(numCoreContributors)
            temp.append(contributors)
            temp.append(authenticatedContributors)
            temp.append(coreContributors)
            temp.append(numCommits)
            temp.append(numOpenIssues)
            temp.append(numClosedIssues)
            temp.append(numOpenPullRequests)
            temp.append(numClosedPullRequests)
            temp.append(numMergedPullRequests)
            temp.append(SDG)

            formattedRepoInfo.append(temp)

        writer.writerows(formattedRepoInfo)

# #Generic save function
def saveReposToCSV(repoInfo, csvName, titles):
    with open(csvName, 'w', newline='',encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(titles)
        print("Repo Info: ", repoInfo)
        writer.writerows(repoInfo)



def getUserInfoFromGithub(user):

    # Make a GET request to fetch user information
    response = requests.get('https://api.github.com/users/'+user, headers=headers)

    userName = user
    email = ""
    location = ""
    company = ""
    numRepos = 0
    numFollowers = 0
    numFollowing = 0
    userRepos = []
    reposContributedTo = []

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        userInfo = response.json()
        
        # Extract relevant information from userInfo

        #Do we need any of this?
        userName = userInfo['login']
        email = userInfo['email']
        location = userInfo['location']
        company = userInfo['company']
        numRepos = userInfo['public_repos']
        numFollowers = userInfo['followers']
        numFollowing = userInfo['following']

        #List of repos
        reposResponse = requests.get('https://api.github.com/users/'+user+'/repos', headers=headers)
        if reposResponse.status_code == 200:
            repos = reposResponse.json()
            # Check if there are more pages of repositories
            while 'next' in reposResponse.links:
                # Make a GET request for the next page of repositories
                nextPageURL = reposResponse.links['next']['url']
                reposResponse = requests.get(nextPageURL, headers={'Accept': 'application/vnd.github.v3+json'})
                
                # Check if the request was successful
                if reposResponse.status_code == 200:
                    # Parse the JSON response
                    nextRepos = reposResponse.json()
                    
                    # Add repositories from the next page to the list
                    repos.extend(nextRepos)
                else:
                    print(f"Failed to fetch repository contributions (next page). Status code: {reposResponse.status_code}")
                    break
            
            for repo in repos:
                repoName = repo['name']
                userRepos.append(repoName)
        else:
            print(f"Failed to fetch user's repositories (first page). Status code: {reposResponse.status_code}")

        publicEventsResponse = requests.get('https://api.github.com/users/'+user+'/events/public', headers=headers)
        if publicEventsResponse.status_code == 200:
            publicEvents = publicEventsResponse.json()

            while 'next' in publicEventsResponse.links:
                # Make a GET request for the next page of public events
                nextPageURL = publicEventsResponse.links['next']['url']
                publicEventsResponse = requests.get(nextPageURL, headers={'Accept': 'application/vnd.github.v3+json'})
                
                # Check if the request was successful
                if publicEventsResponse.status_code == 200:
                    # Parse the JSON response
                    nextPublicEvents = publicEventsResponse.json()
                    
                    # Add public events from the next page to the list
                    publicEvents.extend(nextPublicEvents)
                else:
                    #print(f"Failed to fetch public events (next page). Status code: {publicEventsResponse.status_code}")
                    break

            for event in publicEvents:
                if event:
                    if event['type'] == 'PushEvent':
                        repoName = event['repo']['name']
                        pushDate = event['created_at']
                        reposContributedTo.append((repoName, pushDate))

    else:
        print(f"Failed to fetch user information. Status code: {response.status_code}")

    return reposContributedTo

def isRepoActive(repo):
    #Check if a repo is active
    lastContribution = repo[5]
    lastContributionDate = datetime.strptime(lastContribution, '%Y-%m-%dT%H:%M:%SZ')
    oneYearAgo = datetime.now() - timedelta(days=365)

    if lastContributionDate > oneYearAgo:
        return True
    else:
        return False


def getActiveRepos(repoInfo):
    # Get the list of active repositories
    activeRepos = []
    inactiveRepos = []

    for repo in repoInfo:

        #print("Repo: ", repo)

        if isRepoActive(repo):
            activeRepos.append(repo)
        else:
            inactiveRepos.append(repo)

    print(f"Number of active repositories found: {len(activeRepos)}")

    return activeRepos, inactiveRepos



#Get the number of repos that have been active for a given number of years
#They don't need to still be active
def getNumLongActiveRepos(repoInfo, years):
    count = 0
    for repo in repoInfo:
        startDate = repo[4]
        startDate = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%SZ')
        lastContribution = repo[5]
        lastContribution = datetime.strptime(lastContribution, '%Y-%m-%dT%H:%M:%SZ')
        timeActive = lastContribution - startDate
        if timeActive.days > years*365:
            count += 1

    return count    



def getRepoPercentages(repoInfo):
    averagePercentAuthentic = 0
    averagePercentOneTime = 0
    averagePercentAuthenticOneTime = 0
    averageNumAuth = 0
    averageNumTotal = 0
    averageNumOneTime = 0
    averageNumAuthOneTime = 0
    count = 0
    for repo in repoInfo:

        numTotal = int(repo[numContributorsIndex])
        numAuth = int(repo[numAuthenticatedContributorsIndex])
        numOneTime = int(repo[numOneTimeContributorsIndex])
        numAuthOneTime = int(repo[numAuthenticatedOneTimeContributorsIndex])

        if numTotal:
            percentAuthentic = numAuth/min(numTotal, 500)
            averagePercentAuthentic += percentAuthentic

            percentOneTime = numOneTime/numTotal
            averagePercentOneTime += percentOneTime

            if numAuth:
                percentAuthenticOneTime = numAuthOneTime/numAuth
                averagePercentAuthenticOneTime += percentAuthenticOneTime

            averageNumAuth += numAuth
            averageNumTotal += numTotal
            averageNumOneTime += numOneTime
            averageNumAuthOneTime += numAuthOneTime
        #     else:
        #         print("No authenticated contributors for: ", repo[0])

        # else:
        #     print("No contributors for: ", repo[0])

        count += 1


    averagePercentAuthentic = averagePercentAuthentic/count
    averagePercentOneTime = averagePercentOneTime/count
    averagePercentAuthenticOneTime = averagePercentAuthenticOneTime/count


    averageNumAuth = averageNumAuth/count
    averageNumTotal = averageNumTotal/count
    averageNumOneTime = averageNumOneTime/count
    averageNumAuthOneTime = averageNumAuthOneTime/count

    print("Average percent of authenticated contributors: ", round(averagePercentAuthentic,2))
    print("Average percent of one time contributors: ", round(averagePercentOneTime,2))
    print("Average percent of authenticated one time contributors: ", round(averagePercentAuthenticOneTime,2))

    print("Average number of authenticated contributors: ", round(averageNumAuth,2))
    print("Average number of one time contributors: ", round(averageNumOneTime,2))
    print("Average number of authenticated one time contributors: ", round(averageNumAuthOneTime,2))
    print("Average number of total contributors: ", round(averageNumTotal,2))

    return averagePercentAuthentic, averagePercentOneTime, averagePercentAuthenticOneTime

def getDescriptiveStats(repoInfo, auth = True, graph = False):
    #get min, max, mean, median, mode, and standard deviation for the number of AUTHENTICATED contributors
    numContributors = []
    total = 0
    count = 0
    mean = 0
    stdDev = 0
    sortedContributors = []
    for repo in repoInfo:

        if auth:
            num = int(repo[numAuthenticatedContributorsIndex])
        else:
            num = int(repo[numContributorsIndex])

        numContributors.append(num)
        total += num
        count += 1

    print("Number of contributors: ", total)
    
    mean = total/count

    sortedContributors = sorted(numContributors)

    median = sortedContributors[int(count/2)]

    max = sortedContributors[-1]
    min = sortedContributors[0]

    stdDev = statistics.stdev(numContributors)

    step = 20
    numSteps = math.ceil(max/step)

    rangeList = []
    contributorRangeList = []
    repoCountList = []
    
    for i in range(0, numSteps*step, step):

        contributorRange = f"{i} to {i+step-1}"
        repoCount = len([x for x in numContributors if x >= i and x < i+step])

        #print(f"Number of contributors in range {contributorRange}: {repoCount}")
        rangeList.append((contributorRange, repoCount))
        contributorRangeList.append(contributorRange)
        repoCountList.append(repoCount)

    if graph:
        #graph the ranges in a histogram
        plt.bar(contributorRangeList, repoCountList)
        #roatte x labels
        plt.xticks(rotation=90)
        plt.ylim(0, 25)
        plt.xlabel('Number of Contributors')
        plt.ylabel('Number of Repos')
        plt.title('Number of repos in contributor count Ranges')
        plt.show()

    return min, max, mean, median, stdDev, rangeList



def performTtest(firstList, secondList, ):
    
    firstContributorCounts = []
    secondContributorCounts = []

    #Get contributor counts for each repo

    for repo in firstList:
        contributorCount = int(repo[numAuthenticatedContributorsIndex]) #use authenticted contributors since that what we use for study

        firstContributorCounts.append(contributorCount)
    
    for repo in secondList:
        contributorCount = int(repo[numAuthenticatedContributorsIndex])

        secondContributorCounts.append(contributorCount)

    print("size of first list: ", len(firstContributorCounts))
    print("size of second list: ", len(secondContributorCounts))

    #perform T-test
    results = ttest_ind(firstContributorCounts, secondContributorCounts)
    tStatistic = results.statistic
    pValue = results.pvalue
    df = results.df
    alpha = 0.05
    bonFerroniAlpha = alpha/numSigTests

    print("T-test results: ")
    print("T-statistic: ", tStatistic)
    print("P-value: ", pValue)

    if pValue < alpha:
        print("Reject the null hypothesis")
        print("There is a significant difference between the number of contributors for the two groups")
    else:
        print("Fail to reject the null hypothesis")
        print("There is no significant difference between the number of contributors for the two groups")
    
    return tStatistic, pValue

def performMannWhitneyTest(firstList, secondList):
    
    firstContributorCounts = []
    secondContributorCounts = []

    #Get contributor counts for each repo

    for repo in firstList:
        contributorCount = int(repo[numAuthenticatedContributorsIndex]) 
        firstContributorCounts.append(contributorCount)

        #print("repo: ", repo[0], " num contributors: ", contributorCount)
    
    for repo in secondList:
        contributorCount = int(repo[numAuthenticatedContributorsIndex])
        secondContributorCounts.append(contributorCount)

        #print("repo: ", repo[0], " num contributors: ", contributorCount)

    print("size of first list: ", len(firstContributorCounts))
    print("size of second list: ", len(secondContributorCounts))

    # print("First list: ", firstContributorCounts)
    # print("Second list: ", secondContributorCounts)

    #print without commas (replace commas with spaces)

    # print("Second list: ", str(secondContributorCounts).replace(","," "))

    #perform T-test
    results = mannwhitneyu(firstContributorCounts, secondContributorCounts, False)
    statistic = results.statistic
    pValue = results.pvalue
    alpha = 0.05
    bonFerroniAlpha = alpha/numSigTests

    print("Mann Whitney Test results: ")
    print("Statistic: ", statistic)
    print("P-value: ", pValue)

    if pValue < alpha:
        print("Reject the null hypothesis")
        print("There is a significant difference between the number of contributors for the two groups")
    else:
        print("Fail to reject the null hypothesis")
        print("There is no significant difference between the number of contributors for the two groups")
    
    return statistic, pValue


def filterRepos(repoList, minContributors = 0, maxContributors = 501, minYearsActive = 0):

    filteredRepos = []

    for repo in repoList:
        numContributors = int(repo[numAuthenticatedContributorsIndex])
        startDate = repo[startDateIndex]
        startDate = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%SZ')
        lastContribution = repo[lastContributionIndex]
        lastContribution = datetime.strptime(lastContribution, '%Y-%m-%dT%H:%M:%SZ')
        timeActive = lastContribution - startDate

        if numContributors >= minContributors and numContributors <= maxContributors and timeActive.days >= minYearsActive*365:
            filteredRepos.append(repo)

    print("Number of repos left after filtering: ", len(filteredRepos))
        
    return filteredRepos

#Find more oss repos

def getMoreOSSRepos(rangeList, minYearsActive=0, active=True, existingRepos=[]):
    # GitHub API endpoint for searching repositories
    url = "https://api.github.com/search/repositories"
    repos = []
    page = 1
    perPage = 100
    oneMonthAgo = datetime.now() - timedelta(days=30)
    
    #count is total of all counts in rangelist
    count = sum([x[1] for x in rangeList])
    print("Count of repos to get: ", count)

    #each entry in range list includes a range for contirbutor counts and the number of repos to get in that range

    while len(repos) < count: #could also do while rangelist isnt empty
        # Calculate how many repositories to fetch in this request
        #perPage = min(count - len(repos), 100)

        # Calculate the creation date limit based on minYearsActive
        if active:
            creationDateLimit = datetime.now().year - minYearsActive 
        else:
            creationDateLimit = datetime.now().year #Can't use current year for inactive projects
            #Need to use last contribution date later
            
        #Only works for active project
        #inactive projects require the last contribution date to be used (I need to get this anyways for active projects)

        # Parameters for the search query
        params = {
            'q': f'created:<{creationDateLimit}-01-01',
            # 'sort': 'stars',  # Sort by the number of stars
            'order': 'desc',  # Order by descending
            'per_page': perPage,  # Number of repositories per page (max 100)
            'page': page  # Page number
        }

        # Make the request to the GitHub API
        response = requests.get(url, params=params, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            items = data.get('items', [])
            print("Page number: ", page)
            for repo in items:
                repoName = repo['full_name']
                #print(f"Checking repository: {repoName}")
                if repoName not in existingRepos:

                    #Check if the repo is active if active is True
                    lastContribution = repo['pushed_at']
                    lastContributionDate = datetime.strptime(lastContribution, '%Y-%m-%dT%H:%M:%SZ')
                    if active:
                        if lastContributionDate < oneMonthAgo:
                            #print(f"Skipping repository due to inactivity: {repoName}")
                            continue

                    #Check if the repo has been active for the desired number of years (for active this should already be filtered out by the query)
                    startDate = repo['created_at']
                    startDate = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%SZ')
                    timeActive = lastContributionDate - startDate
                    if timeActive.days < minYearsActive*365:
                        #print(f"Skipping repository due to years active: {repoName}")
                        continue
                    
                    # Fetch the contributors list
                    contributorsUrl = repo['contributors_url']
                    contributorsResponse = requests.get(contributorsUrl, headers=headers, params={'per_page': 100, 'anon': 'false', 'page':1}) #Anonymous are non authenticated
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
                                print(f"URL: {next_page_url}")
                                #Have i exceeded the rate limit?

                                print("Rate limit remaining : ", contributorsResponse.headers['X-RateLimit-Remaining'])
                                #xonvert to datetime
                                print("Rate limit reset : ", datetime.fromtimestamp(int(contributorsResponse.headers['X-RateLimit-Reset'])))
                                break


                        # Filter to count only authenticated contributors
                        # authenticatedContributors = [contributor for contributor in contributorsInfo if contributor.get('login') not in (None, 'ghost', "anonymous")]
                        numContributors = len(contributorsInfo)
                        

                        #INSERT HERE
                        #go through rangelist and see if this repo fits into any, and if that has a count over 0
                        #comvert rangelist to list of lists not lists of tuples
                        rangeList = [list(x) for x in rangeList]

                        #remove any ranges that have 0 repos left
                        rangeList = [x for x in rangeList if x[1] > 0]

                        #print("Range List: ", rangeList)

                        for i in rangeList:
                            print("Checking range: ", i)
                            contributorRange = i[0]
                            minContributors = int(contributorRange.split(" ")[0])
                            maxContributors = int(contributorRange.split(" ")[2])
                            numRepos = i[1]
                            #print("min: ", minContributors, " max: ", maxContributors)
                            if numRepos > 0:
                                if minContributors <= numContributors <= maxContributors:
                                    # Add the repository to the list
                                    repos.append(repoName)
                                    print(f"Added repository: {repoName}")
                                    print(f"Number of contributors: {numContributors}")
                                    print("Last contribution date: ", lastContributionDate)
                                    print("Time active: ", round(timeActive.days/365,2), " years")
                                    #print("-" * 80)
                                

                                    # Decrement the count for the range
                                    i[1] -= 1

                                    print("Number of repos left for range: ", contributorRange, ": ", i[1])

                                    if i[1] == 0:
                                        print(f"No more repos needed for range: {contributorRange}")
                                        
                                    

                                # else:
                                #     print("repo: ", repoName, " does not fit into range: ", contributorRange)
                                #     print(f"Number of contributors: {numContributors}")
                            else:
                                print(f"No more repos needed for range: {contributorRange}")

                    else:
                        print(f"Failed to fetch contributors for repository: {repoName}")
                        print(f"Status code: {contributorsResponse.status_code}")
                        print(f"URL: {contributorsUrl}")
                        print("Rate limit remaining : ", contributorsResponse.headers['X-RateLimit-Remaining'])
                        print("Rate limit reset : ", datetime.fromtimestamp(int(contributorsResponse.headers['X-RateLimit-Reset'])))

                else:
                    print(f"Skipping existing repository: {repoName}")

            page += 1
        else:
            print(f"Failed to fetch repositories: {response.status_code}")
            print("Status code: ", response.status_code)
            print("Rate limit remaining : ", response.headers['X-RateLimit-Remaining'])
            print("Rate limit reset : ", datetime.fromtimestamp(int(response.headers['X-RateLimit-Reset'])))
            break
    
    print("Number of repositories found: ", len(repos))
    print("-" * 80)
    for repo in repos[:count]:
        print(f"Repository URL: {repo}")
        #print(f"Number of contributors: {repo['contributors_url']}")
    print("-" * 80)

    return repos


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
        #print(f"Reset time: {resetTime}")
    else:
        print(f"Failed to fetch rate limit. Status code: {response.status_code}")


def getDiffList(activeSGRangeList, activeNonSGRangeList):
    stepSize = 20
    numSteps = max(len(activeSGRangeList), len(activeNonSGRangeList))
    diffList = []

    for i in range(0, numSteps):

        if i < len(activeSGRangeList):
            contributorRange = activeSGRangeList[i][0]
            numSGRepos = activeSGRangeList[i][1]
        else:
            contributorRange = activeNonSGRangeList[i][0]
            numNonSGRepos = 0

        if i < len(activeNonSGRangeList):
            numNonSGRepos = activeNonSGRangeList[i][1]
        else:
            numNonSGRepos = 0

        print(contributorRange)
        print("Number of SG repos: ", numSGRepos)
        print("Number of Not SG repos: ", numNonSGRepos)

        diff = numSGRepos - numNonSGRepos
        absDiff = abs(diff)
        if diff > 0:
            print(f"Need to add {absDiff} repos to active Not SG in range {contributorRange}")
            diffList.append((contributorRange, diff))
        elif diff < 0:
            print(f"Need to add {absDiff} repos to active SG in range {contributorRange}")
            diffList.append((contributorRange, diff))
        else:
            print(f"Range {contributorRange} is good")

    return diffList


def getNumAuthContributors(repo):

    # Get the contributors list
    contributorsUrl = repo['contributors_url']
    contributorsResponse = requests.get(contributorsUrl, headers=headers, params={'per_page': 100, 'anon': 'false', 'page':1}) #Anonymous are non authenticated
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
                print(f"URL: {next_page_url}")
                #Have i exceeded the rate limit?

                print("Rate limit remaining : ", contributorsResponse.headers['X-RateLimit-Remaining'])
                #xonvert to datetime
                print("Rate limit reset : ", datetime.fromtimestamp(int(contributorsResponse.headers['X-RateLimit-Reset'])))
                break


        # Filter to count only authenticated contributors
        authenticatedContributors = [contributor for contributor in contributorsInfo if contributor.get('login') not in (None, 'ghost', "anonymous")]
        numContributors = len(authenticatedContributors)
    else:
        print(f"Failed to fetch contributors for repository: {repo}")
        print(f"Status code: {contributorsResponse.status_code}")
        print(f"URL: {contributorsUrl}")
        print("Rate limit remaining : ", contributorsResponse.headers['X-RateLimit-Remaining'])
        print("Rate limit reset : ", datetime.fromtimestamp(int(contributorsResponse.headers['X-RateLimit-Reset'])))

    return numContributors

def narrowDownRepos(repos):
    #Criteria:
    #At least 10 contributors and more than one year of history, to exclude toy/personal projects. 
    #At least 500 commits and 50 closed PRs, to exclude projects having a small change history and that are unlikely to provide useful PRs for our analysis.
    #Modified at least once in the last year, to filter out inactive projects. 

    #repos passed in have most of the data already fetched

    numRepos = len(repos)

    newRepos = []

    minContributors = 10
    minCommits = 500
    minClosedPRs = 50
    minLifespan = 365 #days

    #number of repos removed for each criteria
    numInactive = 0
    numLowContributors = 0
    numLowCommits = 0
    numLowClosedPRs = 0
    numShortLifespan = 0

    #Number of repos left after each filter
    numActive = 0
    numHighContributors = 0
    numHighCommits = 0
    numHighClosedPRs = 0
    numLongLifespan = 0



    for repo in repos:
        repoName = repo[0]



        active = isRepoActive(repo)
        if not active:
            #print(f"Skipping {repoName} due to inactivity")
            numInactive += 1
            continue
        else:
            numActive += 1

        numContributors = int(repo[numContributorsIndex])
        numAuthContributors = int(repo[numAuthenticatedContributorsIndex])
        if numAuthContributors < minContributors:
            #print(f"Skipping {repoName} due to low number of contributors: {numAuthContributors}")
            numLowContributors += 1
            continue
        else:
            numHighContributors += 1


        commits = int(repo[numCommitsIndex])
        if commits < minCommits:
            #print(f"Skipping {repoName} due to low number of commits: {commits}")
            numLowCommits += 1
            continue
        else:
            numHighCommits += 1


        closedPullRequests = int(repo[numClosedPullRequestsIndex])
        if closedPullRequests < minClosedPRs:
            #print(f"Skipping {repoName} due to low number of closed PRs: {closedPullRequests}")
            numLowClosedPRs += 1
            continue
        else:
            numHighClosedPRs += 1

        lifespan = int(repo[lifespanIndex])
        if lifespan < minLifespan:
            print(f"Skipping {repoName} due to short lifespan: {lifespan}")
            numShortLifespan += 1
            continue
        else:
            numLongLifespan += 1


        #print(f"Keeping {repoName}")
        newRepos.append(repo)

    numFilteredRepos = len(newRepos)

    print(f"Number of repos before filtering: {numRepos}")
    print(f"Number of repos after filtering: {numFilteredRepos}\n")

    print(f"Number of repos removed due to inactivity: {numInactive}")
    print(f"Number of repos removed due to low number of contributors: {numLowContributors}")
    print(f"Number of repos removed due to low number of commits: {numLowCommits}")
    print(f"Number of repos removed due to low number of closed PRs: {numLowClosedPRs}")
    print(f"Number of repos removed due to short lifespan: {numShortLifespan}\n")

    print(f"Number of repos left after each filter:")
    print(f"Number of active repos: {numActive}")
    print(f"Number of repos with high number of contributors: {numHighContributors}")
    print(f"Number of repos with high number of commits: {numHighCommits}")
    print(f"Number of repos with high number of closed PRs: {numHighClosedPRs}")
    print(f"Number of repos with long lifespan: {numLongLifespan}\n")
    
    
    

    
    return newRepos

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

    return firstQuartile, secondQuartile, thirdQuartile
    



def main():
    print("-----------------Started-----------------")
    repoInfoForSG = None
    repoInfoNotForSG = None
    skip = False



    #Get repo info from github for all repos on list and saved to info 
    print("Get updated OSS4SG info from Github? (may take a while) (y/n)")
    userInput = input()
    if userInput == 'y': 
        before = datetime.now()

        print("Getting all repos for Social good")
        repoInfoForSG = getAllRepoInfoFromGithub(repoListCSVForSG)

        length = len(repoInfoForSG)
        print("Number of repos for SG: ", length)

        print("Clearing CSVs")
        clearCSV(repoInfoCSVForSG)

        print("Saving to CSVs")
        saveRepoInfo(repoInfoForSG, repoInfoCSVForSG, OSS4SGInfoTitles)

        after = datetime.now()
        print("Time taken: ", after - before)
    else:
        if userInput == 's':
            #skip all 
            print("Skipping all")
            skip = True

        print("Loading presaved OSS4SG info from CSVs")
        repoInfoForSG = loadRepoInfo(repoInfoCSVForSG)

    numSG = len(repoInfoForSG)
    print("Number of repos for SG: ", numSG)



    if skip == False:
        print("Get updated OSS (not for SG) info from Github? (may take a while) (y/n)")
        if input() == 'y':
            before = datetime.now()

            print("Getting all repos not for Social good")
            repoInfoNotForSG = getAllRepoInfoFromGithub(repoListCSVNotForSG)

            print("Get additional OSS repos?")
            if input() == 'y':
                print("Getting additional OSS repos")
                additionalRepoInfoNotForSG = getAllRepoInfoFromGithub(additionalRepoListCSVNotForSG)
                repoInfoNotForSG.extend(additionalRepoInfoNotForSG)

            print("Clearing CSVs")
            clearCSV(repoInfoCSVNotForSG)

            print("Saving to CSVs")
            saveRepoInfo(repoInfoNotForSG, repoInfoCSVNotForSG, OSSInfoTitles)

            after = datetime.now()
            print("Time taken: ", after - before)
        else:
            print("Loading presaved OSS info from CSVs")
            repoInfoNotForSG = loadRepoInfo(repoInfoCSVNotForSG)
    else:
        print("Loading presaved OSS info from CSVs")
        repoInfoNotForSG = loadRepoInfo(repoInfoCSVNotForSG)
    # print("Get updated info for additional OSS repos? (y/n)")
    # if input() == 'y':
        


    numNotSG = len(repoInfoNotForSG)
    print("Number of repos not for SG: ", numNotSG)

    if skip == False:
        print("get active OSS4SG repos? (y/n)")
        if input() == 'y':
            activeReposForSG, inactiveReposForSG = getActiveRepos(repoInfoForSG)

            clearCSV(activeRepoInfoCSVForSG)

            saveRepoInfo(activeReposForSG, activeRepoInfoCSVForSG, OSS4SGInfoTitles)
            saveRepoInfo(inactiveReposForSG, inactiveRepoInfoCSVForSG, OSS4SGInfoTitles)
        else:
            print("Loading presaved active repos for SG")
            activeReposForSG = loadRepoInfo(activeRepoInfoCSVForSG)
            inactiveReposForSG = loadRepoInfo(inactiveRepoInfoCSVForSG)
    else:
        print("Loading presaved active repos for SG")
        activeReposForSG = loadRepoInfo(activeRepoInfoCSVForSG)
        inactiveReposForSG = loadRepoInfo(inactiveRepoInfoCSVForSG)

    numActiveSG = len(activeReposForSG)
    print("Number of active repos: ", numActiveSG)

    numInactiveSG = len(inactiveReposForSG)
    print("Number of inactive repos: ", numInactiveSG)
    
    if skip == False:
        print("Get active OSS (not for SG) repos? (y/n)")
        if input() == 'y':
            activeReposNotForSG, inactiveReposNotForSG = getActiveRepos(repoInfoNotForSG)

            clearCSV(activeRepoInfoCSVNotForSG)
            saveRepoInfo(activeReposNotForSG, activeRepoInfoCSVNotForSG, OSSInfoTitles)
            saveRepoInfo(inactiveReposNotForSG, inactiveRepoInfoCSVNotForSG, OSSInfoTitles)
        else:
            print("Loading presaved active repos not for SG")
            activeReposNotForSG = loadRepoInfo(activeRepoInfoCSVNotForSG)
            inactiveReposNotForSG = loadRepoInfo(inactiveRepoInfoCSVNotForSG)
    else:
        print("Loading presaved active repos not for SG")
        activeReposNotForSG = loadRepoInfo(activeRepoInfoCSVNotForSG)
        inactiveReposNotForSG = loadRepoInfo(inactiveRepoInfoCSVNotForSG)

    #Get percent of onetime contributors (and authenticated one time)
    #for activeSG, inactiveSG, activeNotSG, inactiveNotSG
    #4 separate files?

    allRepos = []
    allRepoInfo = []


    #get list of all repos
    for repo in repoInfoForSG:
        allRepos.append(repo[0])
        allRepoInfo.append(repo)

    for repo in repoInfoNotForSG:
        allRepos.append(repo[0])
        allRepoInfo.append(repo)

    #filter repos
    print("Length of sg repos: ", len(repoInfoForSG))
    print("Filtering repos")
    filteredRepos = narrowDownRepos(allRepoInfo)
    print("filtering OSS4SG repos")
    filteredReposForSG = narrowDownRepos(repoInfoForSG)
    print("filtering OSS repos")
    filteredReposNotForSG = narrowDownRepos(repoInfoNotForSG)

    
    #save filtered repos to new csv
    print("Saving filtered repos to CSV")
    saveRepoInfo(filteredReposForSG, filteredRepoInfoCSVForSG, OSS4SGInfoTitles)
    saveRepoInfo(filteredReposNotForSG, filteredRepoInfoCSVNotForSG, OSSInfoTitles)

    # print("Filtering repos by 40+ contributors and 5+ years active")
    # activeReposForSG = filterRepos(activeReposForSG, 40, 501, 5)
    # inactiveReposForSG = filterRepos(inactiveReposForSG, 40, 501, 5)
    # activeReposNotForSG = filterRepos(activeReposNotForSG, 40, 501, 5)
    # inactiveReposNotForSG = filterRepos(inactiveReposNotForSG, 40, 501, 5)


    # print("Getting percentages of contributors")
    # averagePercentAuthentic = 0
    # averagePercentOneTime = 0
    # averagePercentAuthenticOneTime = 0

    # print("\nFor active SG repos:")
    # averagePercentAuthentic, averagePercentOneTime, averagePercentAuthenticOneTime = getRepoPercentages(activeReposForSG)

    # print("\nFor inactive SG repos:")
    # averagePercentAuthentic, averagePercentOneTime, averagePercentAuthenticOneTime = getRepoPercentages(inactiveReposForSG)

    # print("\nFor active Not SG repos:")
    # averagePercentAuthentic, averagePercentOneTime, averagePercentAuthenticOneTime = getRepoPercentages(activeReposNotForSG)

    # print("\nFor inactive Not SG repos:")
    # averagePercentAuthentic, averagePercentOneTime, averagePercentAuthenticOneTime = getRepoPercentages(inactiveReposNotForSG)



    #print descriptive stats for number of contributors
    print("\nGetting descriptive stats for number of contributors")
    print("\nFor active SG repos:")
    activeSGMin, activeSGMax, activeSGMean, activeSGMedian, activeSGStdDev, activeSGRangeList = getDescriptiveStats(activeReposForSG)
    print("Number of repos: ", len(activeReposForSG))
    # print("Min: ", activeSGMin)
    # print("Max: ", activeSGMax)
    # print("Mean: ", activeSGMean)
    # print("Median: ", activeSGMedian)
    # print("Standard Deviation: ", activeSGStdDev)



    # print("\nFor inactive SG repos:")
    # min, max, mean, median, stdDev = getDescriptiveStats(inactiveReposForSG)
    # print("Number of repos: ", len(inactiveReposForSG))
    # print("Min: ", min)
    # print("Max: ", max)
    # print("Mean: ", mean)
    # print("Median: ", median)
    # print("Standard Deviation: ", stdDev)

    print("\nFor active Not SG repos:")
    activeNonSGMin, activeNonSGMax, activeNonSGMean, activeNonSGMedian, activeNonSGStdDev, activeNonSGRangeList = getDescriptiveStats(activeReposNotForSG)
    print("Number of repos: ", len(activeReposNotForSG))
    # print("Min: ", activeNonSGMin)
    # print("Max: ", activeNonSGMax)
    # print("Mean: ", activeNonSGMean)
    # print("Median: ", activeNonSGMedian)
    # print("Standard Deviation: ", activeNonSGStdDev)





    # print("\nFor inactive Not SG repos:")
    # min, max, mean, median, stdDev = getDescriptiveStats(inactiveReposNotForSG)
    # print("Number of repos: ", len(inactiveReposNotForSG))
    # print("Min: ", min)
    # print("Max: ", max)
    # print("Mean: ", mean)
    # print("Median: ", median)
    # print("Standard Deviation: ", stdDev)

    #perform T-test on number of contributors for active SG and active Not SG
    print("\nPerforming tests on number of contributors for active SG and active Not SG")
    performMannWhitneyTest(activeReposForSG, activeReposNotForSG)

    # print("\nPerforming tests on number of contributors for all sg vs nonsg")
    # performMannWhitneyTest(repoInfoForSG, repoInfoNotForSG)


    #compare the rangeLists to see which ranges need to be supplemented to make similar distributions

    # print("Active SG range list: ", activeSGRangeList)
    # print("Active Not SG range list: ", activeNonSGRangeList)

    # diffList = getDiffList(activeSGRangeList, activeNonSGRangeList)

    # print("Diff list: ", diffList)

    # diffList = [x for x in diffList if x[1] > 0]

    # print("positive only Diff list: ", diffList)
    

    # newOSSRepos = getMoreOSSRepos(diffList, 5, True, allRepos)

    # print("New OSS repos: ", newOSSRepos)

    # #add 0 to each repo in list to make them (name, 0)
    # newOSSRepos = [(x, "0") for x in newOSSRepos]

    # #save new repos to csv
    # print("Saving new repos to CSV")
    # saveReposToCSV(newOSSRepos, additionalRepoListCSVNotForSG, listTitles)

    # #get info for new repos
    # print("Getting info for new repos")
    # newRepoInfo = getAllRepoInfoFromGithub(additionalRepoListCSVNotForSG)

    # #save new repo info to csv
    # print("Saving new repo info to CSV")
    # saveRepoInfo(newRepoInfo, repoInfoCSVNotForSG, OSSInfoTitles, False)

    print("Get quartiles for lifespan")
    getQuartiles(filteredRepos)
    print("Get quartiles for SG")
    getQuartiles(filteredReposForSG)
    print("Get quartiles for Not SG")
    getQuartiles(filteredReposNotForSG)


    print("-----------Finished-------------------")




if __name__ == "__main__":
    main()