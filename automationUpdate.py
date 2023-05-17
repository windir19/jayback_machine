import re
import arrow
import threading
import pandas as pd
from datetime import datetime, timedelta
from canvasapi import Canvas
from bs4 import BeautifulSoup
from automationVariables import *
from automationLogging import *

class Update(threading.Thread):
    # Function to remove extra spaces from module titles
    def remove_title_spaces(self, to_course):
        # Sub-function that returns a string with extra spaces removed
        def remove_spaces(title_string):
            return str(re.sub(' +', ' ', title_string))
        
        update_log("Clearing extra spaces from titles of all modules, pages and assignments.") 

        # Clearing spaces from all modules
        to_modules = to_course.get_modules()
        for class_module in to_modules:
            if bool(re.search(' {2,}', str(class_module.name))):
                module_name = remove_spaces(str(class_module.name))
                class_module.edit(module={'name': module_name})
                update_log(f"{str(class_module.name)} changed to {module_name}") 
            else:
                update_log(f"{str(class_module.name)} contains no extra spaces.") 
        
        # Clearing spaces from all pages
        to_pages = to_course.get_pages(per_page=200)
        for page in to_pages:
            if bool(re.search(' {2,}', str(page.title))):
                page_name = remove_spaces(str(page.title))
                page.edit(page={'title': page_name})
                update_log(f"{str(page.title)} changed to {page_name}") 
            else:
                update_log(f"{str(page.title)} contains no extra spaces.") 

        # Clearing spaces from all assignments
        to_assignments = to_course.get_assignments(per_page=200)
        for assignment in to_assignments:
            if bool(re.search(' {2,}', str(assignment.name))):
                assignment_name = remove_spaces(str(assignment.name))
                assignment.edit(assignment={'name': assignment_name})
                update_log(f"{str(assignment.name)} changed to {assignment_name}") 
            else:
                update_log(f"{str(assignment.name)} contains no extra spaces.") 

        update_log("DONE clearing extra spaces from titles of all modules, pages and assignments.") 

    # Change Module Names
    def change_module_names(self, to_course, to_start_date, spring_break_status:int):
        to_modules = to_course.get_modules()
        
        #Checks through all course modules to change the name
        for index, class_module in enumerate(to_modules, start=0):
            # Removes existing Module Name extra spaces
            module_name = str(class_module.name)
            week_span_in_module = bool(re.search(WEEK_SPAN_REGEX, module_name))

            if week_span_in_module:
                #Create week span string 
                add_days = int(index) * 7
                week_span = datetime.fromisoformat(str(to_start_date))

                if index > 6 and spring_break_status == 1:
                        week_span = week_span + timedelta(days=7)

                # Creates datetimes for beginning of the week and end of the week
                week_span += timedelta(days=add_days)
                week_span_end = week_span + timedelta(days=6)
                
                # Make week span string ie. Month # - Month #
                week_span = week_span.strftime("%b %d")
                week_span = re.sub(r'0+(.+)', r'\1', week_span)

                week_span_end = week_span_end.strftime("%b %d")
                week_span_end = re.sub(r'0+(.+)', r'\1', week_span_end)

                week_span = f"{week_span} - {week_span_end}"
                
                # Finds week span to replace name 
                module_name = re.sub(WEEK_SPAN_REGEX, str(week_span), module_name)
                
                if module_name not in str(class_module.name):
                    class_module.edit(module={'name':module_name})
                    notification_string = str(class_module.name) + " to " + module_name
                    update_log(notification_string) 

            else:
                update_log(f"{module_name} contains no week span. Skipping module name update.") 

    # Function to change Library Course Page links in pages to match current Canvas course ID
    def link_change_library_cmp(self, to_course):
        to_pages = to_course.get_pages(per_page=200)

        for page in to_pages:
                current_page = to_course.get_page(page.page_id)
                current_page_content = current_page.body
                soup = BeautifulSoup(current_page_content, 'html.parser')
                
                for link in soup.find_all('a'):
                        link_href = link.get('href')
                        if bool(re.search(LIBRARY_EXT_REGEX, link_href)):
                                link_new_href = re.sub(LIBRARY_EXT_REGEX, str(to_course.id), link_href)
                                link['href'] = link['href'].replace(link_href,link_new_href)
                                page.edit(wiki_page = {'body':str(soup)})
                                update_log(f"Changed course id in link for Library Course Materials for {str(current_page.title)}")       
    
    # Checks to see if Spring Break Shift. Returns 0 to Remove, 1 to Add, None if Not Needed
    def check_spring_break_shift(self, from_course, to_course):
        from_course_name = str(from_course.name)
        to_course_name = str(to_course.name)

        if re.search(r"Spring", from_course_name):
            if re.search(r"Summer|Fall", to_course_name):
                return 0
        elif re.search(r"Summer|Fall", from_course_name) and re.search(r"Spring", to_course_name):
            return 1

        return None

    # Function to create and publish the Spring Break module
    def sp_create_module(self, to_course, to_start_date):
        week_span = datetime.fromisoformat(to_start_date)
        week_span += timedelta(days=49)
        week_span_end = week_span + timedelta(days=6)
        
        spring_break_title = str("Spring Break: " + week_span.strftime("%b %d") + " - " + week_span_end.strftime("%b %d"))
        spring_break_title = re.sub(r'0+(.+)', r'\1', spring_break_title)
        spring_break_module = to_course.create_module(module = {'name' : spring_break_title, 'position' : 8})
        spring_break_module.edit(module = {'published' : True})
        
        spring_break_module_item = spring_break_module.create_module_item(module_item = {'title' : 'There are no assignments due this week', 'type' : 'SubHeader'})
        spring_break_module_item.edit(module_item = {'published' : True})

        update_log(f"{spring_break_title} module created and published.") 

    # Function to delete Spring Break module
    def sb_delete_module(self, to_course):
        to_course_modules = to_course.get_modules()
        
        # Checks through all course modules
        for class_module in to_course_modules:
            module_name = str(class_module.name)
    
            # If it finds "Spring Break", it is removed and removal is notified
            if "Spring Break" in module_name:
                class_module.delete()
                update_log("Deleted old Spring Break Module")

    def sb_date_shift(self, date, spring_break_status:int):
        if spring_break_status == 0:  
            return date.shift(days=-7)
        elif spring_break_status == 1:  
            return date.shift(days=+7)
    """
    The problem I think is in the sb_assignment, sb_quiz, and sb_todo shift functions. Part of the reason they are different functions is: depending on how you shift dates means you have to account
    for the due date being logically between the unlock and lock dates. Also each function then calls upon different .edit() functions with the Canvas API. 
    I realize there is a lot of redundancies but my lack of knowledge in Python makes me struggle to try to find a way to make it more Pythonic or even the words to research a better way of doing this.
    The only thing in scope now is why the date for week 7 are erroneously getting  getting copied forward when adding Spring Break (There is no problems when removing Spring Break).
    """
    # Function for Assignment Spring Break Lock-At "Availible Until" date shift
    def sb_assignment_lock_at_shift(self, assignment, week_start, spring_break_status:int):
        if assignment.lock_at != None:
            lock_date = arrow.get(assignment.lock_at_date).to("US/Central")
            
            if lock_date > week_start:
                update_log(f"{assignment.name} OLD availible from date: {str(assignment.lock_at_date)}") 
                lock_date = self.sb_date_shift(lock_date, spring_break_status)
                assignment.edit(assignment={'lock_at':lock_date})
                update_log(f"{str(assignment.name)} NEW availible from date: {str(assignment.lock_at_date)}")
                    
    # Function for Assignment Spring Break Due date shift
    def sb_assignment_due_date_shift(self, assignment, week_start, spring_break_status:int):
        if assignment.due_at != None:
            due_date = arrow.get(assignment.due_at_date).to("US/Central")

            if due_date > week_start:
                update_log(f"{str(assignment.name)} OLD due date: {str(assignment.due_at_date)}") 
                due_date = self.sb_date_shift(due_date, spring_break_status)
                assignment.edit(assignment={'due_at':due_date})
                update_log(f"{str(assignment.name)} NEW due date: {str(assignment.due_at_date)}") 
                    
    # Function for Assignment Spring Break Unlock-At "Availible From" date shift
    def sb_assignment_unlock_at_shift(self, assignment, week_start, spring_break_status:int):
        if assignment.unlock_at != None:
            unlock_date = arrow.get(assignment.unlock_at_date).to("US/Central")
            
            if unlock_date > week_start:
                update_log(f"{assignment.name} OLD until date: {str(assignment.unlock_at_date)}") 
                unlock_date = self.sb_date_shift(unlock_date, spring_break_status)
                assignment.edit(assignment={'unlock_at': unlock_date})
                update_log(f"{str(assignment.name)} NEW until date: {str(assignment.unlock_at_date)}") 

    # Function for Quiz Spring Break Lock-At "Availible Until" date shift
    def sb_quiz_lock_at_shift(self, quiz, week_start, spring_break_status:int):
        if quiz.lock_at != None:
            lock_date = arrow.get(quiz.lock_at_date).to("US/Central")
            
            if lock_date > week_start:
                update_log(f"{quiz.title} OLD availible from date: {str(quiz.lock_at_date)}") 
                lock_date = self.sb_date_shift(lock_date, spring_break_status)
                quiz.edit(quiz={'lock_at':lock_date})
                update_log(f"{str(quiz.title)} NEW availible from date: {str(quiz.lock_at_date)}")
                    
    # Function for Quiz Spring Break Due date shift
    def sb_quiz_due_date_shift(self, quiz, week_start, spring_break_status:int):
        if quiz.due_at != None:
            due_date = arrow.get(quiz.due_at_date).to("US/Central")

            if due_date > week_start:
                update_log(f"{str(quiz.title)} OLD due date: {str(quiz.due_at_date)}") 
                due_date = self.sb_date_shift(due_date, spring_break_status)
                quiz.edit(quiz={'due_at':due_date})
                update_log(f"{str(quiz.title)} NEW due date: {str(quiz.due_at_date)}") 
                    
    # Function for Quiz Spring Break Unlock-At "Availible From" date shift
    def sb_quiz_unlock_at_shift(self, quiz, week_start, spring_break_status:int):
        if quiz.unlock_at != None:
            unlock_date = arrow.get(quiz.unlock_at_date).to("US/Central")
            
            if unlock_date > week_start:
                update_log(f"{quiz.title} OLD until date: {str(quiz.unlock_at_date)}") 
                unlock_date = self.sb_date_shift(unlock_date, spring_break_status)
                quiz.edit(quiz={'unlock_at': unlock_date})
                update_log(f"{str(quiz.title)} NEW until date: {str(quiz.unlock_at_date)}") 

    # Function for Spring Break To-do date shift
    def sb_todo_shift(self, page, week_start, spring_break_status:int):
        if page.todo_date != None:
            todo_date = arrow.get(page.todo_date_date).to("US/Central")
            
            if todo_date > week_start:
                update_log(f"{str(page.title)} OLD to-do date: {str(page.todo_date_date)}")
                todo_date = self.sb_date_shift(todo_date, spring_break_status)
                page.edit(wiki_page = {'student_todo_at':todo_date})
                update_log(f"{str(page.title)} NEW to-do date: {str(page.todo_date_date)}") 

    # Function that shifts dates for assignments and pages
    def spring_break_shift(self, to_course, to_start_date, spring_break_status:int):
        
        def shift_pages(to_pages, week_start, spring_break_status):
            for page in to_pages:
                self.sb_todo_shift(page, week_start, spring_break_status)

        to_assignments = to_course.get_assignments(per_page=200)
        to_quizzes = to_course.get_quizzes(per_page=200)
        to_pages = to_course.get_pages(per_page=200)

        week_start = datetime.fromisoformat(to_start_date)
        week_start = arrow.get(week_start).to("US/Central")
        week_start += timedelta(days=49)

        if spring_break_status == 0:
            week_start += timedelta(days=7)
            """
            The reason the 3 functions are called in each loop the different orders is to account for the fact that Canvas throws an error if the due date is out of bounds between the unlock and lock dates. 
            Depending on whether spring break is added or removed means the order the functions are called for each assignments (assignments and discussions) and quizzes matters. 
            Any advice on how to simplify or optimize this is welcome as well.
            """
            for assignment in to_assignments:
                self.sb_assignment_unlock_at_shift(assignment, week_start, spring_break_status)
                self.sb_assignment_due_date_shift(assignment, week_start, spring_break_status)
                self.sb_assignment_lock_at_shift(assignment, week_start, spring_break_status)
            for quiz in to_quizzes:
                self.sb_quiz_unlock_at_shift(quiz, week_start, spring_break_status)
                self.sb_quiz_due_date_shift(quiz, week_start, spring_break_status)
                self.sb_quiz_lock_at_shift(quiz, week_start, spring_break_status)
            
            shift_pages(to_pages, week_start, spring_break_status)
            update_log("Completed shifting dates from Spring Break removal") 
        
        elif spring_break_status == 1:
            self.sp_create_module(to_course, to_start_date)
            
            for assignment in to_assignments:
                self.sb_assignment_lock_at_shift(assignment, week_start, spring_break_status)
                self.sb_assignment_due_date_shift(assignment, week_start, spring_break_status)
                self.sb_assignment_unlock_at_shift(assignment, week_start, spring_break_status)
            for quiz in to_quizzes:
                self.sb_quiz_lock_at_shift(quiz, week_start, spring_break_status)
                self.sb_quiz_due_date_shift(quiz, week_start, spring_break_status)
                self.sb_quiz_unlock_at_shift(quiz, week_start, spring_break_status)
            
            shift_pages(to_pages, week_start, spring_break_status)
            update_log("Completed shifting dates from Spring Break addition")

