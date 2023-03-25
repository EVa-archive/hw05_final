from django.contrib import admin

from .models import Group, Post, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    list_editable = ('group',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'email', 'post', 'created',)
    list_filter = ('created',)
    search_fields = ('author', 'text')


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment)
