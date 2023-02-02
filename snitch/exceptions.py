class SnitchError(Exception):
    """Exception for snitch."""


class HandlerError(SnitchError):
    """An error configuring the event handler."""


class AlreadyRegistered(SnitchError):
    """Event handlers already register."""
