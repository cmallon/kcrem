from datetime import date, datetime
from io import BytesIO

import requests
from PIL import Image
from requests.auth import HTTPBasicAuth


def authenticate():
    url = "https://kcre.api.rentmanager.com"
    username = "integral"
    password = "SuiteA-301!11"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(
        url + "/authentication/AuthorizeUser/",
        headers=headers,
        json={"Username": username, "Password": password},
    )
    return str(response.json())


def delete_listing(slug):
    auth = HTTPBasicAuth("christopher.mallon@fishtanklearning.org", "178813Cm")
    get_url = "https://massvaluerentals.com/wp-json/wp/v2/listings?slug={}".format(slug)
    response = requests.get(get_url, auth=auth)
    if response.json() != []:
        url = "https://massvaluerentals.com/wp-json/wp/v2/listings/{}/".format(
            response.json()[0]["id"]
        )
        requests.delete(url, auth=auth)


def create_listing(listing_data):
    auth = HTTPBasicAuth("christopher.mallon@fishtanklearning.org", "178813Cm")
    get_url = "https://massvaluerentals.com/wp-json/wp/v2/listings?slug={}".format(
        listing_data["unit_name"]
    )
    response = requests.get(get_url, auth=auth)
    if response.json() == []:
        url = "https://massvaluerentals.com/wp-json/wp/v2/listings/"
    else:
        url = "https://massvaluerentals.com/wp-json/wp/v2/listings/{}/".format(
            response.json()[0]["id"]
        )
    price = 0
    if listing_data.get("price", 0):
        price = listing_data.get("price", 0)
    vacant = False
    move_out = True
    future_move_in = True
    if listing_data["is_vacant"]:
        vacant = str(listing_data.get("is_vacant", False))
    if (
        listing_data["expected_move_out"]
        and datetime.strptime(
            listing_data["expected_move_out"], "%Y-%m-%dT%H:%M:%S"
        ).date()
        > datetime.today().date()
    ):
        move_out = False
    if (
        listing_data["expected_move_in"]
        and datetime.strptime(
            listing_data["expected_move_in"], "%Y-%m-%dT%H:%M:%S"
        ).date()
        > datetime.today().date()
    ):
        future_move_in = False
    if vacant and move_out and future_move_in:
        wp_data = {
            "slug": listing_data["unit_name"],
            "title": listing_data["unit_name"],
            "content": listing_data["comment"],
            "status": "publish",
            "acf": {
                "square_footage": listing_data["square_footage"],
                "price": price,
                "unit_id": listing_data["unit_id"],
                "images": listing_data["images"],
                "property_name": listing_data["property_name"],
                "rental_type": listing_data["rental_type"],
                "is_vacant": str(listing_data.get("is_vacant", "False")),
                "expected_move_out": listing_data["expected_move_out"],
                "expected_move_in": listing_data["expected_move_in"],
                "address": listing_data["address"],
                "rooms": int(listing_data["rooms"]),
                "bathrooms": int(listing_data["bathrooms"]),
                "amenities": listing_data["amenities"],
                "storage_city": listing_data["storage_city"],
                "floor": listing_data["floor"],
            },
        }
        response = requests.post(url, auth=auth, json=wp_data)
    else:
        delete_listing(listing_data["unit_name"])


def get_media(url, id):
    response = requests.get(url)
    img = response.content
    auth = HTTPBasicAuth("christopher.mallon@fishtanklearning.org", "178813Cm")
    missing_url = "https://massvaluerentals.com/wp-json/wp/v2/media?search={}".format(
        id
    )
    response = requests.get(missing_url, auth=auth)
    if response.json() == []:
        post_url = "https://massvaluerentals.com/wp-json/wp/v2/media/"
    else:
        post_url = "https://massvaluerentals.com/wp-json/wp/v2/media/{}".format(
            response.json()[0]["id"]
        )
    response = requests.post(
        post_url,
        auth=auth,
        headers={
            "Content-Type": "image/png",
            "Content-Disposition": "attachment; filename={}.png".format(id),
        },
        data=img,
    )
    return response.json()


def parse_data(unit_data, type):
    for unit in unit_data:
        for value in unit["UserDefinedValues"]:
            if value["Name"] == "Include in Online Listings":
                include = False
                if value["Value"] == "Yes":
                    include = True

        comment = unit["Comment"]
        square_footage = unit["SquareFootage"]
        is_vacant = unit["IsVacant"]
        expected_move_out = unit["Leases"][-1]["MoveOutDate"]
        expected_move_in = unit["Leases"][-1]["MoveInDate"]
        city = unit["Addresses"][0]["City"]
        unit_id = unit["MarketingData"]["UnitID"]
        unit_name = unit["MarketingData"]["UnitName"]
        property_id = unit["MarketingData"]["PropertyID"]
        property_name = unit["Property"]["Name"]
        floor = None
        if unit["Floor"]:
            floor = unit["Floor"]["Name"]
        bedrooms = unit["Bedrooms"]
        bathrooms = unit["Bathrooms"]
        price = unit["MarketingData"].get("Price", 0)
        storage_city = unit["MarketingData"]["City"]
        images = []
        for image in unit["Images"]:
            if image.get("File", False):
                _id = image["File"]["FileID"]
                _url = image["File"]["DownloadURL"]
                media = get_media(_url, _id)
                images.append({"image": media["id"]})
        amenities = []
        for amenity in unit["Amenities"]:
            amenities.append({"amenity": str(amenity["Name"])})
        if include and not unit["CurrentUnitStatus"]:
            create_listing(
                {
                    "comment": comment,
                    "square_footage": square_footage,
                    "unit_id": unit_id,
                    "unit_name": unit_name,
                    "property_id": property_id,
                    "property_name": property_name,
                    "price": price,
                    "images": images,
                    "rental_type": type,
                    "is_vacant": is_vacant,
                    "expected_move_in": expected_move_in,
                    "expected_move_out": expected_move_out,
                    "address": city,
                    "rooms": bedrooms,
                    "bathrooms": bathrooms,
                    "amenities": amenities,
                    "floor": floor,
                    "storage_city": storage_city,
                }
            )
        else:
            delete_listing(unit_name)


def get_units(api_token, unit_type):
    try:
        url = "https://kcre.api.rentmanager.com"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-RM12Api-ApiToken": api_token,
        }
        response = requests.get(
            url
            + "/Units?embeds=Floor,Amenities,CurrentUnitStatus,CurrentOccupancyStatus,Property,Images,Images.File,IsVacant,Leases,MarketingData,UserDefinedValues,Addresses&filters=UnitTypeID,eq,{}&fields=Amenities,Property,Images,Leases,MarketingData,SquareFootage,UserDefinedValues,Comment,Addresses,Bedrooms,Bathrooms,CurrentUnitStatus,CurrentOccupancyStatus,Floor".format(
                unit_type
            ),
            headers=headers,
        )
        return response.json()
    except Exception as e:
        print(e)


def art_studios(api_token):
    parse_data(get_units(api_token, 1), "Art Studio")


def residential(api_token):
    parse_data(get_units(api_token, 7), "Residential")
    parse_data(get_units(api_token, 11), "Residential")
    parse_data(get_units(api_token, 13), "Residential")


def commercial(api_token):
    parse_data(get_units(api_token, 5), "Commercial")
    parse_data(get_units(api_token, 6), "Commercial")
    parse_data(get_units(api_token, 8), "Commercial")
    parse_data(get_units(api_token, 12), "Commercial")


def storage(api_token):
    parse_data(get_units(api_token, 9), "Storage")


api_token = authenticate()
residential(api_token)
art_studios(api_token)
commercial(api_token)
storage(api_token)
