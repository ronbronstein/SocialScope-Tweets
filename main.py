import tkinter as tk
from tkinter import ttk, scrolledtext, font, messagebox
from tkcalendar import DateEntry
import threading
import queue
import os
import json
from datetime import datetime, timedelta
import webbrowser
from typing import Optional
import logging
from pathlib import Path
from scraper import TwitterScraper, ScraperConfig

class MatrixButton(tk.Button):
    """Custom button with Matrix-style effects"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_bg = kwargs.get('bg', '#0C1714')
        self.default_fg = kwargs.get('fg', '#00FF41')
        
        self.configure(
            relief='ridge',
            borderwidth=2,
            padx=10,
            bg=self.default_bg,
            fg=self.default_fg,
            activebackground='#003B00',
            activeforeground='#00FF41'
        )
        
        self.bind('<Enter>', self.on_hover)
        self.bind('<Leave>', self.on_leave)

    def on_hover(self, event):
        if self['state'] != 'disabled':
            self.configure(bg='#003B00')

    def on_leave(self, event):
        self.configure(bg=self.default_bg)

class MatrixGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Matrix Twitter Scraper v1.0")
        self.root.geometry("1000x800")
        self.root.configure(bg='#0C1714')
        self.root.resizable(True, True)
        
        # Variables
        self.log_queue = queue.Queue()
        self.scraping_active = False
        self.scraper_thread: Optional[threading.Thread] = None
        self.last_save_path = None
        
        # Create GUI elements
        self.create_matrix_fonts()
        self.setup_logging()
        self.create_matrix_gui()
        self.load_config()
        
        # Start periodic tasks
        self.check_log_queue()
        self.update_status_blink()
        
        # Add window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)

    def create_matrix_fonts(self):
        """Create Matrix-style fonts"""
        try:
            self.title_font = font.Font(family="Courier New", size=24, weight="bold")
            self.header_font = font.Font(family="Courier New", size=14, weight="bold")
            self.text_font = font.Font(family="Courier New", size=12)
        except:
            # Fallback fonts
            self.title_font = font.Font(family="Courier", size=24, weight="bold")
            self.header_font = font.Font(family="Courier", size=14, weight="bold")
            self.text_font = font.Font(family="Courier", size=12)

    def create_matrix_gui(self):
        """Create Matrix-themed GUI interface"""
        # Main container
        main_container = tk.Frame(self.root, bg='#0C1714')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Title section
        title_frame = tk.Frame(main_container, bg='#0C1714', relief='ridge', bd=2)
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text="eOracle Twitter Scraper",
            font=self.title_font,
            bg='#0C1714',
            fg='#00FF41'
        )
        title_label.pack(pady=10)

        # Settings section
        settings_frame = self.create_labeled_frame(main_container, "SCRAPING CONFIGURATION")

        # Date range inputs
        dates_frame = tk.Frame(settings_frame, bg='#0C1714')
        dates_frame.pack(fill='x', pady=5)
        
        # Start date
        start_date_frame = tk.Frame(dates_frame, bg='#0C1714')
        start_date_frame.pack(side='left', padx=5)
        
        tk.Label(
            start_date_frame,
            text="Start Date (MM/DD/YYYY):",
            font=self.text_font,
            bg='#0C1714',
            fg='#00FF41'
        ).pack(side='left')
        
        self.start_date_var = tk.StringVar()
        start_date_entry = tk.Entry(
            start_date_frame,
            textvariable=self.start_date_var,
            font=self.text_font,
            bg='#000000',
            fg='#00FF41',
            insertbackground='#00FF41',
            width=10
        )
        start_date_entry.pack(side='left', padx=5)

        # End date
        end_date_frame = tk.Frame(dates_frame, bg='#0C1714')
        end_date_frame.pack(side='left', padx=5)
        
        tk.Label(
            end_date_frame,
            text="End Date (MM/DD/YYYY):",
            font=self.text_font,
            bg='#0C1714',
            fg='#00FF41'
        ).pack(side='left')
        
        self.end_date_var = tk.StringVar()
        end_date_entry = tk.Entry(
            end_date_frame,
            textvariable=self.end_date_var,
            font=self.text_font,
            bg='#000000',
            fg='#00FF41',
            insertbackground='#00FF41',
            width=10
        )
        end_date_entry.pack(side='left', padx=5)

        # In your create_matrix_gui method, after creating the date entries:
        today = datetime.now()
        last_month = today - timedelta(days=30)
        self.start_date_var.set(last_month.strftime('%m/%d/%Y'))
        self.end_date_var.set(today.strftime('%m/%d/%Y'))
        
        # Username entry
        username_frame = tk.Frame(settings_frame, bg='#0C1714')
        username_frame.pack(fill='x', pady=5)
        
        tk.Label(
            username_frame,
            text="Target Username:",
            font=self.text_font,
            bg='#0C1714',
            fg='#00FF41'
        ).pack(side='left')
        
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(
            username_frame,
            textvariable=self.username_var,
            font=self.text_font,
            bg='#000000',
            fg='#00FF41',
            insertbackground='#00FF41',
            width=30
        )
        username_entry.pack(side='left', padx=5)

        # Scraping type
        type_frame = tk.Frame(settings_frame, bg='#0C1714')
        type_frame.pack(fill='x', pady=5)
        
        self.scrape_type = tk.StringVar(value="both")
        
        tk.Radiobutton(
            type_frame,
            text="Tweets Only",
            variable=self.scrape_type,
            value="tweets",
            bg='#0C1714',
            fg='#00FF41',
            selectcolor='#003B00',
            activebackground='#0C1714',
            activeforeground='#00FF41'
        ).pack(side='left', padx=5)
        
        tk.Radiobutton(
            type_frame,
            text="Replies Only",
            variable=self.scrape_type,
            value="replies",
            bg='#0C1714',
            fg='#00FF41',
            selectcolor='#003B00',
            activebackground='#0C1714',
            activeforeground='#00FF41'
        ).pack(side='left', padx=5)
        
        tk.Radiobutton(
            type_frame,
            text="Both",
            variable=self.scrape_type,
            value="both",
            bg='#0C1714',
            fg='#00FF41',
            selectcolor='#003B00',
            activebackground='#0C1714',
            activeforeground='#00FF41'
        ).pack(side='left', padx=5)

        # Max tweets
        max_tweets_frame = tk.Frame(settings_frame, bg='#0C1714')
        max_tweets_frame.pack(fill='x', pady=5)
        
        tk.Label(
            max_tweets_frame,
            text="Max Tweets to Scrape:",
            font=self.text_font,
            bg='#0C1714',
            fg='#00FF41'
        ).pack(side='left')
        
        self.max_tweets_var = tk.StringVar(value='1000')
        max_tweets_entry = tk.Entry(
            max_tweets_frame,
            textvariable=self.max_tweets_var,
            font=self.text_font,
            bg='#000000',
            fg='#00FF41',
            insertbackground='#00FF41',
            width=10
        )
        max_tweets_entry.pack(side='left', padx=5)

        # Controls section
        controls_frame = tk.Frame(main_container, bg='#0C1714')
        controls_frame.pack(fill='x', pady=10)
        
        self.start_button = MatrixButton(
            controls_frame,
            text="▶ START SCRAPING",
            font=self.header_font,
            command=self.start_scraping
        )
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = MatrixButton(
            controls_frame,
            text="⬛ STOP",
            font=self.header_font,
            command=self.stop_scraping,
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=5)

        # Add "Open Last File" button to controls section
        self.open_file_button = MatrixButton(
            controls_frame,
            text="📂 OPEN FILE",
            font=self.header_font,
            command=self.open_last_file,
            state='disabled'
        )
        self.open_file_button.pack(side='right', padx=5)
        
        # Status section
        status_frame = self.create_labeled_frame(main_container, "STATUS")
        
        self.status_var = tk.StringVar(value="System Ready...")
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=self.text_font,
            bg='#0C1714',
            fg='#00FF41'
        )
        status_label.pack(fill='x', pady=5)
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Matrix.Horizontal.TProgressbar",
            troughcolor='#0C1714',
            background='#00FF41',
            darkcolor='#003B00',
            lightcolor='#00FF41'
        )
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            style="Matrix.Horizontal.TProgressbar",
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill='x', pady=5)

        # Log section
        log_frame = self.create_labeled_frame(main_container, "OPERATION LOG")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=self.text_font,
            bg='#000000',
            fg='#00FF41',
            insertbackground='#00FF41'
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Create right-click menu for log
        self.create_log_menu()
        
    def validate_date(self, date_str: str) -> Optional[datetime]:
        """Validate date string format MM/DD/YYYY"""
        if not date_str:  # Handle empty string
            return None
        try:
            # First try to parse with exact format
            parsed_date = datetime.strptime(date_str.strip(), '%m/%d/%Y')
            # Validate year is reasonable
            if parsed_date.year < 2006:  # Twitter launched in 2006
                return None
            return parsed_date
        except ValueError:
            try:
                # Try alternative format in case user adds spaces
                parsed_date = datetime.strptime(date_str.strip(), '%m/%d/%Y')
                if parsed_date.year < 2006:
                    return None
                return parsed_date
            except ValueError:
                return None

    def start_scraping(self):
        """Start the scraping process with date validation"""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter a username!")
            return

        try:
            max_tweets = int(self.max_tweets_var.get())
            if max_tweets <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid number of tweets!")
            return

        # Validate dates
        start_date = self.validate_date(self.start_date_var.get())
        end_date = self.validate_date(self.end_date_var.get())

        if not start_date or not end_date:
            messagebox.showerror("Error", 
                "Invalid date format! Please use MM/DD/YYYY format (e.g., 11/27/2024)")
            return

        if start_date > end_date:
            messagebox.showerror("Error", "Start date must be before end date!")
            return

        if end_date > datetime.now():
            messagebox.showerror("Error", "End date cannot be in the future!")
            return

        # Create scraper config
        config = ScraperConfig(
            username=username,
            max_tweets=max_tweets,
            scrape_type=self.scrape_type.get(),
            save_dir='output',
            start_date=start_date,
            end_date=end_date
        )

        self.prepare_scraping_session(config)

    def open_last_file(self):
        """Open the last saved CSV file"""
        if not self.last_save_path or not os.path.exists(self.last_save_path):
            messagebox.showerror("Error", "No file available to open!")
            return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.last_save_path)
            elif os.name == 'posix':  # macOS and Linux
                if os.path.exists('/usr/bin/open'):  # macOS
                    os.system(f'open "{self.last_save_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{self.last_save_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def run_scraper(self, scraper: TwitterScraper):
        """Run the scraper in a separate thread with improved progress handling"""
        try:
            def progress_callback(progress: float, status: str, is_complete: bool = False):
                if not self.scraping_active:
                    raise Exception("Scraping stopped by user")
                if is_complete:
                    progress = 100.0
                self.root.after(0, self.update_progress, progress, status)
            
            tweets = scraper.fetch_tweets(progress_callback=progress_callback)
            
            if tweets:
                filename = scraper.save_tweets(tweets)
                if filename:
                    self.last_save_path = filename
                    self.save_config()
                    final_message = f"Successfully saved {len(tweets)} tweets to {filename}"
                    self.root.after(0, self.log_text.insert, tk.END, f"{final_message}\n")
                    self.root.after(0, self.status_var.set, final_message)
                    self.root.after(0, self.open_file_button.config, {'state': 'normal'})
                    self.root.after(0, messagebox.showinfo, "Success", final_message)
                else:
                    self.handle_scraping_error("Error saving tweets!")
            else:
                self.handle_scraping_error("No tweets collected!")
                
        except Exception as e:
            self.handle_scraping_error(str(e))
        finally:
            self.cleanup_scraping_session()

    def create_labeled_frame(self, parent, title):
        """Create Matrix-styled labeled frame"""
        frame = tk.LabelFrame(
            parent,
            text=title,
            font=self.header_font,
            bg='#0C1714',
            fg='#00FF41',
            relief='ridge'
        )
        frame.pack(fill='x', padx=5, pady=5)
        return frame
    def setup_logging(self):
        """Configure logging with enhanced formatting"""
        class QueueHandler(logging.Handler):
            def __init__(self, queue):
                super().__init__()
                self.queue = queue

            def emit(self, record):
                self.queue.put(record)

        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers = []
        
        # File handler with timestamp in filename
        log_file = Path('logs') / f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        
        # Queue handler for GUI
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        logger.addHandler(queue_handler)

    def check_log_queue(self):
        """Process log queue entries"""
        try:
            while True:
                record = self.log_queue.get_nowait()
                msg = f"{record.getMessage()}\n"
                
                # Color coding based on log level
                if record.levelno >= logging.ERROR:
                    self.log_text.tag_config('error', foreground='#FF0000')
                    self.log_text.insert(tk.END, msg, 'error')
                elif record.levelno >= logging.WARNING:
                    self.log_text.tag_config('warning', foreground='#FFFF00')
                    self.log_text.insert(tk.END, msg, 'warning')
                else:
                    self.log_text.insert(tk.END, msg)
                
                self.log_text.see(tk.END)
                self.log_queue.task_done()
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_log_queue)

    def create_log_menu(self):
        """Create right-click menu for log"""
        self.log_menu = tk.Menu(self.root, tearoff=0, bg='#0C1714', fg='#00FF41')
        self.log_menu.add_command(label="Copy", command=self.copy_log_selection)
        self.log_menu.add_command(label="Select All", command=self.select_all_log)
        self.log_menu.add_separator()
        self.log_menu.add_command(label="Clear Log", command=self.clear_log)
        self.log_menu.add_command(label="Save Log", command=self.save_log)
        
        self.log_text.bind('<Button-3>', self.show_log_menu)

    def show_log_menu(self, event):
        """Show context menu"""
        self.log_menu.tk_popup(event.x_root, event.y_root)

    def copy_log_selection(self):
        """Copy selected text to clipboard"""
        try:
            selected_text = self.log_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass

    def select_all_log(self):
        """Select all text in log"""
        self.log_text.tag_add(tk.SEL, "1.0", tk.END)
        self.log_text.mark_set(tk.INSERT, "1.0")
        self.log_text.see(tk.INSERT)

    def clear_log(self):
        """Clear log content"""
        if messagebox.askyesno("Clear Log", "Clear log content?"):
            self.log_text.delete(1.0, tk.END)
            logging.info("Log cleared by user")

    def save_log(self):
        """Save log content to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/manual_save_{timestamp}.log"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Log saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")

    def prepare_scraping_session(self, config: ScraperConfig):
        """Prepare and start scraping session"""
        try:
            # Initialize scraper
            scraper = TwitterScraper(config)
            
            # Verify account
            logging.info(f"Verifying account: @{config.username}")
            account_info = scraper.verify_account()
            
            if not account_info['success']:
                messagebox.showerror("Error", f"Could not verify account: {account_info.get('error')}")
                return
            
            # Log account information
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "=== Account Information ===\n")
            self.log_text.insert(tk.END, f"Username: @{config.username}\n")
            self.log_text.insert(tk.END, f"User ID: {account_info['user_id']}\n")
            self.log_text.insert(tk.END, f"Name: {account_info['name']}\n")
            self.log_text.insert(tk.END, f"Total Tweets: {account_info['total_tweets']:,}\n")
            self.log_text.insert(tk.END, f"Followers: {account_info['followers']:,}\n")
            self.log_text.insert(tk.END, f"Account Created: {account_info['created_at']}\n")
            self.log_text.insert(tk.END, "========================\n\n")
            
            if account_info['protected']:
                messagebox.showerror("Error", "This account is protected. Cannot fetch tweets.")
                return
            
            self.start_scraping_session(scraper)
            
        except Exception as e:
            messagebox.showerror("Error", f"Setup error: {str(e)}")
            logging.error(f"Setup error: {str(e)}", exc_info=True)
            return

    def start_scraping_session(self, scraper: TwitterScraper):
        """Start the actual scraping session"""
        self.scraping_active = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_var.set("Starting scrape...")
        self.progress_var.set(0)
        
        self.scraper_thread = threading.Thread(
            target=self.run_scraper,
            args=(scraper,),
            daemon=True
        )
        self.scraper_thread.start()

    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraping_active:
            self.scraping_active = False
            self.status_var.set("Stopping scraper... Please wait...")
            logging.info("User requested stop. Finishing current batch...")
            self.stop_button.config(state='disabled')

    def update_progress(self, progress: float, status: str):
        """Update progress bar and status text"""
        self.progress_var.set(progress)
        self.status_var.set(status)

    def handle_scraping_error(self, error_msg: str):
        """Handle scraping errors"""
        self.root.after(0, self.status_var.set, error_msg)
        self.root.after(0, self.log_text.insert, tk.END, f"Error: {error_msg}\n")
        if error_msg != "Scraping stopped by user":
            self.root.after(0, messagebox.showerror, "Error", error_msg)

    def cleanup_scraping_session(self):
        """Clean up after scraping session"""
        self.scraping_active = False
        self.root.after(0, self.start_button.config, {'state': 'normal'})
        self.root.after(0, self.stop_button.config, {'state': 'disabled'})
        self.root.after(0, self.log_text.see, tk.END)

    def update_status_blink(self):
        """Update status LED animation"""
        if self.scraping_active:
            current_color = '#FF0000' if self.status_var.get().startswith("●") else '#00FF41'
            status_text = self.status_var.get().lstrip("●").strip()
            self.status_var.set(f"● {status_text}")
            blink_speed = 500
        else:
            blink_speed = 1000
        
        self.root.after(blink_speed, self.update_status_blink)

    def save_config(self):
        """Save current configuration"""
        config = {
            'username': self.username_var.get(),
            'max_tweets': self.max_tweets_var.get(),
            'scrape_type': self.scrape_type.get(),
            'last_save_path': self.last_save_path
        }
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f)
        except Exception as e:
            logging.warning(f"Failed to save config: {e}")

    def load_config(self):
        """Load saved configuration"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    self.username_var.set(config.get('username', ''))
                    self.max_tweets_var.set(config.get('max_tweets', '1000'))
                    self.scrape_type.set(config.get('scrape_type', 'both'))
                    self.last_save_path = config.get('last_save_path')
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")

    def quit_application(self):
        """Quit application with cleanup"""
        if self.scraping_active:
            if not messagebox.askyesno("Quit", "Scraping is still running. Stop and quit?"):
                return
            self.stop_scraping()
        
        self.save_config()
        
        # Clean up logging handlers
        logging.getLogger().handlers = []
        
        self.root.quit()

def main():
    """Main entry point"""
    try:
        root = tk.Tk()
        app = MatrixGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Critical Error", f"Application error: {e}")
        logging.critical(f"Application crashed: {e}", exc_info=True)

if __name__ == "__main__":
    main()