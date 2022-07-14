from datetime import datetime
from typing import List

from updater.logging import logger
from updater.updatable_item.abstract_updatable_item import AbstractUpdatableItem


def item_update_datetime_has_come(item: AbstractUpdatableItem,
                                  update_start_datetime: datetime
                                  ) -> bool:
    logger.debug(f"Check item update datetime has come {item.__class__.__name__}")

    need_update = False
    if item.get_last_update_datetime() is None:
        need_update = True
    else:
        item_next_update_datetime = item.get_next_update_datetime()
        if item_next_update_datetime is not None and \
                item_next_update_datetime <= update_start_datetime:
            need_update = True

    logger.debug(f"Item need update by datetime is {need_update}")
    return need_update


def get_dependencies_list(item: AbstractUpdatableItem) -> List[AbstractUpdatableItem]:
    logger.debug("Unpacked dependencies graph is requested")

    dependencies_list = []
    for dependency in item.get_dependencies():
        sub_dependencies = get_dependencies_list(dependency)
        for sub_item in sub_dependencies:
            if sub_item not in dependencies_list:
                dependencies_list.append(sub_item)
        dependencies_list.append(dependency)

    logger.debug(f"Dependency count of {item.__class__.__name__}: {len(dependencies_list)}")
    return dependencies_list


def is_item_dependencies_are_updated(item: AbstractUpdatableItem) -> bool:
    logger.debug(f"Check that item dependencies are updated for {item}")

    item_last_update_datetime = item.get_last_update_datetime()
    item_dependencies = get_dependencies_list(item)
    dependencies_updated = False
    for dependency in item_dependencies:
        if dependency.get_last_update_datetime() >= item_last_update_datetime:
            dependencies_updated = True
            break

    logger.debug(f"Item dependencies update status is {dependencies_updated}")
    return dependencies_updated


def is_need_update_item(item: AbstractUpdatableItem,
                        update_start_datetime: datetime
                        ) -> bool:
    logger.debug("Check need update item")

    need_update = False
    if item_update_datetime_has_come(item, update_start_datetime):
        need_update = True
    elif is_item_dependencies_are_updated(item):
        need_update = True

    logger.debug(f"Item need update status is {need_update}")
    return need_update


def calc_next_update_datetime(item: AbstractUpdatableItem) -> datetime:
    logger.debug("Requested next update datetime")
    next_update_datetime = None
    items_to_update_list = get_dependencies_list(item)
    items_to_update_list.append(item)
    for item in items_to_update_list:
        item_next_update_datetime = item.get_next_update_datetime()
        if next_update_datetime is None:
            next_update_datetime = item_next_update_datetime
        elif item_next_update_datetime is not None:
            next_update_datetime = min(next_update_datetime, item_next_update_datetime)
    logger.debug(f"Next update datetime is {next_update_datetime}")
    return next_update_datetime
