from django.contrib import admin
from .models import Author, Quote, Tag


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'born_date', 'born_location', 'description')


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('quote', 'author', 'tags_display')

    # Show tags in the list of quotes
    def tags_display(self, obj):
        return ', '.join(tag.name for tag in obj.tags)
    tags_display.short_description = 'Tags'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
