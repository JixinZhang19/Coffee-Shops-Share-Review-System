from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import json, time, hashlib
from . import pymongo
from bson import binary
from bson.objectid import ObjectId
from . import pyredis


# 通用方法：返回json格式数据
def response(code: int, message: str, data: any = None):
    body = {"code": code, "message": message, "data": {}}
    if data is not None:
        if hasattr(data, "__dict__"):
            body["data"] = data.__dict__
        else:
            body["data"] = data
    return HttpResponse(json.dumps(body, sort_keys=True, ensure_ascii=False))


# 通用方法：在数组里找ID匹配的店铺数据
"""
shops_data = []
def findShopDataById(id):
    for l in shops_data:
        if l["id"] == id:
            return l
    return None
"""


# 通用方法：在数组里找ID匹配的评论数据，返回数组
"""
comments_data = []
def findCommentDataByShopId(id):
    coms =[]
    for l in comments_data:
        if l["shopID"] == id:
            coms.append(l)
    return coms
"""


# 获取店铺列表接口
@require_http_methods("GET")
def shopList(request):
    shops_data = []
    datas = pymongo.MongoDB.shops.find({}, {"_id": 1, "title": 1, "stars": 1, "desc": 1, "imgs": 1}).sort([("time", -1)]).limit(100)
    for data in datas:
        shops_data.append({
            "id": str(data["_id"]),
            "title": data["title"],
            "stars": data["stars"],
            "desc": data["desc"],
            "imgs": data["imgs"]
        })
    return response(0, "ok", shops_data)


# 获取店铺详情接口：输入参数为店铺唯一ID
@require_http_methods("GET")
def detail(request):
    id = request.GET.get("id", "")

    shop_data = {}
    # 先查找redis缓存：
    # 1.若缓存有数据，则直接返回内容
    # 2.否则读取数据库，若数据库有数据，则更新到缓存中，然后返回内容
    # 若有人评论，则删除缓存
    detail = pyredis.GetShopDetail(id)
    if detail is not None:
        print("find by redis")
        return response(0, "ok", detail)
    data = pymongo.MongoDB.shops.find_one({"_id": ObjectId(id)})
    # data = findShopDataById(id)
    if data is None:
        return response(1, "数据不存在")
    shop_data = {
        "id": str(data["_id"]),
        "user": data["user"],
        "title": data["title"],
        "stars": data["stars"],
        "desc": data["desc"],
        "lat": data["lat"],
        "lng": data["lng"],
        "address": data["address"],
        "comments": data["comments"],
        "time": data["time"],
        "imgs": data["imgs"]
    }
    pyredis.SetShopDetail(id, shop_data)
    print("find by mongodb")
    return response(0, "ok", shop_data)


# 获取某个店铺的评论列表，输入参数为店铺唯一ID
@require_http_methods("GET")
def commentList(request):
    shopID = request.GET.get("shopID", "")

    comments_data = []
    datas = pymongo.MongoDB.comments.find({"shopID": shopID}).sort([("time", -1)]).limit(5)
    for data in datas:
        comments_data.append({
            "id": str(data["_id"]),
            "shopID": data["shopID"],
            "user": data["user"],
            "stars": int(data["stars"]),
            "time": int(data["time"]),
            "desc": data["desc"]
        })
    # data = findCommentDataByShopId(id)
    return response(0, "ok", comments_data)


