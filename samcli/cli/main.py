"""
Entry point for the CLI
"""

import logging
import json
import click

from samcli import __version__
from .options import debug_option, region_option, profile_option
from .context import Context
from .command import BaseCommand

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

pass_context = click.make_pass_decorator(Context)
from click import HelpFormatter, wrap_text
from click._compat import term_len
from colorama import init
from termcolor import colored

init()

message_cyan = lambda x: colored(x, 'cyan', attrs=['blink'])


def write_usage(self, prog, args='', prefix='Usage: '):
    """Writes a usage line into the buffer.

    :param prog: the program name.
    :param args: whitespace separated list of arguments.
    :param prefix: the prefix for the first line.
    """
    usage_prefix = message_cyan('%*s%s ' % (self.current_indent, prefix, prog))
    text_width = self.width - self.current_indent

    if text_width >= (term_len(usage_prefix) + 20):
        # The arguments will fit to the right of the prefix.
        indent = ' ' * term_len(usage_prefix)
        self.write(wrap_text(args, text_width,
                             initial_indent=usage_prefix,
                             subsequent_indent=indent))
    else:
        # The prefix is too long, put the arguments on the next line.
        self.write(usage_prefix)
        self.write('\n')
        indent = ' ' * (max(self.current_indent, term_len(prefix)) + 4)
        self.write(wrap_text(args, text_width,
                             initial_indent=indent,
                             subsequent_indent=indent))


def write_text(self, text):
    """Writes re-indented text into the buffer.  This rewraps and
          preserves paragraphs.
    """
    self.write(text)
    self.write('\n')


def color(self, message):
    message = message_cyan(message)
    self.buffer.append('%*s%s:\n' % (self.current_indent, '', message))


HelpFormatter.write_heading = color
HelpFormatter.write_usage = write_usage
HelpFormatter.write_text = write_text


def docstring(message=""):
    """
    Decorator: Append to a function's docstring.
    """

    def _decorator(func):
        text = colored(message, 'red', attrs=['blink'])
        func.__doc__ = text
        return func

    return _decorator


def common_options(f):
    """
    Common CLI options used by all commands. Ex: --debug
    :param f: Callback function passed by Click
    :return: Callback function
    """
    f = debug_option(f)
    return f


def aws_creds_options(f):
    """
    Common CLI options necessary to interact with AWS services
    """
    f = region_option(f)
    f = profile_option(f)
    return f


def print_info(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return

    click.echo(json.dumps({
        "version": __version__
    }, indent=2))

    ctx.exit()


@click.command(cls=BaseCommand)
@common_options
@click.version_option(version=__version__, prog_name="SAM CLI")
@click.option("--info", is_flag=True, is_eager=True, callback=print_info, expose_value=False)
@pass_context
@docstring(r"""
 🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
🔥  _________   _____      _____            _________ .____    .___      🔥
🔥 /   _____/  /  _  \    /     \           \_   ___ \|    |   |   |     🔥
🔥 \_____  \  /  /_\  \  /  \ /  \   ______ /    \  \/|    |   |   |     🔥
🔥 /        \/    |    \/    Y    \ /_____/ \     \___|    |___|   |     🔥
🔥/_______  /\____|__  /\____|__  /          \______  /_______ \___|     🔥
🔥        \/         \/         \/                  \/        \/         🔥
 🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥

""")
def cli(ctx):
    """
    AWS Serverless Application Model (SAM) CLI

    The AWS Serverless Application Model extends AWS CloudFormation to provide a simplified way of defining the
    Amazon API Gateway APIs, AWS Lambda functions, and Amazon DynamoDB tables needed by your serverless application.
    You can find more in-depth guide about the SAM specification here:
    https://github.com/awslabs/serverless-application-model.
    """
    pass
