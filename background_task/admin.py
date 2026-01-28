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


class WorkerLockedByFilter(admin.SimpleListFilter):
    """
    Shows one dropdown where each entry is "worker - locked_by",
    ordered by worker first, then locked_by.
    """
    title = 'Worker / Locked By'
    parameter_name = 'worker_locked'

    def lookups(self, request, model_admin):
        """
        Build a list of (value, label) pairs for each distinct (worker, locked_by).
        We'll store them as something like 'worker|locked_by' so we can parse it later.
        """
        qs = model_admin.model.objects.all()
        # Distinct pairs of (worker, locked_by) ordered by worker, locked_by
        distinct_pairs = (
            qs.values_list('worker', 'locked_by')
              .distinct()
              .order_by('worker', 'locked_by')
        )

        lookups = []
        for worker, locked_by in distinct_pairs:
            # If you want to skip rows with both worker and locked_by == None, do:
            # if worker is None and locked_by is None:
            #     continue

            # Convert None to a string for the label if you want to show them
            str_worker = worker if worker is not None else "None"
            str_locked_by = locked_by if locked_by is not None else "None"

            label = f"{str_worker} - {str_locked_by}"
            value = f"{str_worker}|{str_locked_by}"
            lookups.append((value, label))

        return lookups

    def queryset(self, request, queryset):
        """
        When a user selects a choice, parse 'worker|locked_by' and filter accordingly.
        """
        if self.value():
            worker_val, locked_by_val = self.value().split('|')

            # Convert "None" back to None so the filter matches the database field
            worker_val = None if worker_val == "None" else worker_val
            locked_by_val = None if locked_by_val == "None" else locked_by_val

            return queryset.filter(worker=worker_val, locked_by=locked_by_val)
        return queryset


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
        WorkerLockedByFilter
        # ("run_at", DateTimeRangeFilter),
        # "locked_by",
        # "worker",
    ]
    list_display = [
        "task_name",
        "queue",
        "task_params",
        "run_at",
        "locked_at",
        "priority",
        # "attempts",
        "worker",
        "locked_by",
        # "locked_by_pid_running",
        # "has_error",
    ]
    actions = [inc_priority, dec_priority, "unlock_task", "run_now"]

    def unlock_task(self, request, queryset):
        if request.user.is_superuser:
            for task in queryset:
                task.locked_by = None
                task.locked_at = None
                task.worker = None
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
        "worker",
    ]
    list_filter = [
        "task_name",
        ScrapeStatusFilter,
        # ("run_at", DateTimeRangeFilter),
        "worker",
    ]
    actions = ["recreate_task"]

    def recreate_task(self, request, queryset):
        """
        Recreate selected completed tasks as new tasks in the Task table.
        The new tasks will be scheduled to run immediately with attempts reset.
        """
        recreated_count = 0
        for completed_task in queryset:
            # Create a new Task with the same parameters
            new_task = Task(
                task_name=completed_task.task_name,
                task_params=completed_task.task_params,
                task_hash=completed_task.task_hash,
                verbose_name=completed_task.verbose_name,
                priority=completed_task.priority,
                run_at=datetime.datetime.now(),  # Schedule to run immediately
                queue=completed_task.queue,
                repeat=completed_task.repeat,
                repeat_until=completed_task.repeat_until,
                creator=completed_task.creator,
                worker=completed_task.worker,
                # Reset attempt-related fields
                attempts=0,
                failed_at=None,
                last_error="",
                locked_by=None,
                locked_at=None,
            )
            new_task.save()
            recreated_count += 1

        self.message_user(
            request,
            f"Successfully recreated {recreated_count} task(s)."
        )

    recreate_task.short_description = "Recreate selected tasks"


admin.site.register(Task, TaskAdmin)
admin.site.register(CompletedTask, CompletedTaskAdmin)
