from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Raffle, RaffleComment, Draw, Winner


class WinnerInline(admin.TabularInline):
    model = Winner
    extra = 0
    readonly_fields = ("position", "is_alternate", "username", "comment_text", "ig_comment_id", "commented_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class DrawInline(admin.StackedInline):
    model = Draw
    extra = 0
    readonly_fields = ("round", "valid_entries", "participants_hash", "rules_snapshot", "random_source", "reason", "created_at")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Raffle)
class RaffleAdmin(admin.ModelAdmin):
    list_display = ("short_uuid", "user", "status", "loaded_comments", "winners_count", "created_at", "certificate_link")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "ig_media_id", "uuid")
    readonly_fields = (
        "uuid", "user", "ig_media_id", "permalink", "caption", "thumbnail_url",
        "media_type", "posted_at", "comments_count", "status",
        "loaded_comments", "load_started_at", "load_finished_at", "load_error",
        "created_at", "drawn_at",
    )
    inlines = [DrawInline]

    @admin.display(description="UUID")
    def short_uuid(self, obj):
        return str(obj.uuid)[:8]

    @admin.display(description="Certificado")
    def certificate_link(self, obj):
        if obj.status == Raffle.STATUS_DRAWN:
            url = f"/r/{obj.uuid}/"
            return format_html('<a href="{}" target="_blank">Ver</a>', url)
        return "—"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(RaffleComment)
class RaffleCommentAdmin(admin.ModelAdmin):
    list_display = ("raffle", "username", "text_preview", "commented_at", "is_reply")
    list_filter = ("is_reply", "raffle")
    search_fields = ("username", "text", "ig_comment_id")
    readonly_fields = ("raffle", "ig_comment_id", "username", "text", "commented_at", "is_reply", "parent_ig_id")

    @admin.display(description="Comentário")
    def text_preview(self, obj):
        return obj.text[:80]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    list_display = ("raffle", "round", "valid_entries", "created_at", "reason")
    list_filter = ("created_at",)
    readonly_fields = ("raffle", "round", "valid_entries", "participants_hash", "rules_snapshot", "random_source", "reason", "created_at")
    inlines = [WinnerInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Winner)
class WinnerAdmin(admin.ModelAdmin):
    list_display = ("draw", "position", "username", "is_alternate", "commented_at")
    list_filter = ("is_alternate",)
    search_fields = ("username",)
    readonly_fields = ("draw", "position", "is_alternate", "username", "comment_text", "ig_comment_id", "commented_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
