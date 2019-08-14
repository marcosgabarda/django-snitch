class HandlerError(Exception):
    """An error configuring the event handler."""

    pass


class AlreadyRegistered(Exception):
    """Event handlers already register."""

    pass
