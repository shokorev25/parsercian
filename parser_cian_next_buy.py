import requests
import csv
from datetime import datetime
import time

REGION_IDS = [
    4649, 4686, 4689, 4762, 4774, 4884, 4972, 5010, 5021, 5030,
    5033, 5035, 5049, 5059, 174178, 174274, 174351, 174511,
    174700, 174986, 175838, 175889, 1241882
]

def try_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def clean_text(value):
    if isinstance(value, str):
        return value.replace("\n", " ").replace("\r", " ").replace(",", ".").strip()
    return value

def safe_get(d, path, default=None):
    for key in path:
        if isinstance(d, dict):
            d = d.get(key)
        else:
            return default
    return d

def get_offer(item):
    price = try_float(item.get("bargainTerms", {}).get("priceRur"))
    area = try_float(item.get("totalArea"))
    price_per_m2 = round(price / area, 2) if price and area else None

    return {
        "id": item.get("id"),
        "date": datetime.fromtimestamp(item["addedTimestamp"]).strftime('%Y-%m-%d %H:%M:%S') if item.get("addedTimestamp") else None,
        "url": clean_text(item.get("fullUrl")),
        "price": price,
        "price_per_m2": price_per_m2,
        "address": clean_text(safe_get(item, ["geo", "userInput"])),
        "district": clean_text(safe_get(item, ["geo", "districtName"])),
        "sub_region": clean_text(safe_get(item, ["geo", "subLocalityName"])),
        "area": area,
        "area_unit": clean_text(item.get("totalAreaUnit")),
        "room_area": try_float(safe_get(item, ["space", "area"])),
        "floor": safe_get(item, ["floorNumber"]),
        "total_floors": safe_get(item, ["building", "floorsCount"]),
        "year_built": safe_get(item, ["building", "buildYear"]),
        "building_type": clean_text(safe_get(item, ["building", "materialType", "name"])),
        "building_class": clean_text(safe_get(item, ["building", "buildingClass", "name"])),
        "has_parking": safe_get(item, ["building", "parking", "hasParking"]),
        "description": clean_text(item.get("description")),
        "client_id": safe_get(item, ["user", "userId"]),
        "agency_name": clean_text(safe_get(item, ["user", "companyName"])),
        "lat": try_float(safe_get(item, ["geo", "coordinates", "lat"])),
        "lng": try_float(safe_get(item, ["geo", "coordinates", "lng"])),
    }

def get_json(region_id, page=1):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://irkutsk.cian.ru",
        "Referer": "https://irkutsk.cian.ru/"
    }

    payload = {
        "jsonQuery": {
            "_type": "commercialsale",
            "engine_version": {"type": "term", "value": 2},
            "region": {"type": "terms", "value": [region_id]},
            "offer_type": {"type": "terms", "value": ["offices"]},
            "page": {"type": "term", "value": page},
            "sort": {"type": "term", "value": "creation_date_desc"}
        }
    }

    response = requests.post(
        'https://api.cian.ru/search-offers/v2/search-offers-desktop/',
        json=payload,
        headers=headers
    )
    response.raise_for_status()
    return response.json()

def main():
    all_offers = []

    for region_id in REGION_IDS:
        print(f"\n Регион ID: {region_id}")
        for page in range(1, 100):
            print(f"Страница {page}")
            try:
                data = get_json(region_id, page)
                offers = data["data"].get("offersSerialized", [])
                if not offers:
                    print("Больше нет данных.")
                    break
                all_offers.extend(get_offer(item) for item in offers)
                time.sleep(1)
            except Exception as e:
                print(f"Ошибка на странице {page}: {e}")
                break

    print(f"\n Всего объявлений собрано: {len(all_offers)}")

    if all_offers:
        with open("irkutsk_region_offices_buy.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_offers[0].keys())
            writer.writeheader()
            writer.writerows(all_offers)
        print("Данные сохранены в irkutsk_region_offices_buy.csv")
    else:
        print("Не найдено объявлений по заданным регионам.")

if __name__ == "__main__":
    main()
