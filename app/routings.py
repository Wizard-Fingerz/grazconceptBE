from django.urls import re_path

from app.visa.pilgrimage.offer.consumers import PilgrimageVisaCommentConsumer
from app.visa.work.offers.consumers import WorkVisaCommentConsumer
from app.visa.study.consumers import StudyVisaCommentConsumer
from app.visa.vacation.offer.consumers import VacationVisaCommentConsumer  # <-- ADDED

websocket_urlpatterns = [
    re_path(r'ws/work/visa-application/(?P<application_id>\w+)/$', WorkVisaCommentConsumer.as_asgi()),
    re_path(r'ws/pilgrimage/visa-application/(?P<application_id>\w+)/$', PilgrimageVisaCommentConsumer.as_asgi()),
    re_path(r'ws/study/visa-application/(?P<application_id>\w+)/$', StudyVisaCommentConsumer.as_asgi()),
    re_path(r'ws/vacation/visa-application/(?P<application_id>\w+)/$', VacationVisaCommentConsumer.as_asgi()),  # <-- ADDED
]
