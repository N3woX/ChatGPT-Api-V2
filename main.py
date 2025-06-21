import undetected_chromedriver as uc
import time
import logging
import os
from flask import Flask, request, jsonify
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
import requests
import zipfile
import io
import shutil
import threading

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)

driver = None
prompt_box = None
message_count = 0
CONTEXT = (
    "RESET: Disregard all previous messages and context. "
    "Forget everything that has been said before; you are now in a brand new conversation with no prior history. "
    "Do not produce any greetings, acknowledgments, or introductory phrases. "
    "Simply await the next user input and respond directly."
)

render_external_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_external_hostname:
    PLACEHOLDER_URL = f"https://{render_external_hostname}"
else:
    PLACEHOLDER_URL = "http://example.com"

def keep_alive():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    while True:
        try:
            logging.info(f"Sending keep-alive request to {PLACEHOLDER_URL}")
            response = requests.get(PLACEHOLDER_URL, headers=headers, timeout=10)
            logging.info(f"Keep-alive request status: {response.status_code}")
            response.close()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending keep-alive request to {PLACEHOLDER_URL}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred in keep-alive thread: {e}")

        time.sleep(60)

def download_and_extract_zip(url, extract_to_dir, subfolder_name, exe_name):
    logging.info(f"Downloading {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        if os.path.exists(extract_to_dir):
            shutil.rmtree(extract_to_dir)
        os.makedirs(extract_to_dir)

        logging.info(f"Extracting zip to {extract_to_dir}...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            zf.extractall(extract_to_dir)
        logging.info("Extraction complete.")

        exe_path = os.path.join(extract_to_dir, subfolder_name, exe_name)

        if not os.path.exists(exe_path):
            logging.critical(f"Executable not found at expected path after extraction: {exe_path}")
            logging.debug(f"Contents of {extract_to_dir}: {os.listdir(extract_to_dir)}")
            if os.path.exists(os.path.join(extract_to_dir, subfolder_name)):
                logging.debug(f"Contents of {os.path.join(extract_to_dir, subfolder_name)}: {os.listdir(os.path.join(extract_to_dir, subfolder_name))}")

            raise FileNotFoundError(f"Executable not found at {exe_path}")

        logging.info(f"Executable found at {exe_path}")
        return exe_path

    except requests.exceptions.RequestException as e:
        logging.critical(f"Error downloading {url}: {e}")
        raise
    except zipfile.BadZipFile:
        logging.critical(f"Error: Downloaded file from {url} is not a valid zip file.")
        raise
    except Exception as e:
        logging.critical(f"An unexpected error occurred during download/extraction: {e}")
        raise

def setup_driver():
    global driver, prompt_box, message_count

    chrome_url = "https://storage.googleapis.com/chrome-for-testing-public/137.0.7151.6/win64/chrome-win64.zip"

    chrome_url = chrome_url.replace("win64", "linux64")

    chrome_extract_dir = "./chrome_bin"
    chrome_subfolder = "chrome-linux64"
    chrome_exe_name = "chrome"

    chrome_binary_path = download_and_extract_zip(chrome_url, chrome_extract_dir, chrome_subfolder, chrome_exe_name)

    os.chmod(chrome_binary_path, 0o755)
    logging.info(f"Set executable permissions for {chrome_binary_path}")

    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.binary_location = chrome_binary_path

    driver = uc.Chrome(options=options)

    logging.info(f"Chrome binary path set to: {chrome_binary_path}")

    driver.get("https://chatgpt.com/")

    time.sleep(5)

    try:
        prompt_box = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "prompt-textarea"))
        )
        logging.info("Prompt box found.")
    except Exception as e:
        logging.error(f"Failed to find prompt box: {e}")
        driver.quit()
        raise

    message_count = 0

def wait_for_stable_response(initial_count, timeout=30, poll_interval=0.3, stability_cycles=2):
    stable_count = 0
    last_text = ""
    start_time = time.time()
    logging.debug(f"Waiting for stable response. Initial paragraphs: {initial_count}")
    while True:
        try:
            paragraphs = driver.find_elements(By.CSS_SELECTOR, "p[data-start]")
            new_paragraphs = paragraphs[initial_count:] if len(paragraphs) > initial_count else []
            texts = []
            for p in new_paragraphs:
                if p.is_displayed():
                    try:
                        texts.append(p.text)
                    except StaleElementReferenceException:
                        logging.debug("Caught StaleElementReferenceException while getting text. Retrying...")
                        paragraphs = driver.find_elements(By.CSS_SELECTOR, "p[data-start]")
                        new_paragraphs = paragraphs[initial_count:] if len(paragraphs) > initial_count else []
                        texts = [p.text for p in new_paragraphs if p.is_displayed()]
                        break

            current_text = "\n".join(texts)

            logging.debug(f"Current text: {current_text[:100]}...")
            logging.debug(f"Last text:    {last_text[:100]}...")
            logging.debug(f"Stable count: {stable_count}")

            if current_text and current_text == last_text:
                stable_count += 1
                logging.debug(f"Text is stable. stable_count: {stable_count}")
            else:
                stable_count = 0
                logging.debug("Text changed or is empty. stable_count reset.")

            if current_text and len(current_text) < 50 and stable_count >= 1:
                logging.debug(f"Short stable response detected. Returning: {current_text}")
                return current_text
            if stable_count >= stability_cycles and current_text:
                logging.debug(f"Response stable for {stability_cycles} cycles. Returning: {current_text}")
                return current_text

            if time.time() - start_time > timeout:
                logging.warning(f"Timeout reached ({timeout}s). Returning current text: {current_text}")
                return current_text

            last_text = current_text
            time.sleep(poll_interval)

        except Exception as e:
            logging.error(f"Error in wait_for_stable_response loop: {e}")
            return current_text

def process_message(message):
    global prompt_box, driver

    logging.info(f"Processing message: {message[:50]}...")

    dismiss_button_xpath = "//button[normalize-space(text())='Rester déconnecté' or normalize-space(text())='Stay disconnected' or normalize-space(.)='Stay disconnected' or normalize-space(.)='Rester déconnecté']"
    dismiss_check_timeout = 10

    try:
        logging.debug(f"Checking for dismiss button with timeout {dismiss_check_timeout}s...")
        dismiss_button = WebDriverWait(driver, dismiss_check_timeout).until(
            EC.element_to_be_clickable((By.XPATH, dismiss_button_xpath))
        )
        logging.info("Dismiss button found and is clickable. Clicking it.")
        dismiss_button.click()
        time.sleep(1)
        logging.info("Dismiss button clicked.")
    except (TimeoutException, NoSuchElementException):
        logging.debug("Dismiss button not found or not clickable within timeout (expected behavior if prompt is not shown).")
        pass
    except Exception as e:
        logging.error(f"An unexpected error occurred while checking for dismiss button: {e}")

    try:
        prompt_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "prompt-textarea"))
        )
        logging.debug("Prompt box is clickable.")
    except Exception as e:
        logging.error(f"Prompt box not clickable or found before sending message: {e}")
        try:
            prompt_box = driver.find_element(By.ID, "prompt-textarea")
            if prompt_box.is_displayed() and prompt_box.is_enabled():
                logging.debug("Re-found prompt box element and it is interactive.")
            else:
                logging.critical("Re-found prompt box but it is not interactive.")
                raise Exception("Prompt box not interactive after re-finding")
        except Exception as ef:
            logging.critical(f"Failed to re-find prompt box: {ef}")
            raise

    initial_paragraphs = driver.find_elements(By.CSS_SELECTOR, "p[data-start]")
    initial_count = len(initial_paragraphs)
    logging.debug(f"Initial paragraph count before sending: {initial_count}")

    prompt_box.clear()
    logging.debug("Prompt box cleared.")

    context_clean = CONTEXT.strip()
    prompt_box.send_keys(context_clean)
    logging.debug("Context sent to prompt box.")
    prompt_box.send_keys(Keys.SHIFT, Keys.ENTER)
    logging.debug("SHIFT+ENTER sent.")
    prompt_box.send_keys(message)
    logging.debug("User message sent to prompt box.")
    prompt_box.send_keys(Keys.RETURN)
    logging.debug("RETURN sent to submit message.")

    response_text = wait_for_stable_response(initial_count)

    logging.info("Response received.")
    return response_text

@app.route('/ask', methods=['POST'])
def ask():
    global message_count, driver

    logging.info("Received POST request to /ask")
    data = request.get_json()

    if not data or "message" not in data:
        logging.warning("Bad request: No message provided.")
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"]
    logging.info(f"User message: {user_message[:50]}...")

    message_count += 1
    logging.info(f"Message count incremented to: {message_count}")

    try:
        response_text = process_message(user_message)
    except Exception as e:
        logging.error(f"Error during message processing: {e}")
        return jsonify({"error": f"Failed to process message: {e}"}), 500

    logging.info("Returning response.")
    return jsonify({"response": response_text})

logging.info("Starting script (Gunicorn import mode).")
try:
    setup_driver()
    logging.info("Driver setup complete.")
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    logging.info("Keep-alive thread started.")
except Exception as e:
    logging.critical(f"Initial setup (driver or keep-alive) failed during Gunicorn import: {e}")

if __name__ == "__main__":
    logging.info("Starting script in local development mode (if this log appears, you're running directly).")
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting Flask app on port {port}.")
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
