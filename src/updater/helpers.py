from datetime import datetime
from typing import List

from updater.update_keychain import UpdateKeychain


def have_item_update_datetime_been_come(item: UpdateKeychain, update_start_datetime: datetime) -> bool:
    need_update = False
    if item.get_last_update_datetime() is None:
        need_update = True
    else:
        item_next_update_datetime = item.get_next_update_datetime()
        if item_next_update_datetime is not None and \
                item_next_update_datetime <= update_start_datetime:
            need_update = True
    return need_update


def get_dependencies_list(item: UpdateKeychain) -> List[UpdateKeychain]:
    dependencies_list = []
    for dependency in item.get_dependencies():
        sub_dependencies = get_dependencies_list(dependency)
        for sub_item in sub_dependencies:
            if sub_item not in dependencies_list:
                dependencies_list.append(sub_item)
        dependencies_list.append(dependency)
    return dependencies_list


def have_item_dependencies_been_update(item: UpdateKeychain) -> bool:
    item_last_update_datetime = item.get_last_update_datetime()
    dependencies_updated = False
    for dependency in get_dependencies_list(item):
        if dependency.get_last_update_datetime() > item_last_update_datetime:
            dependencies_updated = True
            break
    return dependencies_updated


def is_need_update_item(item: UpdateKeychain, update_start_datetime: datetime) -> bool:
    need_update = False
    if have_item_update_datetime_been_come(item, update_start_datetime):
        need_update = True
    elif have_item_dependencies_been_update(item):
        need_update = True
    return need_update


def calc_next_update_datetime(item: UpdateKeychain) -> datetime:
    next_update_datetime = None
    items_to_update_list = get_dependencies_list(item)
    items_to_update_list.append(item)
    for item in items_to_update_list:
        item_next_update_datetime = item.get_next_update_datetime()
        if next_update_datetime is None:
            next_update_datetime = item_next_update_datetime
        elif item_next_update_datetime is not None:
            next_update_datetime = min(next_update_datetime, item_next_update_datetime)
    return next_update_datetime
