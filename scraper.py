# imports
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json

options = Options()  # Options for creating drivers.
options.headless = True  # To run Microsoft Edge in without opening it!
options.add_argument("--window-size=1920,1080")  # Set window-size.

driver = webdriver.ChromiumEdge(options=options)  # create a new driver
driver.get("https://summerofcode.withgoogle.com/programs/2022/organizations")

# As the page is made using Angular, it takes time to load the webpage.
delay = 20  # seconds
try:
    myElem = WebDriverWait(driver, delay).until(
        EC.presence_of_element_located(
            (
                # Locator for grid element (sufficient to tell that page
                # is ready to be scraped).
                By.XPATH,
                "/html/body/app-root/app-layout/mat-sidenav-container/mat-sidenav-content[1]/div/div/main/app-program-organizations/app-orgs-grid/section[2]/div/div[3]/div",
            )
        )
    )
    print("Page is ready!")
except TimeoutException:
    print("Loading main page took too much time!")

i = 0  # Counter to store organisation number processed.
total = int(
    driver.find_element(
        By.XPATH,  # More fail-safe than using the class-name.
        "/html/body/app-root/app-layout/mat-sidenav-container/mat-sidenav-content[1]/div/div/main/app-program-organizations/app-orgs-grid/section[2]/div/mat-paginator/div/div/div[2]/div",
    )
    .text.strip()  # Remove trailing whitespaces.
    .split()
    .pop(-1)  # Get the last word from the string
)

json_begin = '{"organisations":['
json_end = "]}"

orgInCurrPage = driver.find_elements(By.CLASS_NAME, "card")
with open("scraped-data.json", "w") as outfile:
    print("Output json created.")
    outfile.write(json_begin)  # Json syntax.
    while True:
        for org in orgInCurrPage:
            gsocOrgLink = org.find_element(By.TAG_NAME, "a").get_attribute("href")
            name = org.find_element(By.CLASS_NAME, "name").text
            shortdscrp = org.find_element(By.CLASS_NAME, "short-description").text

            # Go to the gsoc webpage of the organisation with new driver.
            driver2 = webdriver.ChromiumEdge(options=options)
            driver2.get(gsocOrgLink)

            # Wait for the file to be loaded.
            try:
                myElem = WebDriverWait(driver2, delay).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "grid"))
                )
                i = i + 1
                print("Organisation", i, "data fetched.")
            except TimeoutException:
                print("Loading", gsocOrgLink, "took too much time!")

            tech = driver2.find_element(By.CLASS_NAME, "tech__content").text
            topic = driver2.find_element(By.CLASS_NAME, "topics__content").text
            orgLink = (
                driver2.find_element(By.CLASS_NAME, "link__wrapper")
                .find_element(By.TAG_NAME, "a")
                .get_attribute("href")
            )

            # Dictionary element for the organisation.
            details = {
                "name": name,
                "short-description": shortdscrp,
                "technologies": tech,
                "topics": topic,
                "gsoc-org-link": gsocOrgLink,
                "org-link": orgLink,
            }
            driver2.quit  # Close the gsoc webpage of the organisation.

            json.dump(details, outfile)  # Dump details in the file.
            if i < total:
                outfile.write(",")  # Comma is appended for json syntax.

        button = driver.find_element(
            By.XPATH,
            "/html/body/app-root/app-layout/mat-sidenav-container/mat-sidenav-content[1]/div/div/main/app-program-organizations/app-orgs-grid/section[2]/div/mat-paginator/div/div/div[2]/button[2]",
        )
        if button.is_enabled() == False:
            print("Reached final page, exiting...")
            break
        else:
            # Go to the next page.
            driver.execute_script("arguments[0].click();", button)  # Javascript.
            print("Clicked on Next Page »")
            orgInCurrPage = driver.find_elements(By.CLASS_NAME, "card")  # Update.

    outfile.write(json_end)  # Json syntax.
    outfile.close()

driver.quit()
