# csdc-scoreboard

Scoring prototype based on a butchery of [zxc
dcss-scoreboard](https://github.com/zxc23/dcss-scoreboard) and [Kramin's
logfile api](https://github.com/Kramin42/Crawl-Log-Api).

ebering wrote in his repo: 

"While it may seem like I know what I am doing with this I do not.

I am allergic to frameworks so the way this thing runs is there's gonna be a
`main.py` that fetches the logfiles into the db and then builds the website. Currently
`dldb.py` does the former only. That's gonna be put on a cronjob.

There's also gonna be an `endweek.py` that finalizes a week and handles
promotion and relegation. Also a cronjob."

You'll need sqlalchemy 1.3.24 to make his scripts work.
pip install sqlalchemy=='1.3.24'