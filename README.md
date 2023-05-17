# The Jayback Machine

A Canvas Migration and Update Automation Script for UMN-CCAPS Canvas LMS courses.

Developed by Paul McLagan, Annika Moe, and Avery Pierce-McGovern

The list of specific functions:
- A simple GUI interface to enter information for the migration and update process as well as select the mode for a single or multiple course migration/update
- Contains a scrolled text box that gives logging feedback of progress for both the migration and update scripts. Logs are saved to a subfolder /logs/
- Migration script:
  1. Copies group sets and groups from the previous course to the new course.
  2. Migrates the previous course (FROM) to the new course (TO) shifting the dates according to the FROM and TO course start dates
  3. Checks the migration progress in Canvas. For multiple courses it loops through the list of courses in the csv file until all of them are done migrating.
- Update script:
  1. Removes extra spaces from module, page, assignment, and quiz titles.
  2. Removes the Spring Break module if present
  3. Changes the module names to contain the week-span for that week if the titles contain a weekspan
  4. Shifts dates depending on wheter Spring Break needs to be added or not. Adds a new Spring Break module if needed
  5. Changes the course id in the link for Library Course Materials in all of the pages in the course.

The scripts uses the following dependancies:
- [CanvasAPI](https://github.com/ucfopen/canvasapi) for the script to work with Canvas LMS
- [TTKbootstrap](https://github.com/israel-dryer/ttkbootstrap) is used for the Tkinter GUI to give it access to easy bootstrap themes
- [Arrow](https://pypi.org/project/arrow/) for handling datetime in the code such as adjustments for timezones and daylight savings
- [Beautiful Soup](https://pypi.org/project/beautifulsoup4/) used for working with HTML in Canvas pages, assignments, discussions. 

CanvasAutomation.py contains the main loop to start the software.
