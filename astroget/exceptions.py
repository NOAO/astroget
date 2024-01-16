import traceback


def genAstrogetException(response, verbose=False):
    """Given status from Server response.json(), which is a dict, generate
    a native exception suitable for Science programs."""

    content = response.content
    if verbose:
        print(f'Exception: response content={content}')
    status = response.json()

    # As of Python 3.10.0.alpha6, python "match" statement could be used
    # instead of if-elif-else.
    # https://docs.python.org/3.10/whatsnew/3.10.html#pep-634-structural-pattern-matching
    match status.get('errorCode'):
        case 'JOBACTIV':
            return JobActive(status.get('errorMessage'))
        case _:
            return UnknownServerError(
                f"{status.get('errorMessage')} "
                f"[{status.get('errorCode')}]")


class BaseClientException(Exception):
    """Base Class for all Astroget exceptions. """
    error_code = 'UNKNOWN'
    error_message = '<NA>'
    traceback = None

    def get_subclass_name(self):
        return self.__class__.__name__

    def __init__(self, error_message, error_code=None):
        Exception.__init__(self)
        self.error_message = error_message
        if error_code:
            self.error_code = error_code
        self.traceback = traceback.format_exc()

    def __str__(self):
        return f'[{self.error_code}] {self.error_message}'

    def to_dict(self):
        """Convert a Astroget exception to a python dictionary"""
        dd = dict(errorMessage=self.error_message,
                  errorCode=self.error_code)
        if self.traceback is not None:
            dd['traceback'] = self.traceback
        return dd




class JobActive(BaseClientException):
    """The job has not completed yet.  Cannot get results."""
    error_code = 'JOBACTIV'

class CannotPredict(BaseClientException):
    """The Server has not done enough work to make a reasonable prediction."""
    error_code = 'NOPRED'


class UnknownServerError(BaseClientException):
    """Client got a status response from the Astro Archive Server that we do not
    know how to decode."""
    error_code = 'UNKNOWN'

class UnknownAstroget(BaseClientException):
    """Unknown Astroget error.  If this is ever raised (seen in a log)
    create and use a new BaseSparcException exception that is more specific."""
    error_code = 'UNKAGET'


# error_code values should be no bigger than 8 characters 12345678
