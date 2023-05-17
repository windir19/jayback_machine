import threading
import pandas as pd
from time import sleep
from canvasapi import Canvas, course
from automationVariables import *
from automationLogging import *

# Parent Migrate Class
class Migrate(threading.Thread):
    # Adds groups to each of the group categories
    def add_groups(self, from_course, to_course):
        from_group_categories = from_course.get_group_categories()

        for from_group_category in from_group_categories:
            # Create the category in the to_course
            to_group_category = to_course.create_group_category(name=from_group_category.name, group_limit=from_group_category.group_limit)
            
            # Notification of the group category created
            notification_string = "Created \"" + str(from_group_category.name) + "\" Group Set in " + str(to_course.name)
            update_log(notification_string)
            
            groups = from_group_category.get_groups()
            for grp in groups:
                to_group_category.create_group(name=grp.name)
                notification_string = str(grp.name) + " was made in " + str(to_group_category.name)
                update_log(notification_string)

# Child Class to Migrate. Migrates many courses in Canvas
class MigrateSingleCourse(Migrate):
    def __init__(self, api_token, from_course_id, to_course_id, from_start_date, to_start_date):
        super().__init__()
        self._stop_event = threading.Event()
        self.api_token = api_token
        self.from_course_id = from_course_id
        self.to_course_id = to_course_id
        self.from_start_date = from_start_date
        self.to_start_date = to_start_date

    # Migrate one course function
    def run(self):
        canvas = Canvas(API_URL,self.api_token)

        update_log("Migration request to Canvas is beginning...")

        # Create from_course and to_course objects
        from_course = Canvas.get_course(self=canvas, course=self.from_course_id, use_sis_id=False)
        to_course = Canvas.get_course(self=canvas, course=self.to_course_id, use_sis_id=False)
        
        # Runs function to add group categories and groups
        self.add_groups(from_course, to_course)

        # Creates a selective import content migration with date shift
        course_migration = course.Course.create_content_migration(self=to_course,
                                                                  migration_type='course_copy_importer',
                                                                  settings={'source_course_id':self.from_course_id},
                                                                  date_shift_options={'shift_dates':True, 'old_start_date':self.from_start_date, 'new_start_date':self.to_start_date},
                                                                  selective_import=True)
        
        # Updates and Starts the content migration to import all content EXCEPT for Announcements and Calendar Events 
        course_migration.update(copy={"all_course_settings":True,
                                      "all_syllabus_body":True,
                                      "all_context_modules":True,
                                      "all_assignments":True,
                                      "all_quizzes":True,
                                      "all_assessment_question_banks":True,
                                      "all_discussion_topics":True,
                                      "all_wiki_pages":True,
                                      "all_announcements":False,
                                      "all_calendar_events":False,
                                      "all_attachments":True})
        
        migration_id = int(course_migration.id)
        to_course_name = str(to_course.name)

        # Notification of which FROM course is being migrated to which TO course
        update_log(f"Beginning migration of {str(from_course.name)} to {str(to_course.name)}")

        migration_completion = False

        while migration_completion == False:
            # Create migration object to get progress data for class migration 
            migration_instance = to_course.get_content_migration(content_migration=migration_id)
            migration_status = migration_instance.get_progress()
            migration_status = float(migration_status.completion)

            # Notification given based on % of progress on migration_status
            if migration_status < 100.0:
                notification_string = to_course_name + " migration is at " + "{:3.1f}".format(migration_status) + "%"
                update_log(notification_string)
                # Waits 3 seconds before proceeding to check next migration in the list
                sleep(3.0)
            else: 
                migration_completion = True
            
        update_log(f"{to_course_name} migration is DONE.") 

