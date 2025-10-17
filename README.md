# Repo Miner (RM)

(RM2) a data-collection pipeline that gathers GitHub commits, issues and
normalizes them, and emit CSVs.
===

Creates a CSV with columns sha, author, email, date (ISO-8601), message (first line)





## How to run -

python -m src.repo\_miner fetch-commits --repo owner/repo \[--max (number)] --out commits.csv





\## RM3 – Data Integration \& Summary



\### Usage



Set a GitHub token:

set GITHUB\_TOKEN=...



Fetch Commits and Issues:

python -m src.repo\_miner fetch-commits --repo octocat/Hello-World --max 100 --out data/commits.csv

python -m src.repo\_miner fetch-issues  --repo octocat/Hello-World --state all --max 50 --out data/issues.csv



Summarize: 

python -m src.repo\_miner summarize --commits commits.csv --issues issues.csv

This prints: 

Top 5 Committers, 

Issue Close rate,

Average Issue open duration (Days, for closed issues only)





