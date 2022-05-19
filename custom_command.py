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

    def updateDB(self,conn, cur, db_id, element_id, element_id_type, element_text, element_tag):
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
                    # print("added page to form: with id: " + str(element_id))
                    break
        except lite.OperationalError:
            pass
        if not alreadyExists:
            pagesList = json.dumps([self.site])
            cur.execute("INSERT INTO forms (id, element_id, element_id_type, element_text, element_tag, pages) VALUES (?,?,?,?,?,?);", (db_id, element_id, element_id_type, element_text, element_tag, pagesList))
            print("inserted new form: " + str(element_id))
        conn.commit()

    def get_input_text(self, input_element):
        return input_element.get_attribute("placeholder") or input_element.text
    
    def get_form_text(self, form_element):
        element_text = ''
        inputs = form_element.find_elements_by_tag_name("input")
        for input in inputs:
            element_text += "\n" + self.get_input_text(input)
        element_text = element_text.strip()
        if element_text == '':
            print("empty element text. Fallback to form.text")
            element_text = form_element.text
        return element_text
    
    def get_form_id_and_tag(self, form_element):
        if form_element.get_attribute("id") != "":
            return form_element.get_attribute("id"), "id"
        else: 
            inputs = form_element.find_elements_by_tag_name("input")
            element_id = ''
            for input in inputs:
                input_id_and_tag = self.get_input_id_and_tag(input)
                id = input_id_and_tag[0]
                tag = input_id_and_tag[1]
                if tag == "id" or tag == "name":
                    element_id += "," + id
            element_id = element_id.strip(',')
            if element_id == '':
                return "", "not_found"
            return element_id, "input_ids"
    
    def get_input_id_and_tag(self, input_element):
            if input_element.get_attribute("id") != "":
                return input_element.get_attribute("id"), "id"
            elif input_element.get_attribute("name") != "":
                return input_element.get_attribute("name"), "name"
            elif input_element.get_attribute("placeholder") != "":
                return input_element.get_attribute("placeholder"), "placeholder"
            elif input_element.text != "":
                return input_element.text, "text"
            else:
                print("no id and tag found")
                return '',''
    
    def getElementIdentifierAndTag(self, element, element_tag):
        if element_tag == "form":
           return self.get_form_id_and_tag(element)
            # elif element.get_attribute("action") != "":
            #     return element.get_attribute("action"), "action"
        elif element_tag == "input":
            return self.get_input_id_and_tag(element)
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
        # print("in FORM execute")
        # print("inputs")
        # print(inputs)
        for element in inputs:
            # if element.get_attribute("id") == "Textbox-1":
            parent_element = element
            try:
                print("---------------------------")
                parent_element = element.find_element_by_xpath("./ancestor::form")
                # print("Found ancestor::form")
                # print(parent_element.tag_name)
                # print(parent_element.text)
                # print("href: ")
                # print(parent_element.get_attribute("href"))
            except NoSuchElementException:
                # print("Didn't Find ancestor::form")
                # print(parent_element.tag_name)
                # print(parent_element.text)
                # print("href: ")
                # print(parent_element.get_attribute("href"))
                self.logger.debug("No form found for input: %s", element.get_attribute("outerHTML"))
            element_tag = ""
            if parent_element != element:
                element_tag = "form"
                # element_text = parent_element.text
                element_text = self.get_form_text(parent_element)
                
            else:
                element_tag = "input"
                element_text = self.get_input_text(element)
            element_id, element_id_type = self.getElementIdentifierAndTag(parent_element, element_tag)
            if element_id == '' or element_id == None:
                # print("element id not found, trying with the input element...")
                # print("element")
                # print(element)
                # print("parent_element")
                # print(parent_element)
                element_id, element_id_type = self.getElementIdentifierAndTag(element, element_tag)
            # print("form_input id")
            # print(element_id)
            # print(element_id_type)
            # print("element_text")
            # print(element_text)
            # print("---------------------------")
            db_id = element_id + "|" + element_id_type + "|" + element_tag
            hashed_db_id = hashlib.sha1(db_id.encode("utf-8")).hexdigest()
            self.updateDB(conn,cur, hashed_db_id, element_id, element_id_type, element_text, element_tag)

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


class AllowCookiesCommand(BaseCommand):
    def __init__(self) -> None:
        self.logger = logging.getLogger("openwpm")

    # While this is not strictly necessary, we use the repr of a command for logging
    # So not having a proper repr will make your logs a lot less useful
    def __repr__(self) -> str:
        return "AllowCookiesCommand"
    
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
        ) -> None:
            ot_allow_cookies_script = "OneTrust.AllowAll()"
            # ot_allow_cookies_script = "console.log('x')"
            try:
                print("running script")
                webdriver.execute_script(ot_allow_cookies_script);
            except Exception as e:
                print("error in running script")
                print(str(e))
            print("ran OT script")

