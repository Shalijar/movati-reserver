from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

from datetime import datetime, timedelta
from threading import Timer
import time 
import sys


import os
from dotenv import load_dotenv

class GymBot:
    def __init__(self, gym_url, username, password):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--window-size=1920x1080")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.gym_url = gym_url
        self.username = username
        self.password = password
        self.main_page_url = 'https://groupexpro.com/schedule/577/?view=new'
        self.selected_location_index = None
        self.selected_location = None
        self.selected_date = None
        self.selected_date_index = None
        self.day_div_id = None
        self.selected_class_index = None

    def open_website(self):
        """Open the gym website."""
        self.driver.get(self.gym_url)

    def login(self):
        """Login to the gym website."""
        email_input = self.driver.find_element(By.ID, 'login')
        email_input.send_keys(self.username)

        password_input = self.driver.find_element(By.ID, 'password')
        password_input.send_keys(self.password)

        login_button = self.driver.find_element(By.CLASS_NAME, 'btn-class')
        login_button.click()


    def navigate_manually(self, url, wait_element_locator):
        """Navigate to the provided URL and wait for the specified element to be visible."""
        try:
            print("\n\033[1;33;49mWaiting for the page to load \033[0m", end="", flush=True)
            self.driver.get(url)

            # Wait for the specified element to be visible
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(wait_element_locator)
            )

            # Simulate loading with dots until the specified element is found
            # while  not self.is_element_present(wait_element_locator):
            #     print("adsfa")
            #     print("\033[1;33;49m.\033[0m", end="", flush=True)
            #     time.sleep(0.1)  # Adjust the sleep time as needed

            print("\n\033[1;32;49mPage loaded.\033[0m")


        except TimeoutException:
            print("\033[1;31;49mTimeout: Unable to find the specified element within the expected time.\033[0m")

        except Exception as e:
            print(f"\033[1;31;49mError during navigation: {e}\033[0m")

    def choose_location(self, location_index=None):
        """Choose the gym location."""
        try:
            dropdown = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'locationsGXP'))
            )

            select = Select(dropdown)
            options = select.options

            if location_index is None:
                print("Available locations:")
                for index, option in enumerate(options, start=1):
                    if (index == 1):
                        continue
                    temp = index
                    print(f"{temp}. {option.text}")
                selected_index = self.get_valid_input("Enter the number corresponding to your chosen location: ", options) 
                self.selected_location_index = selected_index
                location_index = selected_index
            else:
                selected_index = location_index
                
            select.select_by_index(location_index)
            self.selected_location = options[location_index].text
            print(f"Selected location: {options[selected_index].text}")

        except Exception as e:
            print("Unable to choose the location.")
            print(f"Error: {e}")


    DAY_DIV_MAPPING = {
        'Mon': 'GXPMonday',
        'Tue': 'GXPTuesday',
        'Wed': 'GXPWednesday',
        'Thu': 'GXPThursday',
        'Fri': 'GXPFriday',
        'Sat': 'GXPSaturday',
        'Sun': 'GXPSunday',
    }


    def choose_date(self, selected_date_index=None):
        """
        Choose a date interactively from the displayed options on the gym website.

        Returns:
        str: The day_div_id corresponding to the selected date.
        """
        try:
            date_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'day-column'))
            )
            if selected_date_index is None:
                print("Available dates:")
                formatted_dates = []
                for index, date_element in enumerate(date_elements, start=1):
                    day = date_element.get_attribute('data-day')
                    month = date_element.get_attribute('data-month')
                    date = date_element.find_element(By.CLASS_NAME, 'month-day').get_attribute('innerHTML')

                    formatted_date = datetime.strptime(f"{day} {month} {date}", "%A %B %d").strftime("%A, %B %d")
                    formatted_dates.append(formatted_date)
                    print(f"{index}. {formatted_date}")

                selected_index = int(input("Enter the number corresponding to your chosen date: ")) - 1
                self.selected_date_index = selected_index
            else:
                selected_index = selected_date_index
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located((By.ID, "overlay-overhaul"))
                )
            except TimeoutException:
                print("Overlay did not disappear within the timeout period.")
            
            while True:

                date_elements[selected_index].click()
                selected_date_text = date_elements[selected_index].text.strip()
                if selected_date_index is None:
                    print(f"Selected date: {formatted_dates[selected_index]}")

                    self.selected_date = formatted_dates[selected_index]

                    day_div_id = self.DAY_DIV_MAPPING.get(selected_date_text[:3])
                    self.day_div_id = day_div_id
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, f'//div[@id="{self.day_div_id}"]//div[contains(@class, "GXPEntry")]'))
                    )
                    break
                except TimeoutException:
                    print("Target element not found yet. Continuing to click.")

        except Exception as e:
            print("Unable to choose the date.")
            print(f"Error: {e}")


    
    def get_reservation_start_time(self, signup_button):
        """Get the reservation start time from the signup button."""
        reservation_start_time = signup_button.get_attribute('title').split(': ')[-1]

        # Remove leading newline character and adjust the datetime format
        reservation_start_time = reservation_start_time.lstrip("\n")
        reservation_time = datetime.strptime(reservation_start_time, "%m/%d/%Y at %I:%M%p")

        return reservation_time
    
    def refresh_in_time(self, reservation_start_time):

        # Remove leading newline character and adjust the datetime format
        current_time = datetime.now().replace(second=0, microsecond=0)
        print("Current Time", current_time)
        print("Reservation Start Time", reservation_start_time)

        if current_time < reservation_start_time:
            time_difference = reservation_start_time - current_time
            seconds_remaining = int(time_difference.total_seconds())

            self.display_seconds_remaining(seconds_remaining)

        return
    
    def perform_actions(self, selected_index):
        self.driver.refresh()
        self.choose_location(self.selected_location_index)
        time.sleep(2)
        self.choose_date(self.selected_date_index)
        time.sleep(2)
        self.choose_class(selected_index)

    def choose_class(self, selected_class_index=None):
        try:
            # Wait for the class elements to be present
            class_elements = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'//div[@id="{self.day_div_id}"]//div[contains(@class, "GXPEntry")]')
                )
            )
            print("this is the selected class index", selected_class_index)
            if selected_class_index is None:
                print("Available classes:")

            for index, class_element in enumerate(class_elements, start=1):
                try:

                    try: 
                        class_time = class_element.find_element(By.XPATH, './/div[contains(@class, "GXPTime")]').get_attribute('innerHTML')
                    except:
                        class_time = 'No time available'

                    try: 
                        gxptitle_children = class_element.find_elements(By.XPATH, './/div[contains(@class, "GXPTitle")]/child::*')
                        title_elements_text = [child.get_attribute('innerText') for child in gxptitle_children]
                        title_element = ' '.join(title_elements_text).strip()
                    except:
                        title_element = 'No title available'

                    try:
                        instructor_element = class_element.find_element(By.XPATH, './/div[contains(@class, "GXPInstructor")]').get_attribute('innerText')
                    except:
                        instructor_element = 'No instructor available'

                    try:
                        studio_location_element = class_element.find_element(By.XPATH, './/div[contains(@class, "GXPStudio")]//span[contains(@class, "row-studio")]').get_attribute('innerText')
                    except:
                        studio_location_element = 'No studio location available'

                    try:
                        class_capacity_info = class_element.find_element(By.XPATH, './/div[contains(@class, "GXPDescription")]/span').get_attribute('innerHTML')
                    except:
                        class_capacity_info = 'No capacity info available'
                    
                    try:
                        reservation_start_time = self.get_reservation_start_time(class_element.find_element(By.XPATH, './/button[contains(@class, "signup-btn")]'))
                    except:
                        reservation_start_time = ''
                    if selected_class_index is None:
                        print(f"{index}. {class_time} - {title_element} with {instructor_element} at {studio_location_element} - {class_capacity_info} - {reservation_start_time}\n")

                except StaleElementReferenceException:
                    pass

                except Exception as e:
                    print(f"Error retrieving details for class index {index}: {e}")
            if selected_class_index is  None:
                selected_index = self.get_valid_input("Enter the number corresponding to your chosen class: ", class_elements)
            else:
                selected_index = selected_class_index

            class_element = class_elements[selected_index]

            try:
                reservation_start_time = self.get_reservation_start_time(class_element.find_element(By.XPATH, './/button[contains(@class, "signup-btn")]'))
            except:
                reservation_start_time = datetime.now() - timedelta(days=1)

            if reservation_start_time > datetime.now():
                self.refresh_in_time(reservation_start_time)
                self.perform_actions(selected_index)



                # self.choose_date()
            try:
                print('checking for signup button')
                print(class_element)
                signup_button = class_element.find_element(By.XPATH, './/a[contains(@class, "btn signup-btn btn-color-setting signup-btn-color signUpGXP")]')
                signup_button_url = signup_button.get_attribute('href')
                print("Sign-up URL:", signup_button_url)
                self.automatic_signup(signup_button_url)
            except:
                print("No sign-up button found.")
            # self.handle_signup_button(signup_button_url)
            return

            if not signup_button.is_enabled():
                # self.handle_signup_button(signup_button)
                print("found a disabled button")
            else:
                print("Sign-up URL:", signup_button_url)
                self.automatic_signup(signup_button_url)

        except Exception as e:
            print("Unable to choose a class.")
            print(f"Error: {e}")

    def get_valid_input(self, prompt, class_elements):
        while True:
            try:
                selected_index = int(input(prompt)) - 1

                if 0 <= selected_index < len(class_elements):
                    return selected_index

                print("Index out of range. Try again.")

            except ValueError:
                print("Invalid input. Please enter a valid input.")


        
    def display_seconds_remaining(self, seconds_remaining):
        while seconds_remaining > 0:
            days, seconds = divmod(seconds_remaining, 86400)
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)

            time_remaining = ""
            if days > 0:
                time_remaining += f"{days} days, "
            if hours > 0 or time_remaining:
                time_remaining += f"{hours} hours, "
            if minutes > 0 or time_remaining:
                time_remaining += f"{minutes} minutes, "
            time_remaining += f"{seconds} seconds"

            print(f"Time remaining: {time_remaining}", end="\r")
            time.sleep(1)  # Wait for 1 second
            seconds_remaining -= 1
        time.sleep(2) 


    def automatic_signup(self, signup_url: str):
        print("Signing up for the selected class...")
        try:
            # Click the signup button
            self.driver.get(signup_url)
            signup_button = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="schedule-container"]/div/div/form/fieldset/div/div[2]/input'))
                    )
            signup_button.click()
            print("Successfully signed up for the selected class.")
            cancel_button = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'cancelReservation'))
                    )
            cancel_button_href = cancel_button.get_attribute('href')
            if input("Press C to cancel the reservation or any other key to go back to the main page.\n").lower() == 'c':
                self.driver.get(cancel_button_href)
                print("Successfully cancelled the reservation.")
            print("Going back to the main page...")
            self.navigate_manually(self.main_page_url, wait_element_locator=(By.ID, 'locationsGXP'))

        except Exception as e:
            print(f"Error during automatic sign-up: {e}")

    def run_menu(self):
        """Run the main menu loop."""
        day_div_id = None

        while True:
            self.print_menu_options()

            if self.selected_location:
                print(f"Selected Location: {self.selected_location}")
            if self.selected_date:
                print(f"Selected Date: {self.selected_date}")

            choice = input("Enter your choice: ")
            if choice == '1':
                self.choose_location_menu()
            elif choice == '2':
                self.choose_date_menu()
            elif choice == '3':
                self.choose_class_menu()
            elif choice == '4':
                print("Quitting...")
                sys.exit(0)
            else:
                print("Invalid choice. Please enter a valid option.")

    def print_menu_options(self):
        """Print the main menu options with  formatting."""
        print("\n\033[1;37;49m========== Gym Reservation Menu ==========\033[0m")
        print("\n\033[1;36;49m1. Choose Location\033[0m")
        print("\n\033[1;36;49m2. Choose Date\033[0m")
        print("\n\033[1;36;49m3. Choose Class\033[0m")
        print("\n\033[1;31;49m4. Quit\033[0m")
        print("\n\033[1;37;49m==========================================\033[0m\n")

    def choose_location_menu(self):
        """Menu for choosing the gym location."""
        if self.driver.current_url != self.main_page_url:
            self.navigate_manually(self.main_page_url, wait_element_locator=(By.ID, 'locationsGXP'))
        self.choose_location()

    def choose_date_menu(self):
        """Menu for choosing the date."""
        if self.driver.current_url != self.main_page_url:
            self.navigate_manually(self.main_page_url, wait_element_locator=(By.ID, 'locationsGXP'))
        self.choose_date()

    def choose_class_menu(self):
        """Menu for choosing the gym class."""
        if self.driver.current_url != self.main_page_url:
            self.navigate_manually(self.main_page_url, wait_element_locator=(By.ID, 'locationsGXP'))
        if self.day_div_id is None:
            print("Please choose a date first.")
            return
        self.choose_class()


def main():
    load_dotenv()

    gym_url = 'https://groupexpro.com/gxp/auth/login/reservations-schedule-profile-577?c=1&e=0&type=new&location=2311'  # Replace with the actual URL

    gym_username = os.getenv("GYM_USERNAME")
    gym_password = os.getenv("GYM_PASSWORD")

    gym_bot = GymBot(gym_url, gym_username, gym_password)

    try:
        gym_bot.open_website()

        gym_bot.login()

        gym_bot.run_menu()

    finally:

        pass

if __name__ == "__main__":
    main()
