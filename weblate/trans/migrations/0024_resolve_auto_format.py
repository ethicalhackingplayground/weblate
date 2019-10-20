# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-27 13:27
from __future__ import unicode_literals

import os.path

from django.conf import settings
from django.db import migrations

from weblate.formats.auto import AutodetectFormat


def get_path(component):
    if component.linked_component:
        return get_path(component.linked_component)
    return os.path.join(
        settings.DATA_DIR, "vcs", component.project.slug, component.slug
    )


def update_format(component, store):
    component.file_format = store.format_id
    component.save(update_fields=["file_format"])


def resolve_auto_format(apps, schema_editor):
    Component = apps.get_model("trans", "Component")
    db_alias = schema_editor.connection.alias
    for component in Component.objects.using(db_alias).filter(file_format="auto"):
        path = get_path(component)
        template = None
        if component.template:
            template = AutodetectFormat.parse(os.path.join(path, component.template))
        try:
            translation = component.translation_set.all()[0]
        except IndexError:
            if template is None and component.new_base:
                template = AutodetectFormat.parse(
                    os.path.join(path, component.new_base)
                )
            if template is not None:
                update_format(component, template)
                continue
            raise Exception(
                "Existing translation component with auto format and "
                "without any translations, can not detect file format. "
                "Please edit the format manually and rerun migration. "
                "Affected component: {}/{}".format(
                    component.project.slug, component.slug
                )
            )
        store = AutodetectFormat.parse(
            os.path.join(path, translation.filename), template
        )
        update_format(component, store)


class Migration(migrations.Migration):

    dependencies = [("trans", "0023_auto_20190325_1037")]

    operations = [
        migrations.RunPython(
            resolve_auto_format, migrations.RunPython.noop, elidable=True
        )
    ]
