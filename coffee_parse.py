# to run: python .\coffee_parse.py
# pip install beautifulsoup4
# pip install selenium

import csv
from selenium import webdriver
import os

from bs4 import BeautifulSoup

#function to visit and  save webpage so it is kind to the web site owner 
def archive_page(url, file):
    # Create a Chrome WebDriver instance
    driver = webdriver.Chrome()

    # Visit a webpage
    print(f"Visiting {url}")
    driver.get(url)

    # Save the HTML of the page to a file
    html = driver.page_source
    with open(file, "w", encoding="utf-8") as file:
        file.write(html)

    # Close the WebDriver
    driver.quit()

#Target save location
SAVE_FOLDER = "saved_data"

#cya for target location
if not os.path.exists(SAVE_FOLDER):
    os.mkdir(SAVE_FOLDER)

#instock coffees
STOCKED_COFFEE_WEB = "https://www.sweetmarias.com/green-coffee.html?product_list_limit=all&sm_status=1"
STOCKED_COFFEE_FILE = f"{SAVE_FOLDER}\\green-coffee-stocked.html"

# check if page is saved localy first
# if not cache page
if not os.path.exists(STOCKED_COFFEE_FILE):
    archive_page( STOCKED_COFFEE_WEB, STOCKED_COFFEE_FILE)

#archived coffees
UNSTOCKED_COFFEE_WEB = "https://www.sweetmarias.com/green-coffee.html?product_list_limit=all&sm_status=2"
UNSTOCKED_COFFEE_FILE = f"{SAVE_FOLDER}\\green-coffee-outofstock.html"
# repeat as above but archived coffes
if not os.path.exists(UNSTOCKED_COFFEE_FILE):
    archive_page( UNSTOCKED_COFFEE_WEB, UNSTOCKED_COFFEE_FILE)


#define function to clean up bad text or odd characters
def clean_text(text_string):
    return (
        text_string.replace("\n", "")
        .replace("\u00f1", "n")
        .replace("\u00f3", "o")
        .replace("\u00fb", "u")
        .replace("\u00a0", " ")
        .replace("\u00e9", "e")
        .replace("\u00ed", "i")
        .replace("\u00e1", "a")
        .replace("\u00fa", "u")
        .replace("\u00e7", "c")
        .replace("\u00e3", "a")
        .strip()
        if text_string
        else text_string
    )

#translate the html
def parse_coffee_table(html_file):
    coffees = []
    #parse html
    with open(html_file, encoding="utf-8") as fp:
        #make soup
        soup = BeautifulSoup(fp, features="html.parser")
        tbody = soup.find("tbody")
        tr_elements = tbody.find_all("tr")
        #for each element
        #elements are in pairs of rows prod andquick view
        for i in range(0, len(tr_elements), 2):
            product_row = tr_elements[i]
            quickview_row = tr_elements[i + 1]

            #get thumbnailes fo items, found ot needed as data in html, kept incase wanted for image processing another time
            product_img = ""
            cupping_thumb = ""
            flavor_thumb = ""

            short_desc = ""

            # a class="product-item-link"
            # internal text is name
            # href should be product url
            price_link = product_row.find("a", class_="product-item-link")
            name = price_link.get_text() if price_link else ""
            product_url = price_link.get("href") if price_link else ""

            #get the cost data
            # span class="price"
            price_data = product_row.find("span", class_="price")
            price = price_data.get_text() if price_data else ""

            # <p> under div class="short-description"
            # or div text
            desc_div = quickview_row.find("div", class_="short-description")
            if desc_div.find("p"):
                for p_tag in desc_div.find_all("p"):

                    short_desc = (
                        p_tag.get_text()
                        if short_desc == ""
                        else short_desc + "\n" + p_tag.get_text()
                    )
            else:
                short_desc = desc_div.get_text()

            #images in coffee quickview
            imgs = quickview_row.find_all("img")
            for img in imgs:
                img_class = img.get("class")
                img_url = img.get("data-src")

                if "product-image-photo" in img_class:
                    product_img = img_url
                elif "quick-view-first-image" in img_class:
                    cupping_thumb = img_url
                elif "quick-view-second-image" in img_class:
                    flavor_thumb = img_url

            #add record with name, url, desc, price, prod img, cupping, flavor
            coffees.append(
                {
                    'name':clean_text(name),
                    'product_url':product_url,
                    'short_desc':clean_text(short_desc),
                    'price':price,
                    'product_img':product_img,
                    'cupping_thumb':cupping_thumb,
                    'flavor_thumb':flavor_thumb,
                }
            )
    return coffees

