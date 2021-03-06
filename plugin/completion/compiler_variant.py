"""Module contains options for various compiler variants

Attributes:
    log (logging.Logger): logger for this module
"""
import re
import logging

log = logging.getLogger(__name__)
log.debug(" reloading module")


class CompilerVariant(object):
    """
    Encapsulation of a compiler specific options
    """

    def errors_from_output(self, output):
        """
        Parse errors received from the compiler.

        Args:
            output (object): opaque output to be parsed by compiler variant

        Raises:
            NotImplementedError: Guarantees we do not call this abstract method
        """
        raise NotImplementedError("calling abstract method")


class ClangCompilerVariant(CompilerVariant):
    """
    Encapsulation of clang/clang++ specific options

    Attributes:
        init_flags (list): flags that every command needs
        error_regex (re): regex to find contents of an error
    """
    init_flags = ["-c", "-fsyntax-only", "-x c++"]
    error_regex = re.compile("(?P<file>.*)" +
                             ":(?P<row>\d+):(?P<col>\d+)" +
                             ":\s*.*error: (?P<error>.*)")

    def errors_from_output(self, output):
        """
        Parse errors received from clang binary output

        Args:
            view (sublime.View): current view
            clang_output (string): list of unparsed errors

        Returns:
            list(dict): a list of parsed errors
        """
        errors = []
        for line in output.splitlines():
            error_search = self.error_regex.search(line)
            if not error_search:
                continue
            error_dict = error_search.groupdict()
            errors.append(error_dict)
        return errors


class ClangClCompilerVariant(ClangCompilerVariant):
    """
    Encapsulation of clang-cl specific options

    Attributes:
        init_flags (list): flags that every command needs
        error_regex (re): regex to find contents of an error
    """
    init_flags = ["-c", "-fsyntax-only"]
    error_regex = re.compile("(?P<file>.*)" +
                             "\((?P<row>\d+),(?P<col>\d+)\)\s*" +
                             ":\s*.*error: (?P<error>.*)")


class LibClangCompilerVariant(CompilerVariant):
    """
    Encapsulation of libclang specific options

    Attributes:
        pos_regex (re): regex to find position of an error
        msg_regex (re): regex to find error message
    """
    pos_regex = re.compile("'(?P<file>.+)'.*" +  # file
                           "line\s(?P<row>\d+), " +  # row
                           "column\s(?P<col>\d+)")  # col
    msg_regex = re.compile('\"*(?P<error>.+)\"*')

    def errors_from_output(self, output):
        """Parse errors received from diagnostics of a translation unit (used
        with libclang)

        Args:
            output (diagnostics): diagnostics from a translation unit

        Returns:
            list(dict): a list of parsed errors
        """
        errors = []
        for diag in output:
            location = str(diag.location)
            spelling = str(diag.spelling)
            pos_search = self.pos_regex.search(location)
            msg_search = self.msg_regex.search(spelling)
            if not pos_search:
                # not valid, continue
                log.error("regex %s failed to match location: %s",
                          self.pos_regex.pattern, location)
                continue
            if not msg_search:
                # maybe there was no error word, so show everything there is
                log.error("regex %s failed to match error: %s",
                          self.msg_regex.pattern, spelling)
                continue
            error_dict = pos_search.groupdict()
            error_dict.update(msg_search.groupdict())
            errors.append(error_dict)
        return errors
