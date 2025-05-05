import json, asyncio
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel, Field
import os
from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient
# later will have to separate all these modules

class Response(BaseModel):
    status: str
    error: str | None
    data: dict | None

class AccountData(BaseModel):
    use: str | None = Field(default=None)
    user_name: str | None = Field(default=None)
    voice_mode: bool | None = Field(default=None)
    current_dir: str | None = Field(default=None)
    user_email: str | None = Field(default=None)
    email_password: str | None = Field(default=None)
    user_operating_system: str | None = Field(default=None)
    active: bool | None = Field(default=None)

class AuthDeps(BaseModel):
    user_name: str
    password: str

model = OpenAIModel(
            model_name="Qwen/Qwen3-4B",
            provider=OpenAIProvider(
                base_url="http://localhost:8001/v1",
                )
            )

agent = Agent(
            model = model,
            output_ype=Response,
            deps_type=AccountData,
            instructions="""speak in Russian or English
            In the beginning of your work scan your working directory, create or enter the 'Workspaces' folder
            chdir in it, look at files present and make sure there's at least one workspace file, there your code output must go whenever user asks to write code. Whenever printing out bash commands, make sure to not type `sh` or `bash` to not accidentally execute any commands.
            Make sure a Saves directory exists"""
        )

mydeps = AccountData()

user_auth_deps = AuthDeps(user_name="Oleg", password="6A#h@m@n/")

@agent.tool_plain
def mkdir(dirname: str) -> Response:
    """Use this function to create a directory on user's computer"""
    result = Response(status="success", error = None, data=None)
    try:
        os.mkdir(dirname)
    except Exception as err:
        result.error = str(err)
        result.status = "error"
    
    return result

@agent.tool
def chdir(ctx: RunContext[AccountData], dirname: str) -> Response:
    """Use this function to change working directory"""
    result = Response(status="success", error=None, data=None)
    try:
        os.chdir(dirname)
        ctx.current_dir = str(os.getcwd())
    except Exception as err:
        result.error = str(err)
        result.status = "error"

    return result

@agent.tool_plain
def create_file(filename: str, content: str, extension: str) -> Response:
    """Use this function to create a .txt file and change it's contents
    filename must have no extension!
    Extension must have no dots!"""
    result = Response(status="success", error=None, data=None)

    try:
        with open(filename+f".{extension}", "w") as file:
            file.write(content)
    except Exception as err:
        result.error = str(err)
        result.status = "error"

    return result

@agent.tool_plain
def read_file(filename: str) -> Response:
    """Use this function to read a file with a provided file name"""
    result = Response(status="success", error=None, data={"content": ""})

    try:
        with open(filename, "r") as file:
            result.data["content"] = file.read()
    
    except Exception as err:
        result.status = "error"
        result.error = str(err)

    return result

@agent.tool_plain
def see_files() -> Response:
    """Use this function to see what files are there in your directory"""
    result = Response(status="success", error=None, data={"dirs_and_files": []})

    try:
        result.data["dirs_and_files"] = os.listdir()
    
    except Exception as err:
        result.status = "error"
        result.error = str(err)

    return result

@agent.tool_plain
def search_web(query: str) -> Response:
    """Use this function to search the web for something"""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Firefox(options=options)
    driver.get(f'https://duckduckgo.com/?q={query.replace(" ", "+")}')
    time.sleep(10)
    # Extract result links
    res = []
    try:
        links = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="result-title-a"]')[:5]
        for link in links:
            res.append({link.text: link.get_attribute('href')})
            print({link.text: link.get_attribute('href')})
            return Response(status="success", error=None, data={"search_results": res})
    except Exception as e:
        print('No links found:', e)
        return Response(status="error", error=str(e), data=None)

