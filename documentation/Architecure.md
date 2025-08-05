MAIN FOLDER DIRECTORY 

Shift_manager_front_end
-------contains react side of app, shift_manager and history 
	dist
	node_modules
	src
        -----contains source code for the react side
	     pages
	     ------contains most of the code 
		   history 
		    ---contains code for history page 
                              (SEE BELOW FOR MORE DETAILS)
		   EditShift.jsx
		   HistoryDayView.css
	           PlanShift.jsx
	           ViewShifts.jsx
	     hooks
		  UseTransitionPoller.js 
		  
	     assets		

src
-------contains source code for flask side of app (SEE BELOW FOR DETAILS ON SRC)
      
      services
      routes
      static
      templates
      db.py
      plc.py
      globals.py
	
app.py

requirements.txt

matrixapp_v2.db

EXPLANATIONs 

src/ 
-this is regarding the source code for the Flask side of the app

src/routes
	-this folder handles the flask routes connection the html templates together. Each route page is declared as a blueprint 
	in app.py, each route is bottlenecked by auth_id (which is set as 1 for now)
	KEY FEATURES
	-the routes in each folders are what load the templates up with variables, and allow for navigation between screens
	-these routes utilize a variety of db functions to get their data 
	-some routes pass data between eachother 
	