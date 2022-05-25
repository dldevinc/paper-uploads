import sys

import inquirer
import inquirer.themes as themes
from inquirer.render.console import ConsoleRender


class GreenPassion(themes.GreenPassion):
    def __init__(self):
        super().__init__()
        self.Checkbox.selection_icon = "⇨"
        self.Checkbox.selection_color = themes.term.bright_green
        self.Checkbox.selected_icon = "☑"
        self.Checkbox.selected_color = themes.term.bright_green
        self.Checkbox.unselected_icon = "☐"
        self.Checkbox.unselected_color = themes.term.normal
        self.List.selection_cursor = self.Checkbox.selection_icon
        self.List.selection_color = self.Checkbox.selection_color
        self.List.unselected_color = self.Checkbox.unselected_color


class CustomConsoleRender(ConsoleRender):
    def __init__(self, event_generator=None, theme=None, *args, **kwargs):
        theme = theme or GreenPassion()
        super().__init__(event_generator, theme, *args, **kwargs)

    @property
    def width(self):
        return 240

    def _print_header(self, render):
        base = render.get_header()

        header = base[: self.width - 9] + "..." if len(base) > self.width - 6 else base
        default_value = " ({color}{default}{normal})".format(
            default=render.question.default, color=self._theme.Question.default_color, normal=self.terminal.normal
        )
        show_default = render.question.default and render.show_default
        header += default_value if show_default else ""
        msg_template = (
            "{t.clear_eos}{tq.brackets_color}[{tq.mark_color}?{tq.brackets_color}]{t.normal} {msg}"
        )

        self.print_str(
            msg_template,
            msg=header,
            lf=not render.title_inline,
            tq=self._theme.Question,
        )

    def print_str(self, base, lf=False, **kwargs):
        message = base.format(t=self.terminal, **kwargs)

        if lf:
            self._position += message.count("\n") + 1

        print(message, end="\n" if lf else "")
        sys.stdout.flush()


def prompt_action(message, choices, **kwargs):
    """
    Запрос действия от пользователя из заданного списка.

    Пример:
        action = prompt_action(
            message="What do you want to do?",
            choices=["Run script", "Exit"]
        )

        if action == "Run script":
            ...
        elif action == "Exit":
            ...
    """
    kwargs.setdefault("carousel", True)
    return inquirer.prompt(
        [
            inquirer.List(
                "answer",
                message=message,
                choices=choices,
                **kwargs
            )
        ],
        render=CustomConsoleRender()
    )["answer"]


def prompt_variants(message, choices, **kwargs):
    """
    Запрос от пользователя множества вариантов из заданного списка.

    Пример:
        action = prompt_variants(
            message="What fruits do you like?",
            choices=["Apple", "Banana", ""]
        )

        if action == "Run script":
            ...
        elif action == "Exit":
            ...
    """
    kwargs.setdefault("carousel", True)
    return inquirer.prompt(
        [
            inquirer.Checkbox(
                "answer",
                message=message,
                choices=choices,
                **kwargs
            )
        ],
        render=CustomConsoleRender()
    )["answer"]
