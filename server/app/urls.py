from django.urls import path
from . import apps

# /api/{app.urls}
urlpatterns = [
    path('shopList', apps.shopList, name='shopList'),
    path('detail', apps.detail, name='detail'),
    path('commentList', apps.commentList, name='commentList'),
    path('comment/add', apps.commentAdd, name='commentAdd'),
    path('upload', apps.upload, name='upload'),
    path('file', apps.file, name='file'),
    path('shop/add', apps.shopAdd, name='shopAdd'),
]