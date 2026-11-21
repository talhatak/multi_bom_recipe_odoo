# Multi BOM Recipe

An Odoo 19 addon for managing sales-channel-specific recipes from one master recipe view. Sales channels are standard Odoo restaurant floors.

## Features

- Define shared ingredients once and add extra components for individual channels.
- Select floors directly, even when they need no extra components.
- Automatically generate and maintain one phantom (kit) BoM per recipe/channel.
- Merge duplicate component products and convert common-component quantities to the product's default unit of measure.
- Open generated BoMs from the recipe's smart button.
- Select the correct recipe from the POS table floor or the Sales Order's **Sales Channel** field.
- Calculate POS invoice COGS from completed component stock move values using Odoo 19 inventory accounting.

## Dependencies

Only official Odoo addons are required: `mrp`, `sale_mrp`, `stock_account`, `point_of_sale`, `pos_restaurant`, `uom`, and `mail`.

## Installation

1. Place `multi_bom_recipe` in your Odoo addons path.
2. Restart Odoo, update the Apps list, and install **Multi BOM Recipe**.
3. Configure restaurant floors in Point of Sale. Manufacturing users can manage recipes; sales and manufacturing users have read access to the floor selector.

## Recipe setup

Open **Point of Sale > Products > Master Recipes** with a user who has Manufacturing access.

1. Set the recipe name, sellable product, and company.
2. Select the restaurant floors in **Sales Channels**.
3. Add common ingredients in **Main Components**, with their quantity and unit of measure.
4. Add optional extras in **Channel Components**. Quantities here use the component's default unit of measure, displayed on each line.
5. Save. Each selected floor gets its own generated BoM containing common ingredients plus its extras.

A floor used on a channel component line also generates a BoM, even if it is not selected in the header. Remove both references to stop generating that channel's BoM. Recipe and component records are restricted to the user's allowed companies.

For example, a burger recipe can share ingredients across Dine-in and Delivery, with packaging added only to Delivery.

## POS orders

The channel comes from `pos.order.table_id.floor_id`. Each order is linked to its picking before stock moves are created. Session-closing batches are separated by order so orders on different floors use their own recipes. Standard Odoo handles move quantities, lots, refunds, stock valuation, and dates.

## Sales Orders

Set **Sales Channel** on the quotation to the restaurant floor representing that channel, then confirm the order. Procurement uses that floor's generated BoM in the order's company. Quantity increases use the same channel when calculating additional requirements. Standard Odoo handles kit delivery quantities and returns.

The channel cannot change after confirmation. Cancel and reset the order to draft before changing it; existing completed stock operations are not rewritten.

If no channel is selected, or no matching generated BoM exists, an ordinary non-channel BoM is used. Generated channel BoMs never become an arbitrary fallback for another channel. Floors are matched by record ID, so duplicate floor names cannot select the wrong recipe.

Common-component units must share a reference unit with the product unit. Odoo 19 uses reference-unit relationships instead of UoM categories.

## Models and implementation

- `master.recipe`: product, company, selected floors, common components, and channel components.
- `main.component`: shared ingredient, quantity, and unit of measure.
- `master.recipe.channel.line`: this addon's own channel/component model.
- `mrp.bom`: linked recipe, restaurant floor, and generated-BoM flag.
- `sale.order.sales_channel_id`: optional restaurant-floor selector.

`recipe_sales_channel_id` is passed through procurement values and scoped context to select BoMs. Stock and procurement extensions delegate kit processing to standard Odoo rather than copying its implementation.

Generated BoMs are maintained by the recipe; edit ingredient definitions in the recipe view. Existing synchronization replaces generated BoM lines when recipes change. Validate recipe changes against outstanding stock operations before using them in a live database.

## Validation

On a clean Odoo 19 database, install using only the dependencies above. Check shared ingredients, per-channel extras, duplicate components and UoM conversion; POS orders on different floors (including session closing and refunds); Sales Orders with different floors, quantity increases, delivery quantities and returns; unmatched-floor fallback; multi-company isolation; and POS invoice component move valuation/COGS.

## License

LGPL-3. See [LICENSE](LICENSE).