# Child Class to Migrate. Migrates many courses in Canvas
class MigrateMultiCourses(Migrate):
    def __init__(self, api_token, to_start_date, csv_file):
        super().__init__()
        self._stop_event = threading.Event()
        self.api_token = api_token
        self.to_start_date = to_start_date
        self.csv_file = csv_file

    # Checks the CSV file if all of the courses are done migrating
    def check_csv_migrate_completion(self):
        # Creates a dataframe to read from updates CSV
        data_frame = pd.read_csv(self.csv_file)

        for index, row in data_frame.iterrows():
            status = float(row[4])
            
            if status < 100.0:
                update_log("Migration check shows updates are NOT complete yet. Checking migrations again.")
                
                # Waits 5 seconds for before checking migrations in Canvas again 
                sleep(5.0)
                return False      
        
        update_log("Migration check shows migrations ARE complete!")
        return True
    
    # Check migration for multiple courses function
    def check_migrations(self):
        canvas = Canvas(API_URL,self.api_token)
        
        migration_completion = False

        # While loop that checks if migrations in Canvas are completed
        while migration_completion == False:
            
            data_frame = pd.read_csv(self.csv_file)

            cols=('from_course_id', 'from_start_date', 'to_course_id', 'migration_id', 'migration_status')
            new_data_frame = pd.DataFrame(columns=cols)
            
            # Loop through data frame to check all migrating courses in CSV
            for index, row in data_frame.iterrows():
                
                # Define variables from spreadsheet
                from_course_id = row[data_frame.columns.get_loc("from_course_id")]
                from_start_date = row[data_frame.columns.get_loc("from_start_date")]
                to_course_id = row[data_frame.columns.get_loc("to_course_id")]
                migration_id = row[data_frame.columns.get_loc("migration_id")]

                to_course = Canvas.get_course(self=canvas,course=to_course_id,use_sis_id=False)
                
                # Create migration object to get progress data for class migration 
                migration_instance = to_course.get_content_migration(content_migration=migration_id)
                migration_status = migration_instance.get_progress()
                migration_status = float(migration_status.completion)
                
                # Notification given based on % of progress on migration_status
                if migration_status < 100.0:
                    notification_string = str(to_course.name) + " migration is at " + "{:3.1f}".format(migration_status) + "%"
                    update_log(notification_string)
                else:
                    notification_string = str(to_course.name) + " migration is DONE. At "+ "{:3.1f}".format(migration_status) + "%"
                    update_log(notification_string)

                # Create list of values for the row 
                list = [from_course_id, from_start_date, to_course_id, migration_id, migration_status]

                # Turn list into a 'row dataframe'
                new_row = pd.DataFrame(list).T  
                new_row.columns = ['from_course_id', 'from_start_date', 'to_course_id', 'migration_id', 'migration_status']

                # Append the 'row dataframe' to the new dataframe
                new_data_frame = pd.concat([new_data_frame, new_row],axis=0, ignore_index=True)
                new_data_frame.to_csv(path_or_buf=self.csv_file,index=False,index_label=None,mode='w')

                # Waits a second before proceeding to check next migration in the list
                sleep(1.0)
            
            migration_completion = self.check_csv_migrate_completion(self.csv_file)
        
        update_log("Migrations to Canvas DONE!\n")
   
    # Migrate multiple courses function
    def run(self):
        canvas = Canvas(API_URL,self.api_token)

        # Make data frame from spreadsheet
        data_frame = pd.read_csv(self.csv_file)
        data_frame['migration_id'] = None

        # Make a new empty data frame
        cols=('from_course_id', 'from_start_date', 'to_course_id', 'migration_id','migration_status')
        new_data_frame = pd.DataFrame(columns=cols)

        update_log("Migration requests to Canvas are beginning...")

        # Loop through data frame to migrate all courses in CSV
        for index, row in data_frame.iterrows():
            
            # Define variables from spreadsheet
            from_course_id = row[data_frame.columns.get_loc("from_course_id")]
            from_start_date = row[data_frame.columns.get_loc("from_start_date")]
            to_course_id = row[data_frame.columns.get_loc("to_course_id")]

            # Create from_course and to_course objects
            from_course = Canvas.get_course(self=canvas, course=from_course_id, use_sis_id=False)
            to_course = Canvas.get_course(self=canvas, course=to_course_id, use_sis_id=False)
            
            # Runs function to add group categories and groups
            self.add_groups(from_course, to_course)
            
            # Creates a selective import content migration with date shift
            course_migration = course.Course.create_content_migration(self=to_course, 
                                                                    migration_type='course_copy_importer',
                                                                    settings={'source_course_id': from_course_id},
                                                                    date_shift_options={'shift_dates':True, 'old_start_date':from_start_date, 'new_start_date':self.to_start_date},
                                                                    selective_import=True)
            
            # Updates and Starts the content migration to import all content EXCEPT for Announcements and Calendar Events 
            course_migration.update(copy={"all_course_settings":True,
                                          "all_syllabus_body":True,
                                          "all_context_modules":True,
                                          "all_assignments":True,
                                          "all_quizzes":True,
                                          "all_assessment_question_banks":True,
                                          "all_discussion_topics":True,
                                          "all_wiki_pages":True,
                                          "all_announcements":False,
                                          "all_calendar_events":False,
                                          "all_attachments":True})
            
            migration_id = int(course_migration.id)
            
            # create list of values for the row 
            list = [from_course_id, from_start_date, to_course_id, migration_id]

            # turn list into a 'row dataframe'
            new_row = pd.DataFrame(list).T  
            new_row.columns = ['from_course_id', 'from_start_date', 'to_course_id', 'migration_id']

            # Append the 'row dataframe' to the new dataframe
            new_data_frame = pd.concat([new_data_frame, new_row],axis=0, ignore_index=True)
            
            # Notification of which FROM course is being migrated to which TO course
            notification_string = f"Beginning migration of {str(from_course.name)} to {str(to_course.name)}"
            update_log(notification_string)
        
        data_frame.to_csv(path_or_buf=self.csv_file,index=False,index_label=None,mode='w')
        update_log("Migrations complete.\n")