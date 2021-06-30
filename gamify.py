import os, sys
import runpy
import json
from datetime import timedelta, datetime

def getID(line):
    try:
        if '"id": "' not in line:
            return -1

        end = line.rindex('"')
        start = line.rindex('"', 0, end-1) +1
        return line[start:end]
    except:
        print('!!! Error getting ID, full line:')
        print(line)
        return -1

print('How many days will the competition start date go back?')
day_count = int(input())
now = datetime.now()
startdate = now - timedelta(days = day_count)
startDir = os.getcwd()

print('lets do this! Competition start time is ' + startdate.strftime("%d/%m/%Y %H:%M:%S"))

if len(sys.argv) != 2:
    print('1 required argument, working dir')
    exit(1)

print(str(sys.argv[1]))
projDir = sys.argv[1]
os.chdir(projDir)
print('so far, so good!')
print('generating git history!')

starting_branch = os.popen('git rev-parse --abbrev-ref HEAD').read()
os.system('git fetch')
os.system('git pull')
os.system('git log --pretty=format:"%h~%an~%as" package.json > git_out.txt')

# get list of commits, discard those outside of date range
commits = []
dev_dict = dict() # keeps scores

with open('git_out.txt') as f:
    while True:
        print('in file read')
        l = f.readline()
        if not l:
            break

        split = l.split('~')
        # tuple is [commit, name, date]
        commit_tuple = (split[0], split[1], datetime.strptime(split[2].strip(), '%Y-%m-%d'))
        if commit_tuple[1] not in dev_dict:
            dev_dict[commit_tuple[1]] = 0

        # only look at commits after startdate
        if commit_tuple[2] < startdate:
            break
        commits.append(commit_tuple)

os.remove('git_out.txt')

# go through list in reverse order, calling snyk test on each one

# do baseline test before loop TODO
oldest = commits.pop()
os.system('git checkout %s' % oldest[0])
os.system('npm i')

# code to run cli-analytics, but that json doesn't load.  Saving for reference.
#sys.argv = ['', '--repoDescriptor=' + oldest[0], '--fileName=' + oldest[0]+'.json', '--projDir=' + projDir]
#runpy.run_path(startDir+ '/cli-analytics.py', run_name='cli-analytics')

os.system('snyk test --json --strict-out-of-sync=false >> snyk_baseline.json')

# load json results and populate dict
issues = set()

# TODO we ignore failing to parse the ID at present.
# i get errors loading --json output, so :shrug:
for line in open(projDir + '/snyk_baseline.json'):
    id = getID(line)
    if id != -1:
        issues.add(id)

print('Total number of starting vulns is: %i' % len(issues))
os.remove('snyk_baseline.json')
os.system('git reset --hard') # TODO probably a bad idea

try:
    for i in reversed(commits):
        # checkout commit and build
        print('-------- checking out %s ----------' % i[0])
        os.system('git checkout %s' % i[0])
        os.system('npm i')

        ## do test on this commit
        os.system('snyk test --json --strict-out-of-sync=false >> snyk_testresult.json')

        new_issues = set()
        for line in open(projDir + '/snyk_testresult.json'):
            new_issues.add(getID(line))

        # compare vulns in current to baseline
        # update points in dev_dict
        # add points to dev_dict
        for v in issues:
            if v not in new_issues:
                #print('Hooray, vuln fixed!!')
                dev_dict[i[1]] += 1

        issues = new_issues
        os.remove('snyk_testresult.json')
        os.system('git reset --hard') # TODO probably a bad idea
except:
    os.system('git checkout ' + starting_branch)

sorted_dict = dict(sorted(dev_dict.items(), key=lambda item: item[1], reverse=True))
vulns_fixed = 0

dev_markup = ''
dev_count = 0

for dev in sorted_dict:
   vulns_fixed += dev_dict[dev]
   dev_count += 1
   dev_markup += '''<tr class="meta-row meta-row-''' + str(dev_count) + '''"> <th class="meta-row-rank">''' + str(dev_count) + '''</th> <th class="place-img"> </th> <th class="meta-row-label">''' + dev + '''</th> <td class="meta-row-value">''' + str(dev_dict[dev]) + '''</td></tr>'''