#add the in-stock and archived coffees togather for full list
all_coffee = parse_coffee_table(STOCKED_COFFEE_FILE) + parse_coffee_table(UNSTOCKED_COFFEE_FILE)

#pars coffees from product files
def parse_coffee_product_page(product_file):
    #start details
    coffee_details = {}
    with open(product_file, encoding="utf-8") as fp:
        #make soup
        soup = BeautifulSoup(fp, features="html.parser")

        # div class="score-value", get score
        score_data = soup.find("div", class_="score-value")
        if score_data:
            coffee_details["score"] = score_data.get_text()

        # div class="stock", in stock?
        availability_data = soup.find("div", class_="stock")
        if availability_data:
            coffee_details["availability"] = clean_text(
                availability_data.find("span").get_text()
            )

        # div data-chart-id="flavor-chart", the coffee flavor scores
        flavor_chart = soup.find("div", attrs={"data-chart-id": "flavor-chart"})
        if flavor_chart:
            # Floral:0,Honey:0,Sugars:3.5,Caramel:1,Fruits:4,Citrus:0,Berry:3.5,Cocoa:3,Nuts:0,Rustic:2.5,Spice:2,Body:4
            value = flavor_chart.get("data-chart-value")
            print(f"Parsing flavor values:{value}")
            for flavor_value in value.split(","):
                attribute, rating = flavor_value.split(":")
                coffee_details[f'flavor_{attribute.lower().replace(" ","_")}'] = rating

        # div data-chart-id="cupping-chart", the coffee cupping scores
        cupping_chart = soup.find("div", attrs={"data-chart-id": "cupping-chart"})
        if cupping_chart:
            # Dry Fragrance:8.4,Wet Aroma:8.7,Brightness:8.3,Flavor:8.8,Body:9,Finish:8,Sweetness:8.6,Clean Cup:7.7,Complexity:9,Uniformity:8.5
            value = cupping_chart.get("data-chart-value")
            print(f"Parsing cupping values:{value}")
            for cupping_value in value.split(","):
                attribute, rating = cupping_value.split(":")
                coffee_details[f'cup_{attribute.lower().replace(" ","_")}'] = rating

        # Coffee demographics table
        td_elements = soup.find_all("td")
        for element in td_elements:
            data_type = element.get("data-th")
            data_text = clean_text(element.get_text())
            if data_type == "Region":
                coffee_details["region"] = data_text
            elif data_type == "Processing":
                coffee_details["processing"] = data_text
            elif data_type == "Drying Method":
                coffee_details["drying"] = data_text
            elif data_type == "Arrival date":
                coffee_details["arrival"] = data_text
            elif data_type == "Packaging":
                coffee_details["packaging"] = data_text
            elif data_type == "Farm Gate":
                coffee_details["farm"] = data_text
            elif data_type == "Cultivar Detail":
                coffee_details["cultivar"] = data_text
            elif data_type == "Grade":
                coffee_details["grade"] = data_text
            elif data_type == "Roast Recommendations":
                coffee_details["roast"] = data_text
            elif data_type == "Weight":
                coffee_details["weight"] = data_text
            elif data_type == "Type":
                coffee_details["type"] = data_text

    return coffee_details

#start coffee data
all_cofee_data = []

PRODUCTS_FOLDER = f"{SAVE_FOLDER}\\products"

if not os.path.exists(PRODUCTS_FOLDER):
    os.mkdir(PRODUCTS_FOLDER)

