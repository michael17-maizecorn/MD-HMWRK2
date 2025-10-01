# Repo Miner (RM)

(RM2) a data-collection pipeline that gathers GitHub commits, issues and
normalizes them, and emit CSVs.
=======

Creates a CSV with columns sha, author, email, date (ISO-8601), message (first line)




## How to run -
python -m src.repo_miner fetch-commits --repo owner/repo [--max (number)] --out commits.csv
