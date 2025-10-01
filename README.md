# Repo Miner (RM)

(RM1)  a data-collection pipeline that gathers GitHub commits,
normalizes them, and emit CSVs.

Creates a CSV with columns sha, author, email, date (ISO-8601), message (first line)





\##How to run-

python -m src.repo\_miner fetch-commits --repo owner/repo \[--max (number)] --out commits.csv

