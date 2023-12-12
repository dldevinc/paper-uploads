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
        elif action is None or action == "Exit":
            ...
    """
    default = kwargs.pop("default")
    kwargs.setdefault("carousel", True)

    result = inquirer.prompt(
        [
            inquirer.List(
                "answer",
                message=message,
                choices=choices,
                default=default,
                **kwargs
            )
        ],
        render=CustomConsoleRender()
    )
    return result["answer"] if result is not None else None


def prompt_variants(message, choices, **kwargs):
    """
    Запрос от пользователя множества вариантов из заданного списка.

    Пример:
        actions = prompt_variants(
            message="What fruits do you like?",
            choices=["Apple", "Banana", ""]
        )

        if actions is None or "Exit" in actions:
            ...
        elif "Apple" in actions:
            ...
    """
    default = kwargs.pop("default")
    if isinstance(default, str):
        default = [default]

    kwargs.setdefault("carousel", True)

    while True:
        result = inquirer.prompt(
            [
                inquirer.Checkbox(
                    "answer",
                    message=message,
                    choices=choices,
                    default=default,
                    **kwargs
                )
            ],
            render=CustomConsoleRender()
        )

        if result is None:
            return None

        answer = result["answer"]
        if answer:
            return answer
