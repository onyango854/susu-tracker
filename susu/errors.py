class SusuError(Exception):
    """Base class for every rule violation raised by the susu domain."""

class InvalidAmountError(SusuError): pass
class UnknownMemberError(SusuError): pass
class DuplicateMemberError(SusuError): pass
class OverpaymentError(SusuError): pass
class GroupStateError(SusuError): pass
