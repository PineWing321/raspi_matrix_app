

FROM ALEX 8/11/2025
-this deployment is for dev, the production enviornment is still being ironed out,





go to folder in the pi to deploy the doc and unzip it 

run this in terimanl 

-sudo apt update
sudo apt install -y python3 python3-venv python3-pip git unzip \
  build-essential nodejs npm
  
 2/ unzip the project where it lives 
 cd ~/Downloads           # or the folder where the zip is
unzip raspi_matrix_app-main.zip
cd raspi_matrix_app-main

3. install dependencies 
python3 -m venv venv
source venv/bin/activate

# If you have a requirements file:
pip install --upgrade pip
pip install -r requirements.txt

NOTE: FOR UNUSED DEPDENCIES JUST DO
 pip install (missing dependency) 

4) Frontend: install & build
From the project root:

bash
Copy
Edit
cd shift_manager_frontend
npm ci || npm install          # installs Vite + deps from package.json
npm run build                  # produces ./dist
cd ..

-once the build is stalled, copy the dist folder in the shift_manager_frontend/src


-navigate away back to the project root

-go to src/static

-paste the dist folder here 

5 run it 

-activate virtual environment 

source venv/bin/activate 

run command from project route 

python app.py













