"""Contains cog classes for MSL Sales Report interactions."""

from collections.abc import Sequence

__all__: Sequence[str] = ("SalesDataCommandsCog",)


import logging
from logging import Logger
from typing import Final

import discord

from utils import MSL, CommandChecks, TeXBotApplicationContext, TeXBotBaseCog

logger: Final[Logger] = logging.getLogger("TeX-Bot")


class SalesDataCommandsCog(TeXBotBaseCog):
    """Cog class for MSL Sales Report interactions."""

    @discord.slash_command(  # type: ignore[no-untyped-call, misc]
        name="get-sales-reports",
        description="Returns the sales reports on the guild website.",
    )
    @discord.option(  # type: ignore[no-untyped-call, misc]
        name="product_id",
        description="The product ID to get the sales report for.",
        required=True,
        input_type=str,
        parameter_name="product_id",
    )
    @CommandChecks.check_interaction_user_has_committee_role
    @CommandChecks.check_interaction_user_in_main_guild
    async def update_sales_report(self, ctx: TeXBotApplicationContext, product_id: str) -> None:  # noqa: E501
        """Command to get the sales reports on the guild website."""
        initial_response: discord.Interaction | discord.WebhookMessage = await ctx.respond(
            content="Fetching sales reports...",
        )

        sales_report_object: MSL.MSLSalesReports = MSL.MSLSalesReports()

        product_sales: dict[str, int] = await sales_report_object.get_product_sales("10000610")

        if not product_sales:
            await initial_response.edit(
                content=f"No sales data found for product ID: {product_id}.",
            )
            return

        sales_report_message: str = (
            "Found sales data for product ID: 10000610:\n"
            + "\n".join(
                f"{date} - {quantity}"
                for date, quantity in product_sales.items()
            )
        )

        await ctx.respond(content=sales_report_message)

