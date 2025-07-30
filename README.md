Vehicle Parking App — Student Project
What is This?


This is my vehicle parking web app created for my college course project. The app helps manage parking lots for 4-wheelers, lets users book parking spots, and lets an admin add or remove lots and see everything going on. It’s built with Flask (Python), uses SQLite for storing data, and looks nice thanks to Bootstrap and some custom CSS.

Features
Admin (superuser):
Log in with a fixed username and password (no registration needed).

Add new parking lots (just give name, price, address, pin, and spots).

Automatically makes parking spots for each new lot (no need to add one by one).

Delete a lot (only if no one is parked inside it).

See all registered users.

See each spot’s status (occupied or available).

User:
Can register and log in.

Search for parking lots by location.

Reserve a spot (just pick a lot; the system picks your spot).

Enter vehicle number when booking.

Start and end (release) their parking, so time and cost are calculated.

See their booking history and how much they spent.

Edit their own profile info.

Tech Used
Python 3, Flask (the web part)

SQLite (the database, handled by the app itself)

Jinja2 (for HTML templates)

Bootstrap 5 + my own CSS

How the Folders Are Organized
text
vehicle_parking_app/
├── app.py                # The main code file
├── requirements.txt      # Stuff to install (Flask, etc.)
├── README.md             # This file!
├── /instance             # Auto-created app.db after running
├── /static
│   └── /css/style.css    # Your stylesheet
└── /templates            # All the HTML files
    ├── base.html
    ├── login.html
    ├── register.html
    ├── admin_dashboard.html
    ├── add_lot.html
    ├── user_dashboard.html
    ├── reserve_spot.html
    ├── profile.html
    └── search_results.html
How to Run This Project
Install requirements
Open terminal in the project folder and run:

text
pip install flask
Start the app
In the same terminal:

text
python app.py
The first time you run this, the database will be created automatically.

Open in browser:
Go to http://127.0.0.1:5000/
You should see the login page.

Admin Account
Username: admin

Password: admin123

You can log in as admin right from the start, no registration needed!

How to Use
Register as a user, log in, and book a parking spot!

Admins can add new lots and see what users are doing.

Try searching for lots by part of the location name using the search bar.

Release your spot when done to see the total cost.

Extra Info / Notes
Database gets created by running app.py, no tools needed.

If you get stuck or see any errors, restart with python app.py.

No manual setup for the database — it's all coded!

Possible Improvements
Could add charts for admin to see usage visually (I didn't finish this).

Some form validation and better error messages would make the app nicer.

Passwords are stored plain text (not secure, but OK for course project).
