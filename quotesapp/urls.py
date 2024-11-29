from django.urls import path
from . import views

urlpatterns = [
    path('author/<str:pk>/', AuthorDetailView.as_view(), name='author_detail'),
    path('quotes/', QuoteListView.as_view(), name='quote_list'),
]
