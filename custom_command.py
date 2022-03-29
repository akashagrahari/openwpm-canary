""" This file aims to demonstrate how to write custom commands in OpenWPM

Steps to have a custom command run as part of a CommandSequence

1. Create a class that derives from BaseCommand
2. Implement the execute method
3. Append it to the CommandSequence
4. Execute the CommandSequence

"""
import csv
from curses import newpad
import logging
import time
import json
import hashlib

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import sqlite3 as lite

from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket

FORMS_DB_DIR = "./datadir/forms.sqlite"

class FormParserCommand(BaseCommand):
    def __init__(self, site="") -> None:
        self.logger = logging.getLogger("openwpm")
        self.site = site

    # While this is not strictly necessary, we use the repr of a command for logging
    # So not having a proper repr will make your logs a lot less useful
    def __repr__(self) -> str:
        return "FormParserCommand"

    def updateDB(self,conn, cur, db_id, element_id, element_id_type, element_tag):
        # print("element_id: ", element_id, " element_id_type: ", element_id_type, " element_tag: ", element_tag)
        alreadyExists = False
        try:
            for id, pages  in cur.execute("SELECT id, pages FROM forms WHERE id='" + db_id+"'"):
                alreadyExists = True
                pagesList = json.loads(pages)
                if self.site not in pagesList:
                    pagesList.append(self.site)
                    newPages = json.dumps(pagesList)
                    # print("newPages: ", newPages, " db_id: ", db_id)
                    cur.execute("UPDATE forms SET pages=? WHERE id=?",(newPages, db_id))
                    break
        except lite.OperationalError:
            pass
        if not alreadyExists:
            pagesList = json.dumps([self.site])
            cur.execute("INSERT INTO forms (id, element_id, element_id_type, element_tag, pages) VALUES (?,?,?,?,?);", (db_id, element_id, element_id_type, element_tag, pagesList))
        conn.commit()

    def getElementIdentifier(self, element, element_tag):
        if element_tag == "form":
            if element.get_attribute("id") != "":
                return element.get_attribute("id"), "id"
            elif element.get_attribute("action") != "":
                return element.get_attribute("action"), "action"
            elif element.text != "":
                return element.text, "text"
            else:
                return "", "not_found"
        elif element_tag == "input":
            if element.get_attribute("id") != "":
                return element.get_attribute("id"), "id"
            elif element.get_attribute("placeholder") != "":
                return element.get_attribute("placeholder"), "placeholder"
            elif element.text != "":
                return element.text, "text"
            elif element.get_attribute("name") != "":
                return element.get_attribute("name"), "name"
            else:
                return "", "not_found"
    # Have a look at openwpm.commands.types.BaseCommand.execute to see
    # an explanation of each parameter
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        conn = lite.connect(FORMS_DB_DIR)
        cur = conn.cursor()
        inputs = webdriver.find_elements_by_tag_name("input")
        for element in inputs:
            # if element.get_attribute("id") == "Textbox-1":
            parent_element = element
            try:
                parent_element = element.find_element_by_xpath("./ancestor::form")
            except NoSuchElementException:
                self.logger.debug("No form found for input: %s", element.get_attribute("outerHTML"))
            element_tag = "input"
            if parent_element != element:
                element_tag = "form"
            element_id, element_id_type = self.getElementIdentifier(parent_element, element_tag)
            db_id = element_id + "|" + element_id_type + "|" + element_tag
            hashed_db_id = hashlib.sha1(db_id.encode("utf-8")).hexdigest()
            self.updateDB(conn,cur, hashed_db_id, element_id, element_id_type, element_tag)

        conn.close()

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
