from django.conf import settings
import redis, json

if settings.DATABASES["Redis"]["OPEN"]:
    conn_pool = redis.ConnectionPool(
        # host="127.0.0.1",
        host=settings.DATABASES["Redis"]["HOST"],
        # port=6379,
        port=int(settings.DATABASES["Redis"]["PORT"]),
        decode_responses=True,
    )
    RedisCache = redis.Redis(connection_pool=conn_pool, decode_responses=True)
    RedisCache.ping()
    print("connect redis success")

# 数据转换处理--------------------------------------------------------------------

# 定义一个key
def ShopDetailKey(id):
    return "shop_detail_%s" % id

# 写入数据内容到redis
# 字典 -> JSON
def SetShopDetail(id, detail):
    if settings.DATABASES["Redis"]["OPEN"]:
        key = ShopDetailKey(id)
        value = json.dumps(detail, ensure_ascii=False)
        RedisCache.set(key, value, ex=3600)

# 从redis获取数据内容
# JSON -> 字典
def GetShopDetail(id):
    if settings.DATABASES["Redis"]["OPEN"]:
        key = ShopDetailKey(id)
        detail = RedisCache.get(key)
        if detail is not None:
            return json.loads(detail)
        return None

# 删除redis数据
def DelShopDetail(id):
    if settings.DATABASES["Redis"]["OPEN"]:
        key = ShopDetailKey(id)
        RedisCache.delete(key)