from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re



# Initialize DataFrame to store information
columns = ['Title', 'Price', 'Neighborhood', 'Size', 'Rooms', 'Bedrooms', 'Bathrooms', 'Floors', 'Additional Information', 'Location']
df = pd.DataFrame(columns=columns)

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 10)

# Go to the website
driver.get("https://www.mubawab.ma/fr/ct/tanger/immobilier-a-vendre")

# Find the element containing the text with the number of pages
element = driver.find_element(By.XPATH, '//*[@id="mainListing"]/p')

# Extract the text from the element
text = element.text

# Use a regular expression to find the number of pages within the text
match = re.search(r'(\d+)(?=\s*pages)', text)
if match:
    num_pages = int(match.group(0))
else:
    num_pages = None

print(f"Number of pages: {num_pages}")

# Don't forget to close the driver after your scraping job is done
driver.quit()

for k in range(1, num_pages+1):  # Adjust the range as needed
    # Initialize the WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver,4)

    # Go to the website
    driver.get("https://www.mubawab.ma/fr/ct/tanger/immobilier-a-vendre:p:" + str(k))

    try:
        n = 1
        while True:
            # Scroll to ensure visibility of the element
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Adjust based on your internet speed and the site's loading time

            listing_xpath = f"//*[@id='mainListing']/ul/li[{n}]"
            listings = driver.find_elements(By.XPATH, listing_xpath)

            if not listings:
                print("No more listings found on page. Ending the loop.")
                break

            driver.execute_script("arguments[0].scrollIntoView();", listings[0])

            try:
                listings[0].click()
                wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/section/div[2]/div/div[1]/h1")))

                # Extract information
                title = driver.find_element(By.XPATH, "/html/body/section/div[2]/div/div[1]/h1").text
                price = driver.find_element(By.XPATH, "/html/body/section/div[2]/div/div[1]/div[1]/div[1]/h3").text
                neighborhood = driver.find_element(By.XPATH, "/html/body/section/div[2]/div/div[1]/h3").text
                details_elements = driver.find_elements(By.XPATH,
                                                        "//html/body/section/div[2]/div/div[9]/div/ul/li/div/div/span")
                details = [detail.text for detail in details_elements]
                additional_info_elements = driver.find_elements(By.XPATH,
                                                                "/html/body/section/div[2]/div/div[1]/div[2]/span")
                additional_info = [info.text for info in additional_info_elements]

                # Correct the location extraction
                location_button = driver.find_element(By.XPATH, '//*[@id="mapClosed"]/div/a')
                driver.execute_script("arguments[0].click();", location_button)
                time.sleep(1)  # Wait for the map to load

                lat = driver.find_element(By.ID, 'mapOpen').get_attribute('lat')
                lon = driver.find_element(By.ID, 'mapOpen').get_attribute('lon')
                location = [lat, lon]

                size = rooms = bathrooms = bedrooms = floors = "Not specified"
                additional_info_cleaned = []

                for info in additional_info:
                    if 'm²' in info:
                        size = info
                    elif 'hambre' in info:
                        bedrooms = info
                    elif 'ièce' in info:
                        rooms = info
                    elif 'bain' in info:
                        bathrooms = info
                    elif 'étage' in info:
                        floors = info
                    else:
                        additional_info_cleaned.append(info)

                new_row = {'Title': title, 'Price': price, 'Neighborhood': neighborhood, 'Size': size,
                           'Rooms': rooms, 'Bedrooms': bedrooms, 'Bathrooms': bathrooms, 'Floors': floors, 'Additional Information': additional_info_cleaned,
                           'Location': location}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                # Go back to the listings page
                driver.back()
                time.sleep(1)

            except TimeoutException:
                print(f"Element not clickable for listing {n}, moving to the next.")
                driver.back()
            except Exception as e:
                print(f"An error occurred: {e}")
                driver.back()

            print("Added a new row : page "+str(k)+" listing "+str(n))
            print(new_row)

            n += 1
    except Exception as e:
        print(f"An error occurred: {e}")

    # Close the WebDriver
    driver.quit()

# Save the DataFrame to CSV with a timestamped filename
timestamp = datetime.now().strftime('%Y.%m.%d_%H.%M')
filename = f"{timestamp}_extract_mubawab_vente_tanger.csv"
df.to_csv(filename, index=False)
print(f"Data saved to {filename}")