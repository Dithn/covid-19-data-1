import collections
import ast
from dataclasses import dataclass
import click

from cowidev.utils.slackapi import SlackAPI
from cowidev.utils.utils import get_traceback


def feedback_log(
    func,
    server,
    domain,
    step=None,
    text_success="",
    hide_success=False,
    channel="#corona-data-updates",
    **function_kwargs,
):
    if step is None:
        header = domain
    else:
        header = f"{domain} - [{step}]"
    try:
        func(**function_kwargs)
    except Exception as err:
        if server:
            StepReport(
                title=f"{header} step failed",
                trace=get_traceback(err),
                type="error",
            ).to_slack(channel)
        else:
            raise err
    else:
        if server and not hide_success:
            StepReport(
                title=f"{header} step ran successfully",
                text=text_success,
                type="success",
            ).to_slack(channel)


class OptionEatAll(click.Option):
    """From https://stackoverflow.com/a/48394004/5056599"""

    def __init__(self, *args, **kwargs):
        self.save_other_options = kwargs.pop("save_other_options", True)
        nargs = kwargs.pop("nargs", -1)
        assert nargs == -1, "nargs, if set, must be -1 not {}".format(nargs)
        super(OptionEatAll, self).__init__(*args, **kwargs)
        self._previous_parser_process = None
        self._eat_all_parser = None

    def add_to_parser(self, parser, ctx):
        def parser_process(value, state):
            # method to hook to the parser.process
            done = False
            value = [value]
            if self.save_other_options:
                # grab everything up to the next option
                print(state.rargs)
                while state.rargs and not done:
                    for prefix in self._eat_all_parser.prefixes:
                        if state.rargs[0].startswith(prefix):
                            done = True
                    if not done:
                        value.append(state.rargs.pop(0))
            else:
                # grab everything remaining
                value += state.rargs
                state.rargs[:] = []
            value = tuple(value)
            # call the actual process
            self._previous_parser_process(value, state)

        retval = super(OptionEatAll, self).add_to_parser(parser, ctx)
        for name in self.opts:
            our_parser = parser._long_opt.get(name) or parser._short_opt.get(name)

            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break

        return retval


class PythonLiteralOption(click.Option):
    """From https://stackoverflow.com/a/47730333/5056599"""

    def type_cast_value(self, ctx, value):
        if isinstance(value, (list, tuple)):
            return value
        if value is None:
            return []
        try:
            return ast.literal_eval(value)
        except:
            try:
                return value.split(",")
            except:
                raise click.BadParameter(value)


def normalize_country_name(country_name: str):
    return country_name.strip().replace("-", "_").replace(" ", "_").lower()


def _comma_separated_to_list(x):
    return [c for c in x.split(",")]


@dataclass
class Country2Module:
    modules_name: list
    country_to_module: list
    modules_name_incremental: list = None
    modules_name_batch: list = None

    def parse(self, countries):
        if isinstance(countries, str):
            countries = _comma_separated_to_list(countries)
        countries = [normalize_country_name(c) for c in countries]
        if len(countries) == 1:
            if countries[0].lower() == "all":
                return self.modules_name
            elif countries[0] == "incremental":
                return self.modules_name_incremental
            elif countries[0] == "batch":
                return self.modules_name_batch
        if len(countries) >= 1:
            # Verify validity of countries
            self._check_countries(countries)
            # Get module equivalent names
            modules = [self.country_to_module[country] for country in countries]
            return modules
        return []

    def _check_countries(self, countries):
        countries_wrong = [c for c in countries if c not in self.country_to_module]
        countries_valid = sorted(list(self.country_to_module.keys()))
        if countries_wrong:
            raise ValueError(f"Invalid countries: {countries_wrong}. Valid countries are: {countries_valid}")
            # raise ValueError("Invalid country")


class OrderedGroup(click.Group):
    """From https://stackoverflow.com/a/58323807/5056599"""

    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or collections.OrderedDict()

    def list_commands(self, ctx):
        return self.commands


class StepReport:
    def __init__(self, title: str, type: str, text: str = "", trace: str = ""):
        self.title = title
        self.text = text
        self.type = type
        self.trace = trace

    def __str__(self):
        return f"{self.type}: {self.text}"

    def to_slack(report, channel="#corona-data-updates"):
        client = SlackAPI()
        kwargs = {
            "channel": channel,
            "title": report.title,
            "message": report.text,
            "trace": report.trace,
        }
        if report.type == "error":
            client.send_error(**kwargs)
        elif report.type == "warning":
            client.send_warning(**kwargs)
        elif report.type == "success":
            client.send_success(**kwargs)
        else:
            raise ValueError(f"Unknown report status: {report.type}")