# 新增某个店铺的评论接口：输入参数为店铺唯一ID + 评论数据
# 使用post方法请求，输入数据结构为json
@require_http_methods("POST")
def commentAdd(request):
    if str(request.body, "utf-8") == "":
        return response(1, "参数不能为空")

    comment = {
        "shopID": "",
        "user": "",
        "stars": 0,
        "time": int(time.time()),
        "desc": ""
    }
    param = json.loads(request.body)

    if "shopID" not in param or param["shopID"] == "":
        return response(1, "参数shopID不能为空")
    comment["shopID"] = param["shopID"]

    shop = pymongo.MongoDB.shops.find_one({"_id": ObjectId(param["shopID"])})
    if shop is None:
        return response((1, "店铺不存在"))

    if "user" not in param or param["user"] == "":
        return response(1, "参数user不能为空")
    comment["user"] = param["user"]

    if "stars" not in param:
        return response(1, "参数stars不能为空")
    comment["stars"] = param["stars"]

    if "desc" not in param or param["desc"] == "":
        return response(1, "参数desc不能为空")
    comment["desc"] = param["desc"]

    # comments_data.append(comment)
    pymongo.MongoDB.comments.insert_one(comment)

    avgStars = int((shop["stars"] * shop["comments"] + comment["stars"]) / (shop["comments"] + 1))
    pymongo.MongoDB.shops.update_one({"_id": ObjectId(param["shopID"])}, {"$inc": {"comments": 1}, "$set": {"stars": avgStars}})

    pyredis.DelShopDetail(param["shopID"])
    return response(0, "ok")


# 图片上传接口
# {"_id": ObjectId("mongo的唯一ID"), "md5":" 唯一标识", "type": "类型", "body": "图片二进制内容" }
# 临时全局图片变量，数据结构为：dict => {picID: {type: pic_type, body: pic_body}}
# pics = {}
@require_http_methods("POST")
def upload(request):
    f = request.FILES["file"]

    body = f.read()
    md5 = hashlib.md5(body).hexdigest()
    typ = f.content_type
    data = {"md5": md5, "type": typ, "body": binary.Binary(body)}

    # 查询数据库中是否已有同样的图片
    img = pymongo.MongoDB.images.find_one({"md5": md5})
    if img is not None:
        print("find md5 image")
        return response(0, "ok", {"id": str(img["_id"])})

    # 插入一条数据
    ret = pymongo.MongoDB.images.insert_one(data)
    print("insert image")
    return response(0, "ok", {"id": str(ret.inserted_id)})
"""
    fileName = "{}{}".format(f.name, time.time())
    hFileName = hashlib.md5(fileName.encode("utf-8")).hexdigest()
    pics[hFileName] = {"type": f.content_type, "body": f.read()}
    return response(0, "ok", {"id": hFileName})
"""


# 图片获取接口
@require_http_methods("GET")
def file(request):
    id = request.GET.get("id", "")

    img = pymongo.MongoDB.images.find_one({"_id": ObjectId(id)})
    if img is None:
        return response(100, "图片不存在")
    return HttpResponse(img["body"], img["type"])
"""
    if id not in pics:
        return response(100, "图片不存在")
    return HttpResponse(pics[id]["body"], pics[id]["type"])
"""


# 新增店铺接口
@require_http_methods("POST")
def shopAdd(request):
    if str(request.body, "utf-8") == "":
        return response(1, "参数不能为空")

    shop = {
        # "id": "",
        "title": "",
        "user": "",
        "stars": 0,
        "desc": "",
        "lat": 0,
        "lng": 0,
        "address": "",
        "comments": 0,
        "time": int(time.time()), # 服务器端时间戳
        "imgs": []
    }
    param = json.loads(request.body)

    if "title" not in param or param["title"] == "":
        return response(1, "参数title不能为空")
    shop["title"] = param["title"]

    # 生成id
    # titleName = "{}{}".format(param["title"], time.time())
    # shop["id"] = hashlib.md5(titleName.encode("utf-8")).hexdigest()

    if "user" not in param or param["user"] == "":
        return response(1, "参数user不能为空")
    shop["user"] = param["user"]

    if "stars" not in param:
        return response(1, "参数stars不能为空")
    shop["stars"] = param["stars"]

    if "desc" not in param or param["desc"] == "":
        return response(1, "参数desc不能为空")
    shop["desc"] = param["desc"]

    if "lat" not in param or "lng" not in param:
        return response(1, "参数latlng不能为空")
    shop["lat"] = param["lat"]
    shop["lng"] = param["lng"]

    if "address" not in param or param["address"] == "":
        return response(1, "参数address不能为空")
    shop["address"] = param["address"]

    if "imgs" not in param:
        return response(1, "参数imgs不能为空")
    shop["imgs"] = param["imgs"]

    # shops_data.append(shop)
    pymongo.MongoDB.shops.insert_one(shop)
    return response(0, "ok")