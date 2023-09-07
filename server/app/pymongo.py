from django.conf import settings
from pymongo import MongoClient

client = MongoClient(
    # host="127.0.0.1",
    host=settings.DATABASES["MongoDB"]["HOST"],
    # port=27017
    port=int(settings.DATABASES["MongoDB"]["PORT"]),
)

# MongoDB = client["yelpcafe"]
MongoDB = client[settings.DATABASES["MongoDB"]["NAME"]]
MongoDB.command("ping")

print("connect mongodb success")