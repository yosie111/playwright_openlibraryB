async def get_bookshelf_status(item) -> int:
    """
    Returns the active bookshelf id:
    1 = Want to Read
    2 = Currently Reading
    3 = Already Read

    Returns -1 if no active bookshelf was found.
    """
    
    forms = await item.query_selector_all("form.reading-log.primary-action")

    for form in forms:
        action_input = await form.query_selector("input[name='action']")
        shelf_input = await form.query_selector("input[name='bookshelf_id']")

        if not action_input or not shelf_input:
            continue

        value_action = await action_input.get_attribute("value")
        value_bookshelf_id = await shelf_input.get_attribute("value")

        if value_action == "remove" and value_bookshelf_id:
            shelf_id = int(value_bookshelf_id)
            
            if shelf_id in (1, 2, 3):
                return shelf_id
    return -1