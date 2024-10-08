# TnC Summarizer

A Python GUI application that summarizes Terms and Conditions (TnC) documents in real-time using AI.

## Features:
- Summarizes TnC from pasted text or URLs
- Built with Cursor IDE
- Utilizes OpenAI's API for summarization
- Provides up-to-date summaries, unlike static TnC summary websites

## Prerequisites:
- Python installed
- Running in a virtual environment (venv)
- Install the following packages:
  ```
  pip install openai
  pip install requests beautifulsoup4
  pip install --upgrade openai
  pip install selenium webdriver_manager
  pip install requests beautifulsoup4 openai
  pip install tkhtmlview markdown
  ```
  Note: Use `pip install --upgrade openai` if you encounter errors when updating the GPT model.

## Usage:
1. Replace the placeholder with your OpenAI API key in the code
2. Run the application
3. Paste TnC text or URL to get an instant summary

## Note:
While similar functionality exists in ChatGPT and Claude, this project serves as a fun use case and learning experience.

## App Preview:
![Main App](summurizer.png)
![Main App](summary_history.png)

