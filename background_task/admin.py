# -*- coding: utf-8 -*-
import datetime

from django.contrib import admin
from background_task.models import Task
from background_task.models import CompletedTask
from rangefilter.filters import DateTimeRangeFilter
from django.contrib.admin import SimpleListFilter
from django.db.models import Q


class ScrapeStatusFilter(SimpleListFilter):
    title = "Completion Status"  # a label for our filter
    parameter_name = "status"  # you can put anything here

    def lookups(self, request, model_admin):
        # This is where you create filter options; we have two:
        return [
            ("failed", "Failed"),
            ("completed_successfully", "Completed Successfully"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "failed":
            return queryset.distinct().filter(~Q(last_error=""))
        elif self.value() == "completed_successfully":
            return queryset.distinct().filter(last_error="")
        return queryset.distinct()


def inc_priority(modeladmin, request, queryset):
    for obj in queryset:
        obj.priority += 1
        obj.save()


inc_priority.short_description = "priority += 1"


def dec_priority(modeladmin, request, queryset):
    for obj in queryset:
        obj.priority -= 1
        obj.save()


dec_priority.short_description = "priority -= 1"


class TaskAdmin(admin.ModelAdmin):
    display_filter = ["task_name"]
    search_fields = ["task_name", "task_params"]
    list_filter = [
        "task_name",
        # ("run_at", DateTimeRangeFilter),
    ]
    list_display = [
        "task_name",
        "task_params",
        "run_at",
        "priority",
        "attempts",
        "has_error",
        "locked_by",
        "locked_by_pid_running",
    ]
    actions = [inc_priority, dec_priority, "unlock_task", "run_now"]

    def unlock_task(self, request, queryset):
        if request.user.is_superuser:
            for task in queryset:
                task.locked_by = None
                task.locked_at = None
                task.save()

    unlock_task.short_description = "Unlock Selected Tasks"

    def run_now(self, request, queryset):
        if request.user.is_superuser:
            for task in queryset:
                task.run_at = datetime.datetime.now()
                task.save()

    run_now.short_description = "Run Selected Tasks Now"


class CompletedTaskAdmin(admin.ModelAdmin):
    display_filter = ["task_name"]
    search_fields = ["task_name", "task_params"]
    list_display = [
        "task_name",
        "task_params",
        "run_at",
        "priority",
        "attempts",
        "has_error",
        "locked_by",
        "locked_by_pid_running",
    ]
    list_filter = [
        "task_name",
        ScrapeStatusFilter,
        # ("run_at", DateTimeRangeFilter),
    ]


admin.site.register(Task, TaskAdmin)
admin.site.register(CompletedTask, CompletedTaskAdmin)
