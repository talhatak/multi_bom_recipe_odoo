# Multi BOM Recipe

Multi BOM Recipe is an Odoo 18 addon for managing channel-specific recipes from one central master recipe. It is designed for restaurant and delivery workflows where the same sellable product can require different component quantities depending on the sales channel, floor, or delivery type.

The module creates and maintains generated phantom Bills of Materials for each configured sales channel, then uses those BoMs in POS, Blink delivery, stock, and accounting flows.

## Features

- Create a central **Master Recipe** for a sellable product.
- Define common recipe components once and reuse them across every selected sales channel.
- Select one or more restaurant floors/sales channels directly on the master recipe.
- Add extra channel-specific components through sales channel lines when a channel needs additional or different quantities.
- Automatically generate one phantom BoM per selected sales channel.
- Link generated BoMs back to the master recipe for tracking and maintenance.
- Merge duplicate component products into a single generated BoM line.
- View generated BoMs directly from the master recipe smart button.
- Use generated channel BoMs in POS stock move explosion based on the POS table floor.
- Use generated channel BoMs for Blink sale orders based on the Blink order type.
- Recalculate POS Anglo-Saxon COGS from the actual stock valuation of generated component moves.
- Sync master recipes and generated BoMs to child branch companies through server actions.

## Dependencies

This addon depends on the following Odoo modules:

- `mrp`
- `sale_mrp`
- `stock_account`
- `point_of_sale`
- `uom`
- `optp_ext`
- `blink_integration`

The module also uses restaurant floors as sales channels through the `restaurant.floor` model.

## Main Models

### Master Recipe

Model: `master.recipe`

This is the central recipe record. It contains:

- `name`: recipe name.
- `product_id`: sellable product template for which BoMs will be generated.
- `company_id`: company that owns the recipe.
- `recipe_channel_ids`: Many2many selection of restaurant floors/sales channels where this recipe should exist.
- `main_component_lines`: common components used by every generated channel BoM.
- `sales_channel_ids`: optional channel-specific component lines.
- `bom_counts`: count of generated BoMs linked to the recipe.

### Main Component

Model: `main.component`

Stores the shared recipe components. Each line contains:

- component product
- component quantity
- unit of measure

These components are included in every generated sales-channel BoM for the recipe.

### Sales Channel Configuration

Model: `sales.config.channel`

This model is extended with `master_recipe_id` so existing channel configuration lines can also belong to a master recipe. These lines are used for additional channel-specific components.

## How It Works

1. Create a master recipe for a product.
2. Select the sales channels/floors in the **Sales Channels** field.
3. Add shared ingredients/components in the **Main Components** tab.
4. Optionally add channel-specific component lines in the **Sales Channels** tab.
5. When the recipe is created or updated, the module synchronizes generated BoMs.
6. For each selected channel, the module creates one generated phantom BoM.
7. Each generated BoM contains the shared components plus any extra components configured for that specific channel.

Generated BoMs are marked with:

- `master_recipe_id`
- `sales_channel_id`
- `is_master_recipe_bom = True`
- `type = phantom`
- code format: `MR-{recipe_id}-{channel_id}`

## Component Quantity Logic

The generated BoM lines are built from two sources:

- Main component lines on the master recipe.
- Matching sales channel component lines for the same channel.

If the same component product appears more than once, quantities are added together and one BoM line is generated for that product.

Main component quantities are converted from their selected unit of measure into the component product's default unit of measure before being written to the generated BoM.

## POS Working

For POS orders, the module chooses the correct generated BoM from the POS table floor.

When a POS stock move is exploded:

- the module checks the picking's linked POS order;
- reads the table floor from the POS order;
- finds the generated master recipe BoM for that product and floor;
- explodes the phantom BoM into component stock moves.

This lets each restaurant floor or POS sales channel consume the correct recipe components.

## Blink Delivery Working

For Blink sale orders, procurement uses the Blink order type to locate the generated channel BoM.

When procurement runs:

- the module checks whether the sale order is a Blink order;
- reads the sale order `order_type`;
- finds the generated master recipe BoM matching that product and order type;
- explodes the phantom BoM into component procurements.

If no matching generated BoM is found, the standard phantom BoM lookup is used.

## POS COGS Working

The module adjusts POS invoice COGS calculation for Anglo-Saxon accounting.

Instead of costing only the sold parent product, it reads the completed picking moves and uses the stock valuation layers created from the actual component moves. This helps POS invoices reflect the real component cost from the BoM used for the order.

## Branch / Company Sync

The module provides server actions to sync recipes and BoMs to child branch companies.

Available actions:

- **Sync Master Recipe to All Branches** on `master.recipe`.
- **Sync BoM to All Branches** on `mrp.bom`.

When syncing a generated master recipe BoM, the module syncs the full master recipe to child companies. The child company recipe then creates its own generated BoMs using the same master-recipe logic.

The sync copies:

- recipe name
- product
- selected sales channels/floors
- main component lines
- channel-specific component lines

The sync targets leaf child companies under the same root company.

## User Interface

The module adds a **Master Recipes** menu under Point of Sale product configuration.

The master recipe form includes:

- recipe details
- selected sales channels/floors
- main components tab
- channel-specific component tab
- BoM smart button to open generated BoMs

The module also extends the BoM list and form views to show the linked sales channel.

## Typical Use Case

A restaurant sells the same menu item through multiple channels, but each channel may need different packaging or component quantities.

For example:

- Dine-in uses the food ingredients only.
- Delivery uses the food ingredients plus packaging.
- Pickup uses the food ingredients plus a different bag or container.

With this module, the user creates one master recipe, selects all relevant channels, and adds packaging only on the channel-specific lines. The module then generates the correct phantom BoM for each channel automatically.

## Installation

1. Copy the `multi_bom_recipe` folder into your Odoo extra addons path.
2. Restart Odoo.
3. Update the Apps list.
4. Install **Multi BOM Recipe**.

For existing installations, upgrade the module after pulling changes:

```bash
odoo -d <database_name> -u multi_bom_recipe --stop-after-init
```

## Technical Notes

- Generated BoMs are maintained automatically on master recipe create, update, and delete.
- Generated BoMs are deleted when their master recipe is deleted.
- A channel selected only in `recipe_channel_ids` is enough to create a BoM; a channel-specific line is optional.
- Context key `no_sync` is used internally to avoid recursive BoM synchronization.
- The module keeps the older `sales.config.channel.bom_id` relationship available for compatibility with existing customizations.

## License

LGPL-3
