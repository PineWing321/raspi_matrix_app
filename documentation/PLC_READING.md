PLC READING:

-First off, we are reading from the plc to recieve the "truth" on what the system is actually doing 

-this in turn makes it the main determinant of our app 

-THE PLC IS THE TRUTH 

-in PLC.py, we are reading  main flags every second. 

-blocked

-starved

-parts

-rejects

-cycle on 

-cycle off

python dictionary to read off of the plc, the right is the tag location in the plc 
the left is the key name 

TAGS = {
    "cycle_on": "MatrixDataTracking.Status.Running", (BOOL found in plc)
    "cycle_off": "MatrixDataTracking.Status.Stopped", (BOOL found in plc)
    "parts": "MatrixDataTracking.ProductionCounts.Total.ACC",(INT found in plc)
    "rejects": "MatrixDataTracking.ProductionCounts.Fail.ACC",(INT found in plc)
    "starved": "MatrixDataTracking.Status.Starved", (BOOL found in plc)
    "blocked": "MatrixDataTracking.Status.Blocked", (BOOL found in plc)
    "event_flags": "Eventbitvalues",  # ✅ new unified tag (DINT found in plc), transplated to a binary number (256 or 258) 
}

we are using pycomm3 as the library for reading tags
-the speed is not very snappy relative to regular python code,

the plc.read function takes about 100 ms give or take to fire up, one its opened the tags are easily read however

NOTE- IF ADDING ONTO WHAT THE PI IS READING, DONT ADD A NEW ITERATION OF PLC.READ
result = plc.read(
            TAGS["cycle_on"],
            TAGS["cycle_off"],
            TAGS["parts"],
            TAGS["rejects"],
            TAGS["blocked"],
            TAGS["starved"]
        )
       -add onto this one, its very costly to add another plc.read, but adding another parameter is not 
       
-THE EVENT BIT ARRAY is read in get_stop_cause, found in PLC.PY and used in ROUTE_MANAGER.PY


-we read it when the app state changed from machine on to off, this is triggered by cycle_on going from 1 to 0 and cycle_stopped going from 0 to 1

-THE EVENT BIT ARRAY is returned as a number, say 258 
-we read it by converting it so an array of bits like 100000010 (which equals 258 in binary) 
-THE EVNT BIT ARRAY contains common stop events inherent to the system
 bit_map = {
            1: "fence_fault",
            2: "e_stop",
            3: "collision",
            4: "sensor_audit_flag",
            5: "missed_pick",
            6: "missed_placement",
            8: "operator_stop", 
            9: "quality_stop",
        }
        NOTE: 7 is missing since on the d1011 cell it is outfeed full, and that is not a stop event for the cell
-each cause is mapped to a bit in this array
- active_causes = [
            name for bit, name in bit_map.items()
            if value & (1 << bit)
        ]
       
-the code above moves along the given array and adds the value in bit_map to active_causes if its on in the recieved value 

-it is possible to recieve multiple causes, in this scenario we return them, and allow the user to select the real cause 

NOTE***: iF THE EVENT BIT ARRAY IS CHNGED PLC SIDE, IT MUST BE CHANGED PI side

HOW CAN YOU STOP EVENTS TO BE READ

-it is very possible to add things to the bit map, if the event bit array is changed at all on the plc side, it must be adjusted PI side

-if the first member of the event bit array changes from fence fault to e_stop, and fence fault is no longer a common cause found inherent in the system do this 

-the event bit array would be shortend fom 9 bits to 8 
FIRST, change the bit_map 
 bit_map = {
          
            1: "e_stop",
            2: "collision",
            3: "sensor_audit_flag",
            4: "missed_pick",
            5: "missed_placement",
            6: "operator_stop", 
            8: "quality_stop",
        }

-if the cause is determined to need a comment, change flip the need_comment flag true for it in auto_record_stop in src/routes/route_manager.py


SECOND:

go to src/routes/record_stop.html



-THIRD:

In src/templates/record_multiple_causes.html line 54-64, there is a dictionary of lists with a connected reason and require comment flag

-add the cause and its LIKELY connected reason 

NOTE: the linked reason is not always true, it is just auto rendered for flow, the user is always free to change it 

BEFORE
const causeLogic = {
        "fence_fault": { reason: "Non-Machine Related", requireComment: false },
        "e_stop": { reason: "Non-Machine Related", requireComment: false },
        "missed_pick": { reason: "Machine Related", requireComment: false },
        "missed_placement": { reason: "Machine Related", requireComment: false },
        "quality_stop": { reason: "", requireComment: true },
        "collision": { reason: "Machine Related", requireComment: false },
        "sensor_audit_flag": { reason: "Machine Related", requireComment: false },
        "operator_stop": { reason: "", requireComment: false },
        "other": { reason: "", requireComment: true }
    };
 AFTER
const causeLogic = {
        
        "e_stop": { reason: "Non-Machine Related", requireComment: false },
        "missed_pick": { reason: "Machine Related", requireComment: false },
        "missed_placement": { reason: "Machine Related", requireComment: false },
        "quality_stop": { reason: "", requireComment: true },
        "collision": { reason: "Machine Related", requireComment: false },
        "sensor_audit_flag": { reason: "Machine Related", requireComment: false },
        "operator_stop": { reason: "", requireComment: false },
        "other": { reason: "", requireComment: true }
    };




CHANGE AS AUGUST 11
-4 custom signals can be added now each system with user entry

-Code for it has not been completed yet