markup = '''
<!DOCTYPE html>
<html lang="en">

<head>
    <meta http-equiv="Content-type" content="text/html; charset=utf-8">
    <meta http-equiv="Content-Language" content="en-us">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Snyk test report</title>
    <meta name="description" content="As a team you have fixed {{ issues_fixed }} known vulnerabilities.">
    <link rel="icon" type="image/png" href="https://res.cloudinary.com/snyk/image/upload/v1468845142/favicon/favicon.png"
          sizes="194x194">
    <link rel="shortcut icon" href="https://res.cloudinary.com/snyk/image/upload/v1468845142/favicon/favicon.ico">
    <style type="text/css">

        body {
            -moz-font-feature-settings: "pnum";
            -webkit-font-feature-settings: "pnum";
            font-variant-numeric: proportional-nums;
            display: flex;
            flex-direction: column;
            font-feature-settings: "pnum";
            font-size: 100%;
            line-height: 1.5;
            min-height: 100vh;
            -webkit-text-size-adjust: 100%;
            margin: 0;
            padding: 0;
            background-color: #F5F5F5;
            font-family: 'Arial', 'Helvetica', Calibri, sans-serif;
        }

        h1,
        h2,
        h3,
        h4,
        h5,
        h6 {
            font-weight: 500;
        }

        a,
        a:link,
        a:visited {
            border-bottom: 1px solid #4b45a9;
            text-decoration: none;
            color: #4b45a9;
        }

        a:hover,
        a:focus,
        a:active {
            border-bottom: 1px solid #4b45a9;
        }

        hr {
            border: none;
            margin: 1em 0;
            border-top: 1px solid #c5c5c5;
        }

        ul {
            padding: 0 1em;
            margin: 1em 0;
        }

        code {
            background-color: #EEE;
            color: #333;
            padding: 0.25em 0.5em;
            border-radius: 0.25em;
        }

        pre {
            background-color: #333;
            font-family: monospace;
            padding: 0.5em 1em 0.75em;
            border-radius: 0.25em;
            font-size: 14px;
        }

        pre code {
            padding: 0;
            background-color: transparent;
            color: #fff;
        }

        a code {
            border-radius: .125rem .125rem 0 0;
            padding-bottom: 0;
            color: #4b45a9;
        }

        a[href^="http://"]:after,
        a[href^="https://"]:after {
            background-image: linear-gradient(transparent,transparent),url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20112%20109%22%3E%3Cg%20id%3D%22Page-1%22%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20id%3D%22link-external%22%3E%3Cg%20id%3D%22arrow%22%3E%3Cpath%20id%3D%22Line%22%20stroke%3D%22%234B45A9%22%20stroke-width%3D%2215%22%20d%3D%22M88.5%2021l-43%2042.5%22%20stroke-linecap%3D%22square%22%2F%3E%3Cpath%20id%3D%22Triangle%22%20fill%3D%22%234B45A9%22%20d%3D%22M111.2%200v50L61%200z%22%2F%3E%3C%2Fg%3E%3Cpath%20id%3D%22square%22%20fill%3D%22%234B45A9%22%20d%3D%22M66%2015H0v94h94V44L79%2059v35H15V30h36z%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E");
            background-repeat: no-repeat;
            background-size: .75rem;
            content: "";
            display: inline-block;
            height: .75rem;
            margin-left: .25rem;
            width: .75rem;
        }


        /* Layout */

        [class*=layout-container] {
            margin: 0 auto;
            max-width: 71.25em;
            padding: 1.9em 1.3em;
            position: relative;
        }
        .layout-container--short {
            padding-top: 0;
            padding-bottom: 0;
            max-width: 48.75em;
        }

        .layout-container--short:after {
            display: block;
            content: "";
            clear: both;
        }

        /* Header */

        .header {
            padding-bottom: 1px;
        }

        .paths {
            margin-left: 8px;
        }
        .header-wrap {
            display: flex;
            flex-direction: row;
            justify-content: space-between;
            padding-top: 2em;
        }
        .project__header {
            background-color: #4b45a9;
            color: #fff;
            margin-bottom: -1px;
            padding-top: 1em;
            padding-bottom: 0.25em;
            border-bottom: 2px solid #BBB;
        }

        .project__header__title {
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-all;
            margin-bottom: .1em;
            margin-top: 0;
        }

        .timestamp {
            float: right;
            clear: none;
            margin-bottom: 0;
        }

        .meta-counts {
            clear: both;
            display: block;
            flex-wrap: wrap;
            justify-content: space-between;
            margin: 0 0 1.5em;
            color: #fff;
            clear: both;
            font-size: 1.1em;
        }

        .meta-count {
            display: block;
            flex-basis: 100%;
            margin: 0 1em 1em 0;
            float: left;
            padding-right: 1em;
            border-right: 2px solid #fff;
        }

        .meta-count:last-child {
            border-right: 0;
            padding-right: 0;
            margin-right: 0;
        }

        /* Card */

        .card {
            background-color: #fff;
            border: 1px solid #c5c5c5;
            border-radius: .25rem;
            margin: 0 0 2em 0;
            position: relative;
            min-height: 40px;
            padding: 1.5em;
        }

        .card .label {
            background-color: #767676;
            border: 2px solid #767676;
            color: white;
            padding: 0.25rem 0.75rem;
            font-size: 0.875rem;
            text-transform: uppercase;
            display: inline-block;
            margin: 0;
            border-radius: 0.25rem;
        }

        .card .label__text {
            vertical-align: text-top;
            font-weight: bold;
        }

        .card .label--critical {
            background-color: #AB1A1A;
            border-color: #AB1A1A;
        }

        .card .label--high {
            background-color: #CE5019;
            border-color: #CE5019;
        }

        .card .label--medium {
            background-color: #D68000;
            border-color: #D68000;
        }

        .card .label--low {
            background-color: #88879E;
            border-color: #88879E;
        }

        .severity--low {
            border-color: #88879E;
        }

        .severity--medium {
            border-color: #D68000;
        }

        .severity--high {
            border-color: #CE5019;
        }

        .severity--critical {
            border-color: #AB1A1A;
        }

        .card--vuln {
            padding-top: 4em;
        }

        .card--vuln .label {
            left: 0;
            position: absolute;
            top: 1.1em;
            padding-left: 1.9em;
            padding-right: 1.9em;
            border-radius: 0 0.25rem 0.25rem 0;
        }

        .card--vuln .card__section h2 {
            font-size: 22px;
            margin-bottom: 0.5em;
        }

        .card--vuln .card__section p {
            margin: 0 0 0.5em 0;
        }

        .card--vuln .card__meta {
            padding: 0 0 0 1em;
            margin: 0;
            font-size: 1.1em;
        }

        .card .card__meta__paths {
            font-size: 0.9em;
        }

        .card--vuln .card__title {
            font-size: 28px;
            margin-top: 0;
        }

        .card--vuln .card__cta p {
            margin: 0;
            text-align: right;
        }

        .source-panel {
            clear: both;
            display: flex;
            justify-content: flex-start;
            flex-direction: column;
            align-items: flex-start;
            padding: 0.5em 0;
            width: fit-content;
        }



    </style>
    <style type="text/css">
        .metatable {
            text-size-adjust: 100%;
            -webkit-font-smoothing: antialiased;
            -webkit-box-direction: normal;
            color: inherit;
            font-feature-settings: "pnum";
            box-sizing: border-box;
            background: transparent;
            border: 0;
            font: inherit;
            font-size: 100%;
            margin: 0;
            outline: none;
            padding: 0;
            text-align: left;
            text-decoration: none;
            vertical-align: baseline;
            z-index: auto;
            margin-top: 12px;
            border-collapse: collapse;
            border-spacing: 0;
            font-variant-numeric: tabular-nums;
            width: 50%;
            margin: auto;
        }

        tbody {
            text-size-adjust: 100%;
            -webkit-font-smoothing: antialiased;
            -webkit-box-direction: normal;
            color: inherit;
            font-feature-settings: "pnum";
            border-collapse: collapse;
            border-spacing: 0;
            box-sizing: border-box;
            background: transparent;
            border: 0;
            font: inherit;
            font-size: 100%;
            margin: 0;
            outline: none;
            padding: 0;
            text-align: left;
            text-decoration: none;
            vertical-align: baseline;
            z-index: auto;
            display: flex;
            flex-wrap: wrap;
        }

        .meta-row {
            text-size-adjust: 100%;
            -webkit-font-smoothing: antialiased;
            -webkit-box-direction: normal;
            color: inherit;
            font-feature-settings: "pnum";
            border-collapse: collapse;
            border-spacing: 0;
            box-sizing: border-box;
            background: transparent;
            border: 0;
            font: inherit;
            font-size: 100%;
            outline: none;
            text-align: left;
            text-decoration: none;
            vertical-align: baseline;
            z-index: auto;
            display: flex;
            align-items: start;
            border-top: 1px solid #d3d3d9;
            padding: 8px 0 0 0;
            border-bottom: none;
            margin: 8px;
            width: 100%;
            padding: 10px;
        }

        .meta-row-rank {
            text-size-adjust: 100%;
            -webkit-font-smoothing: antialiased;
            -webkit-box-direction: normal;
            font-feature-settings: "pnum";
            border-collapse: collapse;
            border-spacing: 0;
            color: #4c4a73;
            box-sizing: border-box;
            background: transparent;
            border: 0;
            font: inherit;
            margin: 0;
            outline: none;
            text-decoration: none;
            z-index: auto;
            align-self: start;
            margin-right: 10%;
            font-size: 1rem;
            line-height: 1.5rem;
            padding: 0;
            text-align: left;
            vertical-align: top;
            text-transform: none;
            letter-spacing: 0;
        }

        .place-img {
            width: 20px;
            height: 20px;
            display: block;
            width: 30px;
            height: 30px;
            display: block;
            margin-right: 10px;
        }

        .meta-row-1{
            background-color: #CCC41B80
        }

        .meta-row-1 .place-img{
            background-image: url(https://gamify-bucket.s3.amazonaws.com/pngaaa.com-267766.png);
            background-size: 100%;
            background-repeat: no-repeat;
        }

        .meta-row-2{
            background-color: #C0C0C080
        }

        .meta-row-2 .place-img{
            background-image: url(https://gamify-bucket.s3.amazonaws.com/pngfind.com-picture-png-2252395.png);
            background-size: 100%;
            background-repeat: no-repeat;
        }

        .meta-row-3{
            background-color: #CD7F3280
        }

        .meta-row-3 .place-img{
            background-image: url(https://gamify-bucket.s3.amazonaws.com/pngfind.com-picture-png-2252470.png);
            background-size: 100%;
            background-repeat: no-repeat;
        }

        .meta-row-label {
            text-size-adjust: 100%;
            -webkit-font-smoothing: antialiased;
            -webkit-box-direction: normal;
            font-feature-settings: "pnum";
            border-collapse: collapse;
            border-spacing: 0;
            color: #4c4a73;
            box-sizing: border-box;
            background: transparent;
            border: 0;
            font: inherit;
            margin: 0;
            outline: none;
            text-decoration: none;
            z-index: auto;
            align-self: start;
            flex: 1;
            font-size: 1rem;
            line-height: 1.5rem;
            padding: 0;
            text-align: left;
            vertical-align: top;
            text-transform: none;
            letter-spacing: 0;
        }

        .meta-row-value {
            text-size-adjust: 100%;
            -webkit-font-smoothing: antialiased;
            -webkit-box-direction: normal;
            color: inherit;
            font-feature-settings: "pnum";
            border-collapse: collapse;
            border-spacing: 0;
            word-break: break-word;
            box-sizing: border-box;
            background: transparent;
            border: 0;
            font: inherit;
            font-size: 100%;
            margin: 0;
            outline: none;
            padding: 0;
            text-align: right;
            text-decoration: none;
            vertical-align: baseline;
            z-index: auto;
        }
    </style>
</head>

<body class="section-projects">
<main class="layout-stacked">
    <div class="layout-stacked__header header">
        <header class="project__header">
            <div class="layout-container">
                <div class="snyk-img" style="
                        display: block;
                        margin-left: auto;
                        margin-right: auto;
                        width: 50%;
                    ">
                        <img src="https://res.cloudinary.com/snyk/image/upload/v1537345894/press-kit/brand/logo-black.png">
                </div>
                <div class="header-wrap">

                    <h1 class="project__header__title">Snyk Vulnerability Scoreboard</h1>

                    <p class="timestamp"> Date: '''+ now.strftime("%m/%d/%Y") +'''</p>
                </div>
                <div class="source-panel">
                    <span>Scanned the following local git project:</span>
                    <ul>
                        <li class="paths">'''+ os.getcwd() +'''</li>

                    </ul>
                </div>

                <div class="meta-counts">

                    <div class="meta-count"> <span>The team has fixed <span>'''+ str(vulns_fixed) +'''</span> vulnerabilities since</span> <span>'''+ startdate.strftime("%m/%d/%Y") +'''</span></div>
                </div><!-- .meta-counts -->
            </div><!-- .layout-container--short -->
        </header><!-- .project__header -->
    </div><!-- .layout-stacked__header -->
    <section class="layout-container">
        <table class="metatable">
            <tbody>

            ''' + dev_markup + '''
            </tbody>
           </table>
       </section>
     </main><!-- .layout-stacked__content -->
    </body>

     </html>
'''

markup_file = open(projDir + '/leaderboard.html', 'w')
markup_file.write(markup)
markup_file.close()

print(dev_dict)
os.system('git checkout ' + starting_branch)
print('All done!')
