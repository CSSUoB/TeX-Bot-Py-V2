"""Contains cog classes for any Everest interactions."""

from enum import Enum
from typing import TYPE_CHECKING

import discord

from utils import TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from typing import Final, Literal

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext

__all__: "Sequence[str]" = ("EverestCommandCog",)


class CourseTypes(Enum):
    B_SC = "B.Sc."
    M_SCI = "M.Sci."

    def get_course_year_weighting(self, course_year: "Literal[1, 2, 3, 4]") -> float:
        match (self, course_year):
            case CourseTypes.B_SC, 1:
                return 0
            case CourseTypes.M_SCI, 1:
                return 0
            case CourseTypes.B_SC, 2:
                return 0.25
            case CourseTypes.M_SCI, 2:
                return 0.2
            case CourseTypes.B_SC, 3:
                return 0.75
            case CourseTypes.M_SCI, 3:
                return 0.4
            case CourseTypes.M_SCI, 4:
                return 0.4
            case _:
                INVALID_COURSE_YEAR_OR_TYPE_MESSAGE: Final[str] = (
                    f"Cannot calculate weighting for given course year ('{course_year}') "
                    f"and type ('{self}')."
                )
                raise ValueError(INVALID_COURSE_YEAR_OR_TYPE_MESSAGE)


class EverestCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/everest" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_course_years(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[int]":
        """Autocomplete for the course year option."""
        try:
            selected_course_type: CourseTypes | str = ctx.options["course-type"]
        except KeyError:
            return {1, 2, 3, 4}

        if not isinstance(selected_course_type, CourseTypes):
            try:
                selected_course_type = CourseTypes(selected_course_type.strip())
            except ValueError:
                return set()

        match selected_course_type:
            case CourseTypes.B_SC:
                return {1, 2, 3}
            case CourseTypes.M_SCI:
                return {1, 2, 3, 4}

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="everest", description="How many steps of everest is your assignment worth?"
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="course-type",
        description="The type of your university course.",
        input_type=CourseTypes,
        required=True,
        parameter_name="course_type",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="course-year",
        description="The current year of your university course.",
        input_type=int,
        choices=(1, 2, 3, 4),
        autocomplete=autocomplete_get_course_years,
        required=True,
        parameter_name="course_year",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="percentage-of-module",
        description="The percentage of the module that the assignment is worth.",
        input_type=float,
        required=True,
        parameter_name="percentage_of_module",
    )
    async def everest(  # type: ignore[misc]
        self,
        ctx: "TeXBotApplicationContext",
        course_type: CourseTypes,
        course_year: "Literal[1, 2, 3, 4]",
        percentage_of_module: float,
    ) -> None:
        """Calculate how many steps of Mount Everest an assignment is worth."""
        if percentage_of_module < 0 or percentage_of_module > 100:
            await self.command_send_error(
                ctx=ctx,
                message=(
                    f"Percentage of module: '{percentage_of_module}' is not valid. "
                    "Please enter a percentage between 0 - 100."
                ),
            )
            return

        try:
            course_year_weighting: float = course_type.get_course_year_weighting(course_year)
        except ValueError as e:
            await self.command_send_error(ctx, message=str(e))
            return
        await ctx.respond(
            content=(
                f"*Course*: {course_type}\n"
                f"*Year*: {course_year}\n"
                f"*Weighting*: {percentage_of_module}%\n"
                f"This assignment is worth {  # NOTE: Assumes all modules are 20 credits
                    int((percentage_of_module / 100) * (1 / 6) * course_year_weighting * 44250)
                } steps of Mt. Everest!"
            ),
            ephemeral=True,
        )
