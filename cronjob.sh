cd /home/rogga/csdc-scoreboard

python -m venv csdcvenv

source csdcvenv/bin/activate

python addplayers.py

python main.py

# Change to your repository directory
cd /home/rogga/Documents/GitHub/crawl_cosplay

# Add changes
git -C /home/rogga/Documents/GitHub/crawl_cosplay add .

# Commit changes
git -C /home/rogga/Documents/GitHub/crawl_cosplay commit -m "Automated commit"

# Push changes to GitHub
git -C /home/rogga/Documents/GitHub/crawl_cosplay push origin master
