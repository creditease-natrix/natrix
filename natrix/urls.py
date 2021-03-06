"""eagle URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^natrix/benchmark/', include('benchmark.urls')),
    url(r'^natrix/sentinel/', include('sentinel.urls')),
    url(r'^natrix/rbac/', include('rbac.urls')),
    url(r'^natrix/terminal/', include('terminal.urls')),
    url(r'^v2/$', TemplateView.as_view(template_name="index.html"), name=u'natrix_vue'),
    url(r'^natrix/accounts/', admin.site.urls),
    url(r'^natrix/admin/', admin.site.urls),
    url(r'^$', TemplateView.as_view(template_name="index.html"), name=u'natrix_index'),
]

urlpatterns += static(settings.STATIC_URL,
                      document_root=settings.STATIC_ROOT)
