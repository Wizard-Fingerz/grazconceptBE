from django.urls import path, include
from rest_framework.routers import DefaultRouter

from definition.views import TableDropDownDefinitionViewSet

router = DefaultRouter()
router.register(r'definitions', TableDropDownDefinitionViewSet, basename='definition')

urlpatterns = [

    # path('redoc/', name='schema-redoc'),

]

urlpatterns += router.urls