"""Contains cog classes for any everest interactions."""

from typing import TYPE_CHECKING

import discord

from utils import TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from typing import Final

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext

__all__: "Sequence[str]" = ("EverestCommandCog",)


POSSIBLE_COURSE_TYPES: "Final[AbstractSet[str]]" = {"B.Sc.", "M.Sci."}
POSSIBLE_YEARS: "Final[AbstractSet[int]]" = {1, 2, 3, 4}

BSC_WEIGHTINGS: "Final[list[float]]" = [0, 0.25, 0.75]
MSCI_WEIGHTINGS: "Final[list[float]]" = [0, 0.2, 0.4, 0.4]


class EverestCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/everest" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_course_types(
        ctx: "TeXBotAutocompleteContext",  # noqa: ARG004
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        """Autocomplete for the course type option."""
        return POSSIBLE_COURSE_TYPES

    @staticmethod
    async def autocomplete_get_course_years(
        ctx: "TeXBotAutocompleteContext",  # noqa: ARG004
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[int]":
        """Autocomplete for the course year option."""
        return POSSIBLE_YEARS

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="everest", description="How many steps of everest is your assignment worth?"
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="course-type",
        description="Your type of university course: B.Sc. or M.Sci.",
        input_type=str,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_course_types),  # type: ignore[arg-type]
        required=True,
        parameter_name="course_type",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="year",
        description="Current year of the course (1 to 4).",
        input_type=int,
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_course_years),  # type: ignore[arg-type]
        required=True,
        parameter_name="current_course_year",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="module_percentage",
        description="The percentage of a module that the assignment worth.",
        input_type=float,
        required=True,
    )
    async def everest(  # type: ignore[misc]
        self,
        ctx: "TeXBotApplicationContext",
        course_type: str,
        current_course_year: int,
        module_percentage: float,
    ) -> None:
        """Calculate how many steps of Mount Everest an assignment is worth."""
        if course_type not in POSSIBLE_COURSE_TYPES:
            await ctx.respond(
                content=(
                    f"{course_type} is not a valid course type. Please use the autocomplete."
                )
            )
            return

        INVALID_COURSE_YEAR_MESSAGE: Final[str] = (
            f"Course year: {current_course_year} is not valid. Please use the autocomplete."
        )

        try:
            current_course_year = int(current_course_year)
        except ValueError:
            await ctx.respond(content=INVALID_COURSE_YEAR_MESSAGE)
            return

        if current_course_year not in POSSIBLE_YEARS:
            await ctx.respond(content=INVALID_COURSE_YEAR_MESSAGE)
            return

        INVALID_MODULE_WEIGHT_MESSAGE: Final[str] = (
            f"Module weight: {module_percentage} is not valid."
            "Please enter a positive number less than or equal to 100."
        )
        try:
            module_weight = float(module_percentage)
        except ValueError:
            await ctx.respond(content=INVALID_MODULE_WEIGHT_MESSAGE)
            return

        if module_weight < 0 or module_weight > 100:
            await ctx.respond(content=INVALID_MODULE_WEIGHT_MESSAGE)
            return

        if current_course_year == 4 and course_type == "B.Sc.":
            await ctx.respond(
                content=(
                    "You have selected 4th year of a B.Sc. course, which is not valid."
                    "If you are in final year, please select 3rd year."
                )
            )
            return

        year_value: float = 0

        if course_type == "B.Sc.":
            year_value = BSC_WEIGHTINGS[current_course_year - 1]
        if course_type == "msci":
            year_value = MSCI_WEIGHTINGS[current_course_year - 1]

        steps = (
            (module_weight / 100) * 1 / 6 * year_value * 44250
        )  # NOTE: Assumes all modules are 20 credits

        await ctx.respond(
            content=(
                f"Course: {course_type}, "
                f"Year: {current_course_year}, "
                f"Weight: {module_percentage}%\n"
                f"This assignment is worth {int(steps)} steps of Mt. Everest!"
            )
        )
