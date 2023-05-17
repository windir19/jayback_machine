from datetime import datetime
# Canvas API Variables
API_URL = "https://canvas.umn.edu"

# GUI Window Variables
APP_TITLE = "The Jayback Machine: Canvas Migration and Update Automation Script"
APP_TTK_THEME = "darkly"
APP_HEIGHT = 1000
APP_WIDTH = 900
APP_TTK_WINDOW_SIZE = (APP_HEIGHT,APP_WIDTH)

# Regex Varibles
WEEK_SPAN_REGEX = '[A-Za-z]* (\d\d|\d)[ ]{0,}(-|–)[ ]{0,}[A-Za-z]* (\d\d|\d)'
LIBRARY_EXT_REGEX = '(?<=courses\/)\d{6,}(?=\/external_tools\/12142)'

# GUI DateEntry 
FROM_DATEENTRY_START_DATE = datetime.today()
TO_DATEENTRY_START_DATE = datetime.today()

# Test Variables
IS_TESTING = False
FROM_CRS = 399648
TO_CRS = 399912