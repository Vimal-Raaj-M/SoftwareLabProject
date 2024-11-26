Prerequisites:
    Fill in the Details in webmail_scrape.py > get_status_and_msg() function

Steps to Setup and Run the Application:
    Making a virtual environment:
        python3 -m venv env
    Activating the Virtual Environment:
        source env/bin/activate
    Installing Requirements:
        pip install -r requirements.txt
    Running the configuration file:
        python3 config.py
    Running the Application:
        python3 app.py

Project Done By:
    Vimal Raaj M: 24M0821
    Bhagawan Panditi: 24M0829
    Ayyagari Sathya Sai Srikar: 24M0741

Creating a project in google cloud console
1. Creating a google project :
    a. OAuth consent screen(configuring the OAuth consent screen )
2. Keeping external so everyone can use:
    a. external:
    b. Available to any test user with a Google Account. App will start in testing mode and will
    only be available to users you add to the list of test users.
3. Update the scope:(to add)
    a. "openid",
    b. "https://www.googleapis.com/auth/userinfo.email",
    c. "https://www.googleapis.com/auth/userinfo.profile",
    d. "https://www.googleapis.com/auth/calendar",
    e. "https://www.googleapis.com/auth/calendar.events"
4. Test users
    a. add a mail id so we can test the application (eg : vimalraaj2001@gmail.com)
5. Generate Client id and Client Secret Key
