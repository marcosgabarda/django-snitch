class SnitchError(Exception):
    """Exception for snitch."""

    pass


class HandlerError(SnitchError):
    """An error configuring the event handler."""

    pass


class AlreadyRegistered(SnitchError):
    """Event handlers already register."""

    pass
