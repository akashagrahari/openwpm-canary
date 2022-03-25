""" This file aims to demonstrate how to write custom commands in OpenWPM

Steps to have a custom command run as part of a CommandSequence

1. Create a class that derives from BaseCommand
2. Implement the execute method
3. Append it to the CommandSequence
4. Execute the CommandSequence

"""
import logging

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By

from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket
from PIL import Image
import io

class FormCountingCommand(BaseCommand):
    def __init__(self) -> None:
        self.logger = logging.getLogger("openwpm")

    # While this is not strictly necessary, we use the repr of a command for logging
    # So not having a proper repr will make your logs a lot less useful
    def __repr__(self) -> str:
        return "LinkCountingCommand"

    # Have a look at openwpm.commands.types.BaseCommand.execute to see
    # an explanation of each parameter
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        forms = webdriver.find_elements_by_tag_name("form")
        for form in forms:
            form_parent = form.find_element_by_xpath("..").find_element_by_xpath("..")
            image = form_parent.screenshot_as_png
            imageStream = io.BytesIO(image)
            im = Image.open(imageStream)
            im.save("./blahness.png")
            print("the real form:" + form_parent.get_attribute("outerHTML"))
            print("form text: ", form.text, " ; form id: ", form.get_attribute('id'))
            
        # current_url = webdriver.current_url
        # link_count = len(webdriver.find_elements(By.TAG_NAME, "a"))
        # self.logger.info("There are %d links on %s", link_count, current_url)

class LinkCountingCommand(BaseCommand):
    """This command logs how many links it found on any given page"""

    def __init__(self) -> None:
        self.logger = logging.getLogger("openwpm")

    # While this is not strictly necessary, we use the repr of a command for logging
    # So not having a proper repr will make your logs a lot less useful
    def __repr__(self) -> str:
        return "LinkCountingCommand"

    # Have a look at openwpm.commands.types.BaseCommand.execute to see
    # an explanation of each parameter
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        current_url = webdriver.current_url
        link_count = len(webdriver.find_elements(By.TAG_NAME, "a"))
        self.logger.info("There are %d links on %s", link_count, current_url)
        print(webdriver.find_element(By.TAG_NAME, "a"))
        print(webdriver.find_element(By.TAG_NAME, "a").text)
        print(webdriver.find_element(By.TAG_NAME, "a").size)
