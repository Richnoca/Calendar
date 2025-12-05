# Running Calendar with Garmin activity and training plan support

This Python GUI provides an interactive running calendar that inegrates with Garmin Connect to display your past 365 days worth of running activities. It also has the ability to plan future runs by merging .CSV files into your calendar to show you all the runs you have in a training block, instead of having to write it down in a journal.

**IF YOU WISH TO LOOK AT MORE (OR LESS) THAN 365 DAYS WORTH OF DATA, YOU CAN BY ADJUSTING YOUR CODE LOCALLY**
**ON LINE 12 OF THE Calendar.py file, FIND "YEAR_LOOKBACK = 365" AND CHANGE THE 365 TO HOWEVER MANY DAYS YOU LIKE**
**MORE THAN 365 DAYS MAY REQUIRE LONGER LOADING TIMES DEPENDING ON YOUR DEVICE**

Steps For personal use of this Calendar:

1. Download this repository
2. Install Python (Version 3.9 was used during the creation of this)
3. install required packages (can be done in your teminal)
     - pip install tk tkcalendar garminconnect



File Structure for this repository in your folders should be:

  running_calendar/
│
├── plans/                       # CSV training plans
│   └── halhigdon_marathon_plan.csv
├── garmin_config.json            # Stores Garmin login credentials
├── run_evals.json                # Stores self-evaluations
├── Calendar.py                   # Main calendar application

- All of your training plans should be saved in the plans folder as .CSV files in the same format as the ones in this repository
- See subfolder plans with 2 example .CSV files 'halhigdon_intermediate_10k' and 'halhigdon_novice_marathon'.
- If you're unsure how to generate your own .CSV file, find a plan you like and you can Copy and Paste it into ChatGPT and it will generate a           downloadable file that you can save into your own plans folder.

Example of a 3 week snippet .CSV file format:
Week,Mon,Tue,Wed,Thu,Fri,Sat,Sun
1,3 mi run,3 mi run,35 min tempo run,3 mi run,Rest,60 min cross,4 mi run
2,3 mi run,3.5 mi run,8×400 @ 5K pace,4 mi run,Rest,60 min cross,5 mi run
3,3 mi run,4 mi run,40 min tempo run,3 mi run,Rest,60 min cross,6 mi run

# USING THE WIDGET

**YOU MUST HAVE A GARMIN CONNECT ACCOUNT TO USE THIS WIDGET**
**GARMIN CONNECT ACCOUNTS ARE FREE, BUT WITHOUT A GARMIN DEVICE YOU WILL BE UNABLE TO SEE PAST RUN ACTIVITIES**
**EVEN IF YOU DONT HAVE A GARMIN DEVICE YOU CAN STILL UTILIZE THE TRAINING PLAN FEATURE**

- To run the application, in your terminal type 'python running_calendar.py'
- you will be prompted to enter your Garmin Connect login credentials (Email and Password)
    -Credentials will be saved locally to your garmin_config.json to enable staying logged in.
    -If you wish to erase your login information, delete garmin_config.json contents and save which will prompt you for credentials next time.
- Successful login will immediately start the activity retrieval process and placed into their cooresponding Calendar dates.
- Open the drop down to select a training plan you'd like to implement and click the 'Start Plan' button.
    -Plan will start on whatever day you currently have highlighted
- The 'Clear Plan' button will remove the plan from your calendar if you would like to choose a different start date or different plan.
- On days that you have runs you can type in the 'Self-Evaluation' box and click Save Self-Evaluation so you can go back and look at how you felt    during those runs.
    -If you wish to clear a previously saved Self-Evaluation, go into you local run_evals.json and you can edit any evaluation there and they are            listed by date.




  <img width="977" height="784" alt="image" src="https://github.com/user-attachments/assets/9243806a-af93-40b8-a0c6-a60ac0849622" />
