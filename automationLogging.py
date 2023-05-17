import logging
import queue

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import ScrolledText, Frame

# Creates logger for the instance.
logger = logging.getLogger(__name__)

# Updates the log
def update_log(msg: str):
        lvl = getattr(logging, "INFO")
        logger.log(lvl, msg) 

# Class to send logging records to a queue. It can be used from different threads. The ConsoleUi class polls this queue to display records in a ScrolledText widget
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

# Class to poll messages from a logging queue and display them in a scrolled text widget
class ConsoleUi:
    def __init__(self, frame):
        self.frame = frame
        
        # Create a ScrolledText wdiget
        textbox_row = Frame(frame)
        textbox_row.pack(fill=X, expand=YES, pady=(15, 0))

        self.scrolled_text = ScrolledText(textbox_row, state='disabled', height=12)
        self.scrolled_text.pack(side=TOP,fill=BOTH)
        
        # Logging Default Color Coding
        self.scrolled_text.tag_config('INFO', foreground='white')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        
        # Custom Logging Color Coding
        self.scrolled_text.tag_config('DONE', foreground='green')

        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)
        
        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    # Function displays text in scrolled_text by enabling it, inserting text, disabling it and then scrolling to the bottom
    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(ttk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(ttk.END)

    # Function that is so important, it is beyond my comprehension. Leave this be unless you know more than me.
    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)
    
    # Function returns all text from scrolledtext
    def get_all_text(self):
        return self.scrolled_text.get('1.0', ttk.END)
    
    def is_empty(self):
        if self.scrolled_text.compare("end-1c", "==", "1.0"):
            return True
        else:
            return False