import json
import requests
import time
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook, DiscordEmbed


def scrape_products():
    page = 1
    new_products = []
    full_product_list = []

    # Load existing products from JSON file, if it exists
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            saved_products = json.load(f)
            saved_product_ids = {
                product["id"] for product in saved_products
            }  # Track existing product IDs
            full_product_list = saved_products  # Initialize with the current products
    except FileNotFoundError:
        saved_product_ids = set()

    # Loop through each page until no products are returned
    while True:
        base_url = f"https://chiikawamarket.jp/collections/newitems/products.json?limit=250&sort_by=created-descending&page={page}"
        response = requests.get(base_url)
        data = response.json()

        # Break the loop if no more products are found on the current page
        if not data.get("products"):
            break

        # Check for new products by comparing product IDs
        for product in data["products"]:
            if product["id"] not in saved_product_ids:
                formatted_tags = " ".join(f"{tag}" for tag in product["tags"])

                # Extract title, price, first image URL, and handle for alert
                product_info = {
                    "title": product["title"],
                    "price": product["variants"][0]["price"],
                    "first_image": (
                        product["images"][0]["src"]
                        if product["images"]
                        else "No image available"
                    ),
                    "url": f"https://chiikawamarket.jp/collections/newitems/products/{product['handle']}",
                    "tags": formatted_tags,
                }
                new_products.append(
                    product_info
                )  # Add new product info to the alert list

                # Append full product data to the main list and update the saved IDs
                full_product_list.append(product)
                saved_product_ids.add(product["id"])

        page += 1

    # If there are new products, alert and update products.json
    if new_products:
        print("New products found!")
        for product in new_products:
            print(product)

            webhook = DiscordWebhook(
                url="https://discord.com/api/webhooks/1300628977140109344/SuB_HswOB7adKDhjodBnaEXWmLRl8iJUypRAZ2rIv2CIeInvRKkh_4eHae5Q8nHbOVpO"
            )

            embed = DiscordEmbed(
                title=product["title"],
                description=product["tags"],
                url=product["url"],
                color="03b2f8",
            )
            embed.add_embed_field(name="Price", value=product["price"])
            embed.set_timestamp()
            embed.set_image(url=product["first_image"])
            webhook.add_embed(embed)

            response = webhook.execute()

        # Update the saved products file with the updated full product list
        with open("products.json", "w", encoding="utf-8") as f:
            json.dump(full_product_list, f, ensure_ascii=False, indent=4)
    else:
        print("No new products found.")


# Run the scraping every hour, precisely on the hour
while True:
    scrape_products()

    # Calculate the next hour
    now = datetime.now()
    next_hour = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait_time = (next_hour - now).total_seconds()
    print(f"Waiting until the next minutes ({wait_time}) before the next scrape...")
    time.sleep(wait_time)
