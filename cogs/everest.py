"""Contains cog classes for any Everest interactions."""

import logging
from enum import Enum
from typing import TYPE_CHECKING, override

import discord

from utils import TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet
    from logging import Logger
    from typing import Final

    from utils import TeXBotApplicationContext, TeXBotAutocompleteContext

__all__: "Sequence[str]" = ("EverestCommandCog",)

logger: "Final[Logger]" = logging.getLogger("TeX-Bot")

MOUNT_EVEREST_TOTAL_STEPS: "Final[int]" = 44250


class _CourseTypes(Enum):
    B_SC = "B.Sc."
    M_SCI = "M.Sci."

    def get_course_year_weighting(self, course_year: int) -> float:
        """Calculate the grade weighting the given year has for this course type."""
        match (self, course_year):
            case _CourseTypes.B_SC, 1:
                return 0
            case _CourseTypes.M_SCI, 1:
                return 0
            case _CourseTypes.B_SC, 2:
                return 0.25
            case _CourseTypes.M_SCI, 2:
                return 0.2
            case _CourseTypes.B_SC, 3:
                return 0.75
            case _CourseTypes.M_SCI, 3:
                return 0.4
            case _CourseTypes.M_SCI, 4:
                return 0.4
            case _:
                INVALID_COURSE_YEAR_OR_TYPE_MESSAGE: Final[str] = (
                    f"Cannot calculate weighting for given course year ('{course_year}') "
                    f"and type ('{self}')."
                )
                raise ValueError(INVALID_COURSE_YEAR_OR_TYPE_MESSAGE)

    @override
    def __str__(self) -> str:
        return self.value


class EverestCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/everest" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_course_years(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[int] | AbstractSet[str]":
        """Autocomplete for the course year option."""
        try:
            selected_course_type: _CourseTypes | str = ctx.options["course-type"]
        except KeyError:
            return {1, 2, 3, 4}

        if not isinstance(selected_course_type, _CourseTypes):
            selected_course_type = selected_course_type.strip()

            if not selected_course_type:
                return {1, 2, 3, 4}

            try:
                selected_course_type = _CourseTypes[selected_course_type]
            except ValueError:
                return set()

        match selected_course_type:
            case _CourseTypes.B_SC:
                return {1, 2, 3}
            case _CourseTypes.M_SCI:
                return {1, 2, 3, 4}

    @discord.slash_command(
        name="everest", description="How many steps of everest is your assignment worth?"
    )
    @discord.option(
        name="course-type",
        description="The type of your university course.",
        input_type=str,
        choices=(  # NOTE: Display name is stored in the enum's value.
            discord.OptionChoice(name=course_type.value, value=course_type.name)
            for course_type in _CourseTypes
        ),
        required=True,
        parameter_name="raw_course_type",
    )
    @discord.option(
        name="course-year",
        description="The current year of your university course.",
        input_type=int,
        autocomplete=autocomplete_get_course_years,  # NOTE: Choices cannot be used for validation as they are static an preclude the ability to have dynamic autocomplete
        required=True,
        parameter_name="course_year",
    )
    @discord.option(
        name="percentage-of-module",
        description="The percentage of the module that the assignment is worth.",
        input_type=float,
        autocomplete=discord.utils.basic_autocomplete(  # NOTE: Pycord documents that they accept any iterable, testing shows that they only accept lists (generators do not work correctly).
            [
                discord.OptionChoice(name=f"{percentage * 5:.1f}%", value=percentage * 5)
                for percentage in range(1, 21)
            ]
        ),
        required=True,
        parameter_name="percentage_of_module",
    )
    async def everest(
        self,
        ctx: "TeXBotApplicationContext",
        raw_course_type: str,
        course_year: int,
        percentage_of_module: float,
    ) -> None:
        """Calculate how many steps of Mount Everest an assignment is worth."""
        try:
            course_type: _CourseTypes = _CourseTypes[raw_course_type]
        except KeyError:
            await self.command_send_error(
                ctx, message=f"Invalid course type: '{raw_course_type}'."
            )
            return

        if course_year < 1 or course_year > 10:
            await self.command_send_error(
                ctx, message=f"Invalid course year: '{course_year}'."
            )
            return

        if percentage_of_module < 0 or percentage_of_module > 100:
            await self.command_send_error(
                ctx,
                message=(
                    f"Percentage of module: '{percentage_of_module}' is not valid. "
                    "Please enter a percentage between 0 - 100."
                ),
            )
            return

        try:
            course_year_weighting: float = course_type.get_course_year_weighting(course_year)
        except KeyError:
            await self.command_send_error(
                ctx,
                message=(
                    f"Invalid course year ('{course_year}') for course type '{course_type}'."
                ),
            )
            return

        logger.debug("User %s used '/everest' command", ctx.user)

        await ctx.respond(
            content=(
                f"**Course**: {course_type}\n"
                f"**Year**: {course_year}\n"
                f"**Percentage of Module**: {percentage_of_module:.1f}%\n"
                f"This assignment is worth {  # NOTE: Assumes all modules are 20 credits
                    int(
                        (percentage_of_module / 100)
                        * (1 / 6)
                        * course_year_weighting
                        * MOUNT_EVEREST_TOTAL_STEPS
                    )
                } steps of Mt. Everest!"
            ),
            ephemeral=True,
        )
