"""Contains cog classes for any everest interactions."""

import random
from typing import TYPE_CHECKING

import discord

from config import settings
from utils import TeXBotBaseCog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from utils import TeXBotApplicationContext

__all__: "Sequence[str]" = ("EverestCommandCog",)


class EverestCommandCog(TeXBotBaseCog):
    """Cog class that defines the "/everest" command and its call-back method."""

    @staticmethod
    async def autocomplete_get_course_types(
        ctx: "TeXBotAutocompleteContext",
    ) -> "AbstractSet[discord.OptionChoice] | AbstractSet[str]":
        raise NotImplementedError  # TODO(Donian960)

    @discord.slash_command(description="How many steps of everest is your assignment worth?")
    @app_commands.describe(
        course="What course are you on (bsc or msci)",
        year="Current year of the course (1 to 4)",
        value="What % of a module is the assignment worth"
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="course",
        description="Your type of university course: B.Sc. or M.Sci.",
        input_type=...,  # TODO(Donian960): Make type into a limited set of choices
        autocomplete=discord.utils.basic_autocomplete(autocomplete_get_course_types),  # type: ignore[arg-type]
        required=True,
        parameter_name="course_type",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="year",
        description="Current year of the course (1 to 4).",
        input_type=...,  # TODO(Donian960): Make type into a limited set of choices
        required=True,
        parameter_name="current_course_year",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="module_percentage",
        description="The percentage of a module that the assignment worth.",
        input_type=float,  # TODO(Donian960): limit values to between 0% & 100%
        required=True,
    )
    async def everest(self, ctx: "TeXBotApplicationContext", course_type: ..., current_course_year: int, module_percentage: float):  # TODO(Donian960): Choose correct type for 'course_type' variable
        message_start = "Course: " + str(course) + ", Year: " + str(year) + ", Value: " +str(value) + "%\n" # message data

        course = course.lower() # allowing capital courses

        if course != "bsc" and course != "msci": # weeding out fake courses
            message = message_start + "That's not a real course :(" # preparing to tell the user to go away
            await interaction.response.send_message(message) # telling the user to go away
        else: # if the course is real
            failure = False # it hasn't failed yet

            try: # seeing if it will fail in a safe way
                year = int(year) # checking the year is an int
                value = float(value) # checking the % is valid
            except: # if they aren't
                failure = True # it's failed
                message = message_start + "Invalid data type :(" # preparing to tell the user to go away
                await interaction.response.send_message(message) # telling the user to go away

            if failure == False: # if it didn't fail
                if year < 1 or (year > 3 and course == "bsc") or (year > 4 and course == "msci"): # checking they are on a real year
                    message = message_start + "Invalid year :(" # preparing to tell the user to go away
                    await interaction.response.send_message(message) # telling the user to go away

                else: # if they're on a real year
                    if course == "bsc": # this
                        if year == 1: # is
                            year_value = 0 # just
                        elif year == 2: # a
                            year_value = 0.25 # longer
                        else: # way
                            year_value = 0.75 # to
                    if course == "msci": # do
                        if year == 1: # a
                            year_value = 0 # dictionary
                        elif year == 2: # but
                            year_value = 0.2 # too
                        else: # bad
                            year_value = 0.4 # how much is each year worth

                    steps = (value / 100) * 1 / 6 * year_value * 44250 # actually calculating the steps of everest (assumes modules are worth 20 / 120 credits)

                    message = message_start + "This assignment is worth " + str(int(steps)) + " steps of Mt. Everest!" # preparing to tell the user how much they walked
                    await interaction.response.send_message(message) # telling the user how much they walked