#process the coffees to get the details for each one
total_coffee= len(all_coffee)
for i, coffee in enumerate(all_coffee):
    print(f"processing {i} of {total_coffee}")
    product_url = coffee.get("product_url", "")
    if product_url:
        # check if page is saved localy first
        # if not cache page
        #get only the base/file or coffee name not full path
        local_product_page = f"{PRODUCTS_FOLDER}\\{os.path.basename(product_url)}"
        if not os.path.exists(local_product_page):
            archive_page(product_url,local_product_page)

        coffee_details = parse_coffee_product_page(local_product_page)
        # combine dicts py 3.9 method
        coffee_data = coffee | coffee_details
        all_cofee_data.append(coffee_data)

#save to final data list
COFFEE_DATA_FILE = f"{SAVE_FOLDER}\\enriched_list_all.csv"

#write coffee data 
with open(COFFEE_DATA_FILE, "w", newline="", encoding="utf-8") as file:
    print(f"writing csv {COFFEE_DATA_FILE}")
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)

    # Write the header
    writer.writerow(
        [
            "name",
            "product_url",
            "price",
            "availability",
            "score",
            "region",
            "processing",
            "drying",
            "arrival",
            "packaging",
            "farm",
            "cultivar",
            "grade",
            "roast",
            "weight",
            "type",
            "flavor_floral",
            "flavor_honey",
            "flavor_sugars",
            "flavor_caramel",
            "flavor_fruits",
            "flavor_citrus",
            "flavor_berry",
            "flavor_cocoa",
            "flavor_nuts",
            "flavor_rustic",
            "flavor_spice",
            "flavor_body",
            "cup_dry_fragrance",
            "cup_wet_aroma",
            "cup_brightness",
            "cup_flavor",
            "cup_body",
            "cup_finish",
            "cup_sweetness",
            "cup_clean_cup",
            "cup_complexity",
            "cup_uniformity",
            "short_desc",
            "product_img",
            "cupping_thumb",
            "flavor_thumb",
        ]
    )

    # coffee per-row
    for i, coffee in enumerate(all_cofee_data):
        print(f"writing {i} of {total_coffee}")
        writer.writerow(
            [
                coffee.get("name", ""),
                coffee.get("product_url", ""),
                coffee.get("price", ""),
                coffee.get("availability", ""),
                coffee.get("score", ""),
                coffee.get("region", ""),
                coffee.get("processing", ""),
                coffee.get("drying", ""),
                coffee.get("arrival", ""),
                coffee.get("packaging", ""),
                coffee.get("farm", ""),
                coffee.get("cultivar", ""),
                coffee.get("grade", ""),
                coffee.get("roast", ""),
                coffee.get("weight", ""),
                coffee.get("type", ""),
                coffee.get("flavor_floral", ""),
                coffee.get("flavor_honey", ""),
                coffee.get("flavor_sugars", ""),
                coffee.get("flavor_caramel", ""),
                coffee.get("flavor_fruits", ""),
                coffee.get("flavor_citrus", ""),
                coffee.get("flavor_berry", ""),
                coffee.get("flavor_cocoa", ""),
                coffee.get("flavor_nuts", ""),
                coffee.get("flavor_rustic", ""),
                coffee.get("flavor_spice", ""),
                coffee.get("flavor_body", ""),
                coffee.get("cup_dry_fragrance", ""),
                coffee.get("cup_wet_aroma", ""),
                coffee.get("cup_brightness", ""),
                coffee.get("cup_flavor", ""),
                coffee.get("cup_body", ""),
                coffee.get("cup_finish", ""),
                coffee.get("cup_sweetness", ""),
                coffee.get("cup_clean_cup", ""),
                coffee.get("cup_complexity", ""),
                coffee.get("cup_uniformity", ""),
                coffee.get("short_desc", ""),
                coffee.get("product_img", ""),
                coffee.get("cupping_thumb", ""),
                coffee.get("flavor_thumb", ""),
            ]
        )