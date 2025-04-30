from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel
import os
from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class Response(BaseModel):
    status: str
    error: str | None

model = OpenAIModel(
            model_name="Qwen/Qwen3-4B",
            provider=OpenAIProvider(
                base_url="http://localhost:8001/v1",
                )
            )

agent = Agent(
            model = model,
            output_ype=str,
            system_prompt="""DO NOT USE INTERNAL REASONING. You are Aybert, an AI Agent developed by Oleg, except you are excelent at coding.
            User name: Oleg""",
            instructions="""speak in Russian or English
            In the beginning of your work scan your working directory, create or enter the 'Workspaces' folder
            chdir in it, look at files present and make sure there's at least one workspace file, there your code output must go whenever user asks to write code
            Make sure a Saves directory exists"""
        )

VOICE = True

@agent.tool_plain
def mkdir(dirname: str) -> Response:
    """Use this function to create a directory on user's computer"""
    result = Response(status="success", error = None)
    try:
        os.mkdir(dirname)
    except Exception as err:
        result.error = str(err)
        result.status = "error"
    
    return result

@agent.tool_plain
def chdir(dirname: str) -> Response:
    """Use this function to change working directory"""
    result = Response(status="success", error=None)
    try:
        os.chdir(dirname)
    except Exception as err:
        result.error = str(err)
        result.status = "error"

    return result

@agent.tool_plain
def create_file(filename: str, content: str, extension: str) -> Response:
    """Use this function to create a .txt file and change it's contents
    filename must have no extension!
    Extension must have no dots!"""
    result = Response(status="success", error=None)

    try:
        with open(filename+f".{extension}", "w") as file:
            file.write(content)
    except Exception as err:
        result.error = str(err)
        result.status = "error"

    return result

@agent.tool_plain
def read_file(filename: str) -> tuple[Response, str]:
    """Use this function to read a file with a provided file name"""
    result = Response(status="success", error=None)
    content = ""

    try:
        with open(filename, "r") as file:
            content = file.read()
    
    except Exception as err:
        result.status = "error"
        result.error = str(err)

    return result, content    

@agent.tool_plain
def see_files() -> [Response, list]:
    """Use this function to see what files are there in your directory"""
    result = Response(status="success", error=None)
    content = []

    try:
        content = os.listdir()
    
    except Exception as err:
        result.status = "error"
        result.error = str(err)

    return result, content

@agent.tool_plain
def search_web(query: str) -> tuple[Response, list]:
    """Use this function to search the web for something"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.get(f'https://duckduckgo.com/?q={query.replace(" ", "+")}')
    time.sleep(10)
    # Extract result links
    res = []
    try:
        links = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="result-title-a"]')[:5]
        for link in links:
            res.append({link.text: link.get_attribute('href')})
            print({link.text: link.get_attribute('href')})
            return Response(status="success", error=None), res
    except Exception as e:
        print('No links found:', e)
        return Response(status="error", error=str(e)), []

@agent.tool_plain
def read_page_contents(url: str) -> tuple[Response, str]:
    """Use this function to open a link in browser and read all the text from the page"""
    # Initialize Chrome options
    print("Reading page:", url)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # Initialize WebDriver
    # service = Service("/usr/bin/google-chrome")
    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to the URL
        driver.get(url)
        time.sleep(5)  # Wait for page to load

        # Wait for the document to be ready
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Extract all text from the page
        all_text = driver.find_element(By.TAG_NAME, "body").text
        return Response(status="success", error=None), all_text[:len(all_text)//2]

    except Exception as err:
        print(f"Error: {err}")
        return Response(status="error", error=str(err)), ""

    finally:
        # Close the browser
        if "driver" in locals():
            driver.quit()

@agent.tool_plain
def create_xlsx_table(execute: str) -> Response:
    """Use this function to create an executable python script that would create an MS excel table
    execute is the script itself"""
    result = Response(status="success", error=None)

    try:
        exec(execute)
        return result
    except Exception as err:
        return Response(status="error", error=str(err))

    return response

@agent.tool_plain
def toggle_speech() -> Response:
    """Use this function if user asks to toggle voice mode (enables or disables basic text to speech)"""
    global VOICE
    try:
        VOICE = not VOICE
        return Response(status="success", error=None)
    except Exception as err:
        return Response(status="error", error=str(err))

output = agent.run_sync('')

while True:    
    try:
        textresponse = output.all_messages()[-1].parts[-1].content
        printable = textresponse[textresponse.find("</think>")+len("</think>"):]
        print(printable)
        print(f"VOICE: {VOICE}")
        if VOICE: os.system(f'espeak -v en+m3 -p 5 "{printable}"')
        print("+||||||||||||||||||||||||||||||||||||+")
        msg_hist = output.new_messages()
        output = agent.run_sync(input(), message_history=msg_hist)
        print("+||||||||||||||||||||||||||||||||||||+")
    except Exception as err:
        print(output.new_messages())
        msg_hist = output.new_messages()[len(msg_hist)//2:]
        raise err