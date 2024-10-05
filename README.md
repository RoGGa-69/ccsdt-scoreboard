# Crawl Cosplay sudden Death Tournament scoreboard

ebering wrote in his repo: 

"Scoring prototype based on a butchery of [zxc
dcss-scoreboard](https://github.com/zxc23/dcss-scoreboard) and [Kramin's
logfile api](https://github.com/Kramin42/Crawl-Log-Api).
While it may seem like I know what I am doing with this I do not.
I am allergic to frameworks so the way this thing runs is there's gonna be a
`main.py` that fetches the logfiles into the db and then builds the website."

You'll need sqlalchemy 1.3.24 to make his scripts work. 
In Ubuntu terminal type:

   pip install sqlalchemy=='1.3.24'

I've made quite a few tweaks to the webpages to make it integrate with the Crawl Cosplay website: cosplay.kelbi.org

If you are thinking of forking this repo, I would suggest you fork ebering's since it work out-of-the-box

A big thank you to scrubdaddy for helping me figure out what to change in the python scripts.