# Child Class to Update. Updates a single course in Canvas.
class UpdateSingleCourse(Update):
    def __init__(self, api_token, from_course_id, to_course_id, from_start_date, to_start_date):
        super().__init__()
        self._stop_event = threading.Event()
        self.api_token = api_token
        self.from_course_id = from_course_id
        self.to_course_id = to_course_id
        self.from_start_date = from_start_date
        self.to_start_date = to_start_date
    
    # Update single course function
    def run(self):
        canvas = Canvas(API_URL,self.api_token)

        from_course = Canvas.get_course(self=canvas,course=self.from_course_id,use_sis_id=False)
        to_course = Canvas.get_course(self=canvas,course=self.to_course_id,use_sis_id=False)

        spring_break_status = self.check_spring_break_shift(from_course, to_course)

        self.remove_title_spaces(to_course)
        self.sb_delete_module(to_course)
        self.change_module_names(to_course, self.to_start_date, spring_break_status)
        
        if spring_break_status != None:
            self.spring_break_shift(to_course, self.to_start_date, spring_break_status)
        else:
            update_log("No Spring Break shift required.") 

        update_log(f"{str(to_course.name)} update is complete!")

# Child Class to Update. Updates many courses in Canvas.
class UpdateMultiCourses(Update):
    def __init__(self, api_token, to_start_date, csv_file):
        super().__init__()
        self._stop_event = threading.Event()
        self.api_token = api_token
        self.to_start_date = to_start_date
        self.csv_file = csv_file

    # Update multiple courses function
    def run(self):
        canvas = Canvas(API_URL,self.api_token)

        # Make data frame from spreadsheet
        data_frame = pd.read_csv(self.csv_file)

        # Loop through data frame to migrate each course
        for index, row in data_frame.iterrows():
            # Define variables from spreadsheet
            from_course_id = row[data_frame.columns.get_loc("from_course_id")]
            to_start_date = row[data_frame.columns.get_loc("old_start_date")]
            to_course_id = row[data_frame.columns.get_loc("to_course_id")]

            from_course = Canvas.get_course(self=canvas,course=from_course_id,use_sis_id=False)
            to_course = Canvas.get_course(self=canvas,course=to_course_id,use_sis_id=False)

            spring_break_status = self.check_spring_break_shift(from_course, to_course)

            self.remove_title_spaces(to_course)
            self.sb_delete_module(to_course)
            self.change_module_names(to_course, to_start_date, spring_break_status)
            
            if spring_break_status != None:
                self.spring_break_shift(to_course, to_start_date, spring_break_status)
            else:
                update_log("No Spring Break shift required.") 

            update_log(f"{str(to_course.name)} update is complete!")

        update_log("Updates complete.\n")