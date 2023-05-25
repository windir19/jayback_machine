from dateutil import parser
from pprint import pprint

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter.filedialog import askopenfilename

from canvasapi import Canvas

from automationVariables import *
from automationLogging import *
from automationMigration import MigrateSingleCourse, MigrateMultiCourses
from automationUpdate import UpdateSingleCourse, UpdateMultiCourses

class RequiredInput:
    def __init__(self, frame):
        self.frame = frame

        # TTK Create and add API Access Token widget elements
        api_token_row = ttk.Frame(self.frame)
        api_token_row.pack(fill=X, expand=YES, pady=(0,20))

        self.api_token_label = ttk.Label(api_token_row, text="Access Token")
        self.api_token_label.pack(side=LEFT, fill=X, padx=(0, 10))

        self.api_token = ttk.StringVar(frame)

        self.api_token_entry = ttk.Entry(api_token_row, width=70, textvariable=self.api_token)
        self.api_token_entry.pack(side=LEFT, fill=X, expand=YES)

        # TTK Create and add TO Start Date Calendar widget elements
        to_start_date_row = ttk.Frame(self.frame)
        to_start_date_row.pack(fill=X, pady=(0, 0))    

        self.to_start_date_label = ttk.Label(to_start_date_row, text="TO Course Start Date")
        self.to_start_date_label.pack(side=LEFT, padx=(0, 30))

        self.to_start_date_entry = ttk.DateEntry(to_start_date_row,startdate=TO_DATEENTRY_START_DATE)
        self.to_start_date_entry.pack(side=LEFT)
    
    # Get TO Course Start Date from Field formatted to datetime in US/Central Time
    def get_to_start_date(self):
        start_date = self.to_start_date_entry.entry.get()
        update_log("DateEntry TO Date string: " + str(start_date))
        start_date = datetime.strptime(start_date, '%m/%d/%y')
        start_date = start_date.replace(hour=0, minute=0, second=0, tzinfo='US/Central')
        update_log("Datetime: " + str(start_date) + " " + str(start_date.tzname))
        return start_date

    # Get TO Course Start Date from Field formatted to ISO String format
    def get_to_start_date_str(self):
        start_date = self.to_start_date_entry.entry.get()
        start_date = str(parser.parse(start_date))
        return start_date

class Options:
    def __init__(self, frame):
        self.frame = frame
        
        row1 = ttk.Frame(self.frame)
        row1.pack(fill=X, expand=YES, pady=(0,20))

        self.sb_weeks_to_start_checkbtn_value = ttk.IntVar()

        self.sb_weeks_to_start_checkbtn = ttk.Checkbutton(row1, text="Spring Break is on week:", 
                                                          onvalue=1, offvalue=0,
                                                          variable=self.sb_weeks_to_start_checkbtn_value,
                                                          command=self.sb_weeks_to_start_entry_state)
        self.sb_weeks_to_start_checkbtn.pack(side=LEFT, fill=X, padx=(0, 10))
        self.sb_weeks_to_start_checkbtn.state(['!alternate'])

        self.sb_start_week = ttk.StringVar(frame, value=8)

        self.sb_weeks_to_start_entry = ttk.Spinbox(row1, textvariable=self.sb_start_week,
                                                   width=10,
                                                   from_=0, to=15,
                                                   wrap=True)
        self.sb_weeks_to_start_entry.pack(side=LEFT, fill=X)
        self.sb_weeks_to_start_entry["state"] = "disabled"
    
    def sb_weeks_to_start_entry_state(self):
        if self.sb_weeks_to_start_checkbtn_value.get() == 1:
            self.sb_weeks_to_start_entry["state"] = "normal"
        else:
            self.sb_weeks_to_start_entry["state"] = "disabled"


class ModeButtons:
    def __init__(self, frame, single_update_input, multi_update_input):
        self.frame = frame
        self.single_update_input = single_update_input
        self.multi_update_input = multi_update_input

        mode_btn_label = ttk.Label(self.frame, text="Choose the type of migration/update")
        mode_btn_label.pack(side=LEFT, padx=(7, 10))

        self.single_course_btn = ttk.Button(
            self.frame,
            text="Single Course", 
            command=self.set_single_course
            )
        self.single_course_btn.pack(padx=(0, 0), side=LEFT)

        self.multi_course_btn = ttk.Button(
            self.frame, 
            text="Multiple Courses", 
            command=self.set_multi_course
            )
        self.multi_course_btn.pack(padx=(10, 0), side=LEFT)
        self.multi_course_btn.config(state="disabled")

    def set_single_course(self):
        global SELECT_MULTIPLE_MIGRATION
        SELECT_MULTIPLE_MIGRATION = False
        
        self.single_course_btn.config(bootstyle=PRIMARY)
        self.multi_course_btn.config(bootstyle=SECONDARY)

        self.single_update_input.enable()
        self.multi_update_input.disable()
        
    def set_multi_course(self):
        global SELECT_MULTIPLE_MIGRATION
        SELECT_MULTIPLE_MIGRATION = True

        self.single_course_btn.config(bootstyle=SECONDARY)
        self.multi_course_btn.config(bootstyle=PRIMARY)

        self.single_update_input.disable()
        self.multi_update_input.enable()


class RunButtons:
    def __init__(self, frame, root, main_app, mode_buttons, required_input, options_input, single_update_input, multi_update_input):
        self.frame = frame
        self.root = root
        self.main_app = main_app
        self.mode_buttons = mode_buttons
        self.required_input = required_input
        self.options_input = options_input
        self.single_update_input = single_update_input
        self.multi_update_input = multi_update_input 

        self.required_input.api_token.trace("w", self.api_token_entry_change)

        self.close_btn = ttk.Button(self.frame, 
                                    text="Close", 
                                    command=self.close)
        self.close_btn.pack(side=RIGHT, padx=(10, 0))

        self.start_update_btn = ttk.Button(self.frame, 
                                           text="Start Updates", 
                                           command=self.run_update)
        self.start_update_btn.pack(side=RIGHT, padx=(10, 0))

        self.start_migration_btn = ttk.Button(self.frame,
                                              text="Start Migration", 
                                              command=self.run_migration)
        self.start_migration_btn.pack(side=RIGHT, padx=(10, 0))

        self.check_api_token_btn = ttk.Button(self.frame,
                                              text="Check Access Token", 
                                              command=self.check_api_token)
        self.check_api_token_btn.pack(side=RIGHT, padx=(0, 0))

    def check_api_token(self):
        try:
            canvas = Canvas(API_URL, self.required_input.api_token.get())
            current_user = canvas.get_current_user()
            update_log(f"Hello {current_user.name}! You are ready to use the scripts.")
            self.enable_run_buttons()
            self.check_api_token_btn.config(bootstyle = "primary")
            self.required_input.api_token_entry.config(bootstyle = "success")
            self.required_input.api_token_label.config(bootstyle = "success")
        except:
            update_log("Access Token is not correct for Canvas access to use the scripts.")
            self.api_token_entry_change()

    # Run Migration script
    def run_migration(self):    
        self.disable_run_buttons()
        
        api_token = self.required_input.api_token.get()
        to_start_date = self.required_input.get_to_start_date_str()
        
        if SELECT_MULTIPLE_MIGRATION:
            csv_file_address = self.multi_update_input.filename.get()

            migrate_multi_courses = MigrateMultiCourses(api_token, csv_file_address, to_start_date)
            migrate_multi_courses.start()
            
        else:
            from_course_id = self.single_update_input.from_course.get()
            to_course_id = self.single_update_input.to_course.get()
            from_start_date = self.single_update_input.get_from_start_date_str()

            migrate_single_course = MigrateSingleCourse(api_token, from_course_id, to_course_id, from_start_date, to_start_date)
            migrate_single_course.start()
        
        self.enable_run_buttons()
        
    # Run Update script   
    def run_update(self):        
        self.disable_run_buttons()

        api_token = self.required_input.api_token.get()
        to_start_date = self.required_input.get_to_start_date_str()
        sb_start_week = int(self.options_input.sb_start_week.get())

        if SELECT_MULTIPLE_MIGRATION:
            update_log("Updates beginning. Please wait...")
            csv_file_address = self.multi_update_input.get_file_address_str()
            update_multi_courses = UpdateMultiCourses(api_token, to_start_date, csv_file_address, sb_start_week)
            update_multi_courses.start()
        else:
            update_log("Update beginning. Please wait...")
            from_course_id = self.single_update_input.from_course.get()
            to_course_id = self.single_update_input.to_course.get()
            from_start_date = self.single_update_input.get_from_start_date_str()
            update_single_course = UpdateSingleCourse(api_token, from_course_id, to_course_id, from_start_date, to_start_date, sb_start_week)
            update_single_course.start()
        
        self.enable_run_buttons()
        
    def api_token_entry_change(self, *args):
        self.check_api_token_btn.config(bootstyle = "success")
        self.required_input.api_token_entry.config(bootstyle = "danger")
        self.required_input.api_token_label.config(bootstyle = "danger")
        self.disable_run_buttons()

    # Disables Migration and Update run buttons
    def enable_run_buttons(self):
        self.start_migration_btn.config(state="normal")
        self.start_update_btn.config(state="normal")

    # Enables Migration and Update run buttons
    def disable_run_buttons(self):
        self.start_migration_btn.config(state="disabled")
        self.start_update_btn.config(state="disabled")
        
    # Closes window and program. Saves simple log on close.
    def close(self):
        self.main_app.save_simple_log()
        self.root.destroy()


class SingleUpdateInput:
    def __init__(self, frame):
        self.frame = frame
        self.from_course = ttk.StringVar(frame)
        self.to_course = ttk.StringVar(frame)

        # TTK Create and add TO and FROM Course widget elements
        course_id_input_row = ttk.Frame(self.frame)
        course_id_input_row.pack(fill=X, expand=YES, pady=(0,20))
    
        self.from_course_label = ttk.Label(course_id_input_row, text="FROM Course ID")
        self.from_course_label.pack(side=LEFT, fill=X, padx=(0, 10))

        self.from_course_entry = ttk.Entry(course_id_input_row, textvariable=self.from_course)
        self.from_course_entry.pack(side=LEFT, fill=X, expand=YES)

        self.to_course_label = ttk.Label(course_id_input_row, text="TO Course ID")
        self.to_course_label.pack(side=LEFT, fill=X, padx=(10, 10))

        self.to_course_entry = ttk.Entry(course_id_input_row, textvariable=self.to_course)
        self.to_course_entry.pack(side=LEFT, fill=X, expand=YES)

        # TTK Create and add Start Date Calendar widget elements
        from_start_date_row = ttk.Frame(self.frame)
        from_start_date_row.pack(fill=X, pady=(0, 0))    

        self.from_start_date_label = ttk.Label(from_start_date_row, text="FROM Course Start Date")
        self.from_start_date_label.pack(side=LEFT, padx=(0, 10))

        self.from_start_date_entry = ttk.DateEntry(from_start_date_row,startdate=FROM_DATEENTRY_START_DATE)
        self.from_start_date_entry.pack(side=LEFT)

    def enable(self):
        self.to_course_entry["state"] = "normal"
        self.from_course_entry["state"] = "normal"
        self.from_start_date_entry["state"] = "normal"

        self.frame.config(bootstyle = "default")
        self.to_course_label.config(bootstyle = "default")
        self.from_course_label.config(bootstyle = "default")
        self.from_start_date_label.config(bootstyle = "default")

    def disable(self):
        self.to_course_entry.delete(0, END)
        self.from_course_entry.delete(0, END)
        
        self.to_course_entry["state"] = "disabled"
        self.from_course_entry["state"] = "disabled"
        self.from_start_date_entry["state"] = "disabled"
        
        self.frame.config(bootstyle = "danger")
        self.to_course_label.config(bootstyle = "danger")
        self.from_course_label.config(bootstyle = "danger")
        self.from_start_date_label.config(bootstyle = "danger")

    # Get FROM Course Start Date from Field formatted to datetime in US/Central Time
    def get_from_start_date(self):
        start_date = self.from_start_date_entry.entry.get()
        update_log("DateEntry FROM Date string: " + str(start_date))
        start_date = datetime.strptime(start_date, '%m/%d/%y')
        start_date = start_date.replace(hour=0, minute=0, second=0, tzinfo='US/Central')
        update_log("Datetime: " + str(start_date) + " " + str(start_date.tzname))
        return start_date

    # Get FROM Course Start Date from Field formatted in ISO String format
    def get_from_start_date_str(self):
        start_date = self.from_start_date_entry.entry.get()
        start_date = str(parser.parse(start_date))
        return start_date

class MultiUpdateInput:
    def __init__(self, frame):
        self.frame = frame
        self.filename = ttk.StringVar()

        browse_row = ttk.Frame(self.frame)
        browse_row.pack(fill=X, expand=YES, pady=(0,15))

        self.browse_label = ttk.Label(browse_row, text="Course .csv")
        self.browse_label.pack(side=LEFT, padx=(0, 25))

        self.browse_entry = ttk.Entry(browse_row, textvariable=self.filename)
        self.browse_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))

        self.browse_button = ttk.Button(master=browse_row,
                                        text="Browse", 
                                        command=self.on_browse,
                                        width=8,
                                        bootstyle="primary")
        self.browse_button.pack(side=LEFT, padx=(5, 0))
    
    def on_browse(self):
        path = askopenfilename(title="Choose CSV file", filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        with open(path, encoding='utf-8') as f:
            self.filename.set(path)

    def enable(self):
        self.browse_entry["state"] ="normal"
        self.browse_button["state"] ="normal"

        self.frame.config(bootstyle = "default")
        self.browse_label.config(bootstyle = "default")

    def disable(self):
        self.browse_entry.delete(0, END)
        
        self.browse_entry["state"] = "disabled"
        self.browse_button["state"] = "disabled"

        self.frame.config(bootstyle = "danger")
        self.browse_label.config(bootstyle = "danger")