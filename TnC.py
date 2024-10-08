import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from tkhtmlview import HTMLLabel
import markdown
import json
from datetime import datetime
import itertools
import time

class TnCSummarizerApp:
    def __init__(self, master):
        self.master = master
        master.title("Terms and Conditions Summarizer")
        
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.main_frame = ttk.Frame(self.notebook)
        self.history_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_frame, text="Summarizer")
        self.notebook.add(self.history_frame, text="History")
        
        self.setup_main_frame()
        self.setup_history_frame()
        
        self.history = self.load_history()

        self.setup_text_tags(self.summary_output)
        self.setup_text_tags(self.history_summary)

    def setup_main_frame(self):
        self.label = tk.Label(self.main_frame, text="Enter Terms and Conditions or URL:")
        self.label.pack()
        
        self.text_input = scrolledtext.ScrolledText(self.main_frame, width=60, height=10)
        self.text_input.pack()
        
        self.summarize_button = tk.Button(self.main_frame, text="Summarize", command=self.summarize)
        self.summarize_button.pack()
        
        self.summary_label = tk.Label(self.main_frame, text="Summary:")
        self.summary_label.pack()
        
        self.summary_output = tk.Text(self.main_frame, wrap=tk.WORD, width=60, height=20)
        self.summary_output.pack(fill="both", expand=True)
        self.summary_output.config(state=tk.DISABLED)  # Make it read-only initially
        
        self.copy_button = tk.Button(self.main_frame, text="Copy Summary", command=self.copy_summary)
        self.copy_button.pack()

    def setup_history_frame(self):
        self.history_frame_left = ttk.Frame(self.history_frame)
        self.history_frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.history_frame_right = ttk.Frame(self.history_frame)
        self.history_frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.history_listbox = tk.Listbox(self.history_frame_left, width=30)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(self.history_frame_left)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.history_listbox.yview)
        
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)

        self.history_summary = tk.Text(self.history_frame_right, wrap=tk.WORD, width=50, height=20)
        self.history_summary.pack(fill=tk.BOTH, expand=True)
        self.history_summary.config(state=tk.DISABLED)

    def setup_text_tags(self, text_widget):
        text_widget.tag_configure('heading1', font=('Arial', 14, 'bold'))
        text_widget.tag_configure('heading2', font=('Arial', 12, 'bold'))
        text_widget.tag_configure('bullet', lmargin1=20, lmargin2=20)

    def summarize(self):
        input_text = self.text_input.get("1.0", tk.END).strip()
        
        try:
            if input_text.startswith('http://') or input_text.startswith('https://'):
                try:
                    tnc_text = self.get_text_from_url(input_text)
                    print(f"Fetched text (first 500 characters): {tnc_text[:500]}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to fetch content from URL: {str(e)}")
                    return
            else:
                tnc_text = input_text
            
            if not tnc_text.strip():
                messagebox.showerror("Error", "No text to summarize.")
                return
            
            summary = self.get_summary_from_chatgpt(tnc_text)
            self.apply_summary_formatting(self.summary_output, summary)
            
            self.add_to_history(input_text, summary)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def get_text_from_url(self, url):
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        try:
            driver.set_page_load_timeout(30)  # Set a 30-second timeout
            driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Scroll to load all content
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Get the page source after JavaScript execution
            page_source = driver.page_source
            
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Try different selectors to find the main content
            main_content = soup.find('div', {'role': 'main'}) or \
                           soup.find('div', {'class': 'content'}) or \
                           soup.find('main') or \
                           soup.find('body')
            
            if main_content:
                for element in main_content(['style', 'script', 'noscript', 'iframe', 'header', 'footer', 'nav']):
                    element.decompose()
                
                text = main_content.get_text(separator='\n', strip=True)
                lines = (line.strip() for line in text.splitlines())
                text = '\n'.join(line for line in lines if line)
                
                return text
            else:
                raise Exception("Could not find main content on the page.")
        except Exception as e:
            print(f"Error fetching URL: {str(e)}")
            raise
        finally:
            driver.quit()

    def get_summary_from_chatgpt(self, text):
        try:
            client = OpenAI(api_key='your_actual_api_key')  # Replace with your actual API key
            
            print(f"Sending request to OpenAI (first 500 characters): {text[:500]}")
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in summarizing Terms and Conditions and Privacy Policies. Your task is to provide clear, concise summaries focusing on key points that users should be aware of. Use relevant emojis at the start of each point."},
                    {"role": "user", "content": f"""Please summarize the following Terms and Conditions or Privacy Policy. Focus on these key aspects:

1. What personal data is collected
2. How the data is used
3. Data sharing practices
4. User rights and controls
5. Important policy changes or unique clauses

Present the summary as a bulleted list with clear, concise points. Use Markdown formatting for better readability. Start each point with a relevant emoji. For example:
- 📧 for email-related information
- 📍 for location data
- 🖼️ for photos or images
- 👤 for personal profile information
- 🔒 for security-related points
- 🤝 for data sharing practices
- ⚖️ for legal or policy changes

Here's the text to summarize:

{text[:4000]}"""}  # Limit text to 4000 characters
                ]
            )
            
            summary = response.choices[0].message.content
            print(f"Received summary (first 500 characters): {summary[:500]}")
            return summary
        except Exception as e:
            print(f"Error in getting summary from ChatGPT: {str(e)}")
            raise Exception(f"Error in getting summary from ChatGPT: {str(e)}")

    def copy_summary(self):
        summary = self.summary_output.get("1.0", tk.END).strip()
        self.master.clipboard_clear()
        self.master.clipboard_append(summary)
        messagebox.showinfo("Copied", "Summary copied to clipboard!")

    def add_to_history(self, input_text, summary):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append({"timestamp": timestamp, "input": input_text, "summary": summary})
        self.save_history()
        self.update_history_listbox()

    def load_history(self):
        try:
            with open("summary_history.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_history(self):
        with open("summary_history.json", "w") as f:
            json.dump(self.history, f)

    def update_history_listbox(self):
        self.history_listbox.delete(0, tk.END)
        for item in self.history:
            self.history_listbox.insert(tk.END, f"{item['timestamp']} - {item['input'][:50]}...")

    def on_history_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            data = self.history[index]
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert(tk.END, data["input"])
            
            self.apply_summary_formatting(self.history_summary, data["summary"])

    def apply_summary_formatting(self, text_widget, summary):
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        
        for line in summary.split('\n'):
            if line.startswith('# '):
                text_widget.insert(tk.END, line[2:] + '\n', 'heading1')
            elif line.startswith('## '):
                text_widget.insert(tk.END, line[3:] + '\n', 'heading2')
            elif line.startswith('- '):
                text_widget.insert(tk.END, '  • ' + line[2:] + '\n', 'bullet')
            else:
                text_widget.insert(tk.END, line + '\n')
        
        text_widget.config(state=tk.DISABLED)

root = tk.Tk()
app = TnCSummarizerApp(root)
root.mainloop()
