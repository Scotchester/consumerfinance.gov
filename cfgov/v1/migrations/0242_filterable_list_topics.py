# Generated by Django 3.2.18 on 2023-05-16 17:20

from django.db import migrations

from v1.util.migrations import migrate_page_types_and_fields


def migrate(apps, schema_editor):
    migrate_page_types_and_fields(
        apps,
        [
            ("v1", "BrowseFilterablePage", "content", "filter_controls"),
            ("v1", "SublandingFilterablePage", "content", "filter_controls"),
        ],
        migrate_filterable_list,
    )


def migrate_filterable_list(page_or_revision, data):
    data["topics"] = data.pop("topic_filtering", None) != "no_filter"
    return data


class Migration(migrations.Migration):
    dependencies = [
        ("v1", "0241_remove_filterable_5050"),
    ]

    operations = [
        migrations.RunPython(migrate, elidable=True),
    ]