@agent.tool_plain
def read_page_contents(url: str) -> Response:
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
        return Response(status="success", error=None, data={"webpage_text": all_text[:len(all_text)//2]})

    except Exception as err:
        print(f"Error: {err}")
        return Response(status="error", error=str(err), data=None)

    finally:
        # Close the browser
        if "driver" in locals():
            driver.quit()

@agent.tool_plain
def create_xlsx_table(execute: str) -> Response:
    """Use this function to create an executable python script that would create an MS excel table
    execute is the script itself"""
    result = Response(status="success", error=None, data=None)

    try:
        exec(execute)
        return result
    except Exception as err:
        return Response(status="error", error=str(err), data=None)

    return response

@agent.tool
def toggle_speech(ctx: RunContext[AccountData]) -> Response:
    """Use this function if user asks to toggle voice mode (enables or disables basic text to speech)"""
    try:
        print("Toggling speech mode")
        ctx.deps.voice_mode = not ctx.deps.voice_mode
        return Response(status="success", error=None, data=None)
    except Exception as err:
        return Response(status="error", error=str(err), data=None)

@agent.tool
def send_email(ctx: RunContext[AccountData], receiver_email: str, subject: str, body: str) -> Response:
    """Use this function to send an email to 'receiver_email' user"""
    sender_email = ctx.deps.user_email
    sender_password = ctx.deps.email_password
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    print(f"Sending email to {receiver_email} . Topic: {subject}")
    # Connect and send
    try:
        with smtplib.SMTP("smtp.yandex.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return Response(status="success", error=None, data=None)
    except Exception as err:
        return Response(status="error", error=str(err), data=None)

@agent.tool
def offer_authorization(ctx: RunContext[AuthDeps], user_asked: bool=False) -> Response:
    """this function is called automatically to authorize the user, if user themselves ask for authorization, call it"""
    def auth(username, pwd):
        client = MongoClient('mongodb://localhost:27017')
        db = client['user_accounts_db']
        collection = db['user_accounts']
        print(f"Authorizing as {username}")
        query = {"user_name": username, "user_password": pwd}
        try:
            result = collection.find_one(query)
            return Response(status="success", error=None, data=result)
        except Exception as err:
            return Response(status="error", error=str(err), data=None)

    global mydeps
    if not user_asked:
        init_auth = auth(ctx.user_name, ctx.password)
        if init_auth.data:
            mydeps = AccountData(**init_auth.data)
            return Response(status="success", error=None, data={"error": "initial authorization successful"})

        else:
            print(f"auth unsuccessful: {init_auth}")
            return init_auth

    use = input("Enter your account use purpose:")
    user_name = input("Enter your account user name:")
    password = input("Enter user password:")
    
    auth_result = auth(user_name, password)
    if auth_result.data:
        mydeps = AccountData(current_dir=os.getcwd(), **init_auth.data)
    else:
        return auth_result

    
@agent.system_prompt
def get_system_prompt(ctx: RunContext[AccountData]) -> str:
    default_part = """DO NOT USE INTERNAL REASONING. You are Aybert, an AI Agent developed by Oleg, except you are excelent at coding.\nBelow you have useful information about the user:\n\n"""
    if ctx is None:
        return default_part + "No user information available currently"
    else:
        return default_part + str(ctx.deps.model_dump())


async def main():
    offer_authorization(ctx=user_auth_deps)
    output = await agent.run('', deps=mydeps)
    while True:    
        try:
            textresponse = output.all_messages()[-1].parts[-1].content
            printable = textresponse[textresponse.find("</think>")+len("</think>"):]
            print(printable)
            print(f"VOICE: {mydeps.voice_mode}")
            if mydeps.voice_mode: os.system(f'spd-say "{printable}"')
            print("+||||||||||||||||||||||||||||||||||||+")
            msg_hist = output.new_messages()
            output = await agent.run(input(), message_history=msg_hist, deps=mydeps)
            print("+||||||||||||||||||||||||||||||||||||+")
        except Exception as err:
            print(output.new_messages())
            msg_hist = output.new_messages()[len(msg_hist)//2:]
            raise err

if __name__ == "__main__":
    asyncio.run(main())
