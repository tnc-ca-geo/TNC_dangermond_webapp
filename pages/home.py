import dash
from dash import html
import datetime
import io
import requests
import dash
from datetime import date as dt, timedelta
import plotly.express as px
import pandas as pd
import time
from datetime import date
from dash import (
    Dash,
    html,
    dcc,
    Input,
    Output,
    callback,
    State,
    Patch,
    no_update,
    dash_table,
    ctx,
)

from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import Flask
import numpy as np
import os
import boto3
import io
import xarray as xr
import logging

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from figures import figures_main
import data_loader

log = logging.getLogger(__name__)
dash.register_page(__name__, path="/")


BUCKET_NAME = os.environ.get('BUCKET_NAME') or 'tnc-dangermond'


# note, boto3 will ignore this if local aws credentials exist
s3 = boto3.resource(
    "s3",
    aws_access_key_id=os.getenv("aws_access_key_id"),
    aws_secret_access_key=os.getenv("aws_secret_access_key"),
)

data = data_loader.DataLoader(s3_resource=s3, bucket_name=BUCKET_NAME)
# data = data_loader.DataLoader(local_data_dir="./data") # local mode

# list of catchments in the ngen output data
cats = data.ds_ngen["catchment"].to_pandas().to_list()

# figs that load with the layout
fig = go.Figure()
precip_bar_fig = figures_main.precip_bar_fig(data)
summary_data_fig = figures_main.annual_mean(data)


layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        dcc.Loading(
                            parent_className="loading_wrapper",
                            children=[
                                dcc.Store(id="cat-click-store"),
                                # shows selected reach
                                html.Div(id="contents", hidden=True),
                                dbc.Label("Model Formulation:"),
                                dbc.Checklist(
                                    options=[
                                        {
                                            "label": (
                                                "CFE - Groundwater Calibration"
                                            ),
                                            "value": 1,
                                            # "disabled": "True",
                                        },
                                        # {
                                        #     "label": "CFE - Streamflow Calibration",
                                        #     "value": 2,
                                        #     "disabled": "True",
                                        # },
                                    ],
                                    value=[1],
                                    id="switches-input",
                                    switch=True,
                                    style={
                                        "padding": "0rem 1.5rem 0rem 1.5rem",
                                        # "color": "pink",
                                    },
                                ),
                                dbc.Label("Select year and month:"),
                                dcc.Dropdown(
                                    id="year-dropdown",
                                    options=[
                                        {"label": str(year), "value": year}
                                        for year in range(1983, 2024)
                                    ],
                                    value=2008,  # default value is the current year
                                    placeholder="Select a year",
                                    className="mb-1",
                                    clearable=False,
                                ),
                                # Dropdown for selecting month
                                dcc.Dropdown(
                                    id="month-dropdown",
                                    options=[
                                        {"label": "January", "value": 1},
                                        {"label": "February", "value": 2},
                                        {"label": "March", "value": 3},
                                        {"label": "April", "value": 4},
                                        {"label": "May", "value": 5},
                                        {"label": "June", "value": 6},
                                        {"label": "July", "value": 7},
                                        {"label": "August", "value": 8},
                                        {"label": "September", "value": 9},
                                        {"label": "October", "value": 10},
                                        {"label": "November", "value": 11},
                                        {"label": "December", "value": 12},
                                    ],
                                    value=1,  # default value is the current month
                                    placeholder="Select a month",
                                    clearable=False,
                                ),
                                html.Div(
                                    [
                                        # html.Br(),
                                        dbc.Label("Select output variable:"),
                                        dcc.Dropdown(
                                            id="variable-dropdown",
                                            options=[
                                                {"label": col, "value": col}
                                                for col in [
                                                    # "SOIL_STORAGE",
                                                    "Potential ET",
                                                    "Actual ET",
                                                    "Streamflow",
                                                    "Groundwater Storage",
                                                    "Precipitation",
                                                ]
                                            ],
                                            value="Streamflow",  # Default value
                                        ),
                                    ],
                                    # className="custom-control custom-switch",
                                    # style={"padding": "1.5rem 1.5rem 1.5rem 1.5rem"},
                                ),
                                html.Br(),
                                html.Div("Full Domain Statistics:"),
                                html.Div(
                                    id="comparison-table-container",
                                    children=[
                                        dbc.Table(
                                            html.Tbody(
                                                [
                                                    html.Tr(
                                                        [
                                                            html.Td("Month"),
                                                            html.Td(""),
                                                        ]
                                                    ),  # Blank cell for month
                                                    html.Tr(
                                                        [
                                                            html.Td(
                                                                "Selected Volume (m³)"
                                                            ),
                                                            html.Td(""),
                                                        ]
                                                    ),  # Blank cell for selected volume
                                                    html.Tr(
                                                        [
                                                            html.Td(
                                                                "Avg Volume (m³)"
                                                            ),
                                                            html.Td(""),
                                                        ]
                                                    ),  # Blank cell for average volume
                                                    html.Tr(
                                                        [
                                                            html.Td(
                                                                "% of Avg"
                                                            ),
                                                            html.Td(""),
                                                        ]
                                                    ),  # Blank cell for % of avg
                                                ]
                                            ),
                                            bordered=True,  # Add table borders
                                            hover=True,  # Enable hover effect
                                            striped=True,  # Stripe the rows
                                            responsive=True,  # Make table responsive
                                            size="sm",  # Small size for a more compact look
                                            # style={
                                            #     "border-radius": "5px",  # Rounded corners
                                            #     "overflow": "hidden",  # Ensure borders and rounding apply smoothly
                                            # },
                                        )
                                    ],
                                ),
                                # html.Br(),
                                html.Div(
                                    [
                                        dbc.Label("Data Summary:"),
                                        dcc.Markdown(
                                            id="summary-text",
                                            children="Loading data...",
                                            style={
                                                "padding": "0.5rem",
                                                # "font-size": "14px",
                                            },
                                        ),
                                    ]
                                ),
                                html.Div(
                                    [
                                        dbc.Button(
                                            "Download Data",
                                            color="primary",
                                            disabled=True,
                                            id="download-data-button",
                                        ),
                                        dcc.Download(
                                            id="download-dataframe-csv"
                                        ),
                                    ],
                                    className="d-grid gap-2",
                                    # style={"padding": "1.5rem 0 1.5rem 1.5rem 1.5rem"},
                                ),
                                html.Br(),
                                dcc.Store(id="selected-date-store"),
                            ],
                            style={
                                "height": "100vh",
                                "overflow-y": (
                                    "auto"
                                ),  # Ensures entire sidebar is scrollable
                                "padding": (
                                    "10px"
                                ),  # Prevents unexpected spacing issues
                            },
                        ),
                    ),
                    # html.Div(id="coords", style={"display": "none"}),
                    lg=3,
                    className="ml-3 mt-0",
                ),
                dbc.Col(
                    html.Div(
                        [
                            dbc.Tabs(
                                id="right-column-tabs",
                                active_tab="tab-1",
                                children=[
                                    dbc.Tab(
                                        label="Map View",
                                        tab_id="tab-1",
                                        children=[
                                            dcc.Loading(
                                                id="loading-spinner-map",
                                                delay_show=100,
                                                type="default",
                                                children=[
                                                    dcc.Graph(
                                                        id="choropleth-map",
                                                        style={
                                                            "height": "40vh"
                                                        },
                                                        config={
                                                            "displaylogo": (
                                                                False
                                                            ),
                                                            "scrollZoom": True,
                                                        },
                                                    ),
                                                ],
                                            ),
                                            dcc.Loading(
                                                id="loading-spinner-wb_ts",
                                                delay_show=100,
                                                type="default",
                                                children=[
                                                    dcc.Graph(
                                                        id="wb_ts_fig",
                                                        style={
                                                            "height": "40vh"
                                                        },
                                                        config={
                                                            "displaylogo": (
                                                                False
                                                            )
                                                        },
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dbc.Tab(
                                        label="1982 - 2023 Water Balance Summary",
                                        tab_id="tab-2",
                                        children=[
                                            dcc.Loading(
                                                id="loading-spinner-precip-bar",
                                                delay_show=100,
                                                type="default",
                                                children=[
                                                    dcc.Graph(
                                                        figure=precip_bar_fig,
                                                        style={
                                                            "height": "70vh"
                                                        },
                                                        config={
                                                            "displaylogo": (
                                                                False
                                                            )
                                                        },
                                                    ),
                                                ],
                                            ),
                                            dcc.Loading(
                                                id="loading-spinner-summary-fig",
                                                delay_show=100,
                                                type="default",
                                                children=[
                                                    dcc.Graph(
                                                        figure=summary_data_fig,
                                                        style={
                                                            "height": "50vh"
                                                        },
                                                        config={
                                                            "displaylogo": (
                                                                False
                                                            )
                                                        },
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            # DBC Modal
                            dbc.Modal(
                                [
                                    dbc.ModalHeader(
                                        dbc.ModalTitle(id="well-name-title")
                                    ),
                                    dbc.ModalBody(
                                        dcc.Loading(
                                            id="loading-spinner-model",
                                            delay_show=100,
                                            type="default",
                                            children=[
                                                dcc.Graph(
                                                    id="modal-figure",
                                                    figure=fig,
                                                )  # Include the figure inside the modal
                                            ],
                                        )
                                    ),
                                    dbc.ModalBody(html.P(id="modal-content")),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Close",
                                            id="close-modal",
                                            className="ml-auto",
                                            n_clicks=0,
                                        )
                                    ),
                                ],
                                id="modal",
                                size="xl",
                                is_open=False,  # Initially closed
                            ),
                        ],
                        style={
                            # "overflow-y": "scroll",  # Enables vertical scrolling
                            "height": "auto",
                            "box-shadow": (
                                "-4px -4px 10px 6px rgba(0, 0, 0, 0.1)"
                            ),
                            "border-top-left-radius": (
                                "10px"
                            ),  # Rounded top left corner
                            "border-top-right-radius": (
                                "10px"
                            ),  # Rounded top right corner
                        },
                    ),
                    style={
                        # "backgroundColor": "#cccccc",
                        # "border-radius": "5px",
                        # "overflow-x": "hidden",
                    },  # dbc.Col style
                    class_name="mr-3",
                ),
            ],
        )
    ]
)


# # Callbacks ----------------
@callback(Output("contents", "children"), Input("choropleth-map", "clickData"))
def update_contents(click_data):
    """
    get click data from primary map, add to layout.
    """
    if click_data:
        layer = click_data["points"][0]["curveNumber"]
        if layer == 0:
            # print("clicked")
            # print(click_data)
            id = click_data["points"][0]["customdata"][0]
            # dff = df[df["centroid_lat"] == fips]
    else:
        id = 1

    return html.Div(
        [
            # dash_table.DataTable(
            #     id="table",
            #     columns=[{"name": i, "id": i} for i in dff.columns],
            #     data=dff.to_dict(orient="records"),
            # )
            1
        ]
    )


@callback(
    [
        # Output("output-date", "children"),
        Output("selected-date-store", "data"),
    ],  # Store the selected date
    [Input("year-dropdown", "value"), Input("month-dropdown", "value")],
)
def date_from_year_month(year, month):
    """ """
    if year and month:
        selected_date = datetime.date(year, month, 1).strftime("%Y-%m-%d")
        return [selected_date]
    return None


# Callback to update map based on selected column
@callback(
    Output("choropleth-map", "figure"),
    Input("variable-dropdown", "value"),
    Input("selected-date-store", "data"),
)
def mapbox_lines(display_var, time_click):
    """
    Primary map with flowpaths within Dangermond Preserve.
    """
    print(display_var)
    print(time_click)

    return figures_main.mapbox_lines(
        gdf=data.gdf,
        gdf_outline=data.gdf_outline,
        display_var=display_var,
        ds=data.ds_ngen,
        gdf_wells=data.gdf_wells,
        gdf_lines=data.gdf_lines,
        time=time_click,
        cfe_routed_flow_af=data.cfe_routed_flow_af,
    )


# Callback to handle click event and show/hide modal
@callback(
    Output("modal", "is_open"),
    [Input("choropleth-map", "clickData"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(click_data, n_clicks, is_open):
    # check if click_data or None
    if click_data:
        layer = click_data["points"][0]["curveNumber"]

        # set True if well location points have been clicked
        if (layer == 3) and not is_open:
            return True

    # If the close button is clicked, close the modal
    if n_clicks and is_open:
        return False

    return is_open  # Keep modal state unchanged if no click event


# Callback to update modal content based on click_data
@callback(
    Output("well-name-title", "children"),
    Input("choropleth-map", "clickData"),
)
def update_modal_content(click_data):
    if click_data:
        # print(f"{click_data=}")
        layer = click_data["points"][0]["curveNumber"]
        if layer == 3:
            well_name = click_data["points"][0]["hovertext"]
            stn_id = click_data["points"][0]["customdata"]
            cat = data.gdf_wells[
                data.gdf_wells["station_id_dendra"] == stn_id
            ]["divide_id"].values[0]
            return f"Groundwater Comparison: {well_name} & catchment '{cat}'"
    return ""


# Callback to update modal content based on clickData (optional if dynamic)
@callback(
    [Output("modal-figure", "figure"), Output("modal-content", "children")],
    Input("choropleth-map", "clickData"),
    prevent_initial_call=True,
)
def update_modal_figure(click_data):
    """Update modal fig with comparison of CFE groundwater elevation and observed well level,
    and display any warning messages in the modal."""
    warnings = []  # List to collect warning messages

    if click_data:
        layer = click_data["points"][0]["curveNumber"]
        if layer == 3:
            print(f"well click: {click_data}")
            stn_id = click_data["points"][0]["customdata"]
            print(f"{stn_id=}")
            cat = data.gdf_wells[
                data.gdf_wells["station_id_dendra"] == stn_id
            ]["divide_id"].values[0]
            print(f"{cat=}")
            default_index = data.ds_ngen.Time.values

            # Precip forcing for catchment
            try:
                ppt_aorc = (
                    data.ds_ngen["RAIN_RATE_INCHES"]
                    .sel({"catchment": cat})
                    .to_pandas()
                )
            except Exception as _:
                warning = "Precipitation forcing not avilable for catchment."
                warnings.append(warning)
                print(warning)
                ppt_aorc = pd.Series(dtype=float, index=default_index)

            # Cumulative CFE elevation change for catchment
            try:
                cfe_elev_series = (
                    data.ds_ngen["NET_GW_CHANGE_FEET"]
                    .sel({"catchment": cat})
                    .cumsum()
                    .to_pandas()
                )
            except Exception as _:
                warning = "Simulated water elevation change not available for catchment."
                warnings.append(warning)
                print(warning)
                cfe_elev_series = pd.Series(dtype=float, index=default_index)

            # Observation data for catchment
            try:
                well_obs_series = data.well_data[stn_id]
                first = well_obs_series.first_valid_index()
                well_obs_series -= well_obs_series[first]
            except Exception as _:
                warning = "Observed water level data not found for catchment."
                warnings.append(warning)
                print(warning)
                well_obs_series = pd.Series(dtype=float, index=default_index)

            if len(well_obs_series) < 1:
                well_obs_series = [0]

            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.02,
            )

            fig.add_trace(
                go.Scatter(
                    x=cfe_elev_series.index,
                    y=cfe_elev_series,
                    mode="lines",
                    name="CFE Simulated Groundwater Elevation Change",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=well_obs_series.index,
                    y=well_obs_series,
                    mode="lines",
                    name="Observed Groundwater Level Change",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=ppt_aorc.index,
                    y=ppt_aorc,
                    mode="lines",
                    name="Precipitation Forcing (inches)",
                ),
                row=2,
                col=1,
            )

            fig.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5,
                ),
                margin=dict(l=50, r=30, t=30, b=30),
                yaxis=dict(title="Water Level Change (feet)"),
                yaxis2=dict(title="Precipitation (inch)"),
            )

            warnings_text = "\n".join(warnings) if warnings else ""
            return fig, warnings_text

    return go.Figure(), ""


@callback(
    Output("wb_ts_fig", "figure"),
    Input("choropleth-map", "clickData"),
    Input("variable-dropdown", "value"),
    State("cat-click-store", "data"),
)
def water_balance_figure(click_data, model_var, stored_cat_click):
    """
    Define time series figure locations on map.
    """
    if click_data:
        layer = click_data["points"][0]["curveNumber"]
        if layer == 0:  # click must be on polygon layer
            cat_id = click_data["points"][0]["customdata"][0]
            # print(click_data)

            if model_var == "Streamflow":
                return figures_main.plot_q_out(data, cat_id)

            if model_var == "Actual ET":
                print("returning et plot")
                return figures_main.plot_actual_et(data, cat_id)

            if model_var == "Precipitation":
                return figures_main.plot_precip(data, cat_id)

            if model_var == "Groundwater Storage":
                return figures_main.plot_storage(data, cat_id)

            if model_var == "Potential ET":
                return figures_main.plot_potential_et(data, cat_id)

    return figures_main.plot_default(data)


@callback(
    Output("choropleth-map", "figure", allow_duplicate=True),
    Input("choropleth-map", "clickData"),
    prevent_initial_call=True,
)
def higlight_line_segment_on_map(click_data):
    """
    Highlight line segment to make user selection more obvious. This method use linestrings, rather
    than polygons, to provide higlighting around the polygons.
    """
    if click_data:
        layer = click_data["points"][0]["curveNumber"]
        # print(f"layer: {layer}")

        if layer == 0:
            id = click_data["points"][0]["customdata"][0]
            patched_figure = Patch()

            # print(id)
            subset = data.gdf[data.gdf["divide_id"] == id]
            # print(subset)

            # if geometry is a LINESTRING
            # catchment_lats = list(subset["geometry"][0].exterior.xy[1])
            # catchment_lons = list(subset["geometry"][0].exterior.xy[0])

            # if geometry is a POLYGON
            catchment_lons = list(subset["geometry"].iloc[0].exterior.xy[0])
            catchment_lats = list(subset["geometry"].iloc[0].exterior.xy[1])

            fig_data = go.Scattermap(
                lat=catchment_lats,
                lon=catchment_lons,
                mode="lines",
                hoverinfo="skip",
                line=dict(
                    width=3,
                    color="white",
                ),
                # hovertext=gdf_cat["divide_id"].tolist(),
            )

            patched_figure["data"][1] = fig_data
            return patched_figure

    return no_update


@callback(
    Output("cat-click-store", "data"),
    Input("choropleth-map", "clickData"),
)
def store_catchment_click(click_data):
    """ """
    if click_data:
        layer = click_data["points"][0]["curveNumber"]
        print(f"{layer=}")
        if layer == 0:
            print(click_data)
            cat_id = click_data["points"][0]["customdata"]
            print(cat_id)
            return cat_id


@callback(
    Output("comparison-table-container", "children"),
    Input("selected-date-store", "data"),
)
def update_table(selected_date):
    # Convert the selected date into a pandas datetime object
    selected_date = pd.to_datetime(selected_date)

    # Extract the selected month and year
    selected_month = selected_date.month

    # Filter the DataFrame to get data for the selected month across all years
    # selected_month_df = df_q[df_q.index.month == selected_month]
    selected_month_df = data.tnc_domain_q[
        data.tnc_domain_q.index.month == selected_month
    ]

    # Get the volume for the selected month (for the specific year)
    # selected_month_value = df_q.loc[selected_date, "Simulated Monthly Volume"]
    selected_month_value = data.tnc_domain_q.loc[
        selected_date, "monthly_vol_af"
    ]

    # Calculate the average volume for that month across all years
    # average_value = selected_month_df["Simulated Monthly Volume"].mean()
    average_value = selected_month_df["monthly_vol_af"].mean()

    # Calculate the "% of average" for the selected month
    percent_of_average = (selected_month_value / average_value) * 100

    # Format the data for display
    formatted_selected_value = f"{selected_month_value:,.0f}"
    formatted_average_value = f"{average_value:,.0f}"
    formatted_percent_of_average = f"{percent_of_average:.0f}%"

    # Construct the dbc.Table with a vertical layout
    table = dbc.Table(
        # Table header
        [
            # Table body with data in vertical layout
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td("Month"),
                            html.Td(selected_date.strftime("%B %Y")),
                        ]
                    ),  # Month Year
                    html.Tr(
                        [
                            html.Td("Monthly Volume (af)"),
                            html.Td(formatted_selected_value),
                        ]
                    ),  # Selected month value
                    html.Tr(
                        [
                            html.Td("Avg Volume (af)"),
                            html.Td(formatted_average_value),
                        ]
                    ),  # Average value for month
                    html.Tr(
                        [
                            html.Td("% of Avg"),
                            html.Td(formatted_percent_of_average),
                        ]
                    ),  # % of average
                ]
            )
        ],
        bordered=True,  # Add table borders
        hover=True,  # Enable hover effect
        striped=True,  # Stripe the rows
        responsive=True,  # Make table responsive
        size="sm",  # Small size for a more compact look
        style={
            # "border-radius": "5px",  # Rounded corners
            "overflow": "hidden",  # Ensure borders and rounding apply smoothly
        },
    )

    return table


@callback(
    Output("summary-text", "children"),
    Input("year-dropdown", "value"),
)
def update_summary_text(selected_year):
    """
    Update summary paragraph with statistics from the data class.
    """
    if selected_year is None:
        raise PreventUpdate

    # Convert selected year into water year format
    water_year = f"Water Year {selected_year}"

    # Get total precipitation for the selected water year (example dataset key)
    if hasattr(data, "terraclim_ann_precip"):
        total_precip = data.terraclim_ann_precip["wy_precip_inch"].loc[
            selected_year
        ]
        precip_quartile = data.terraclim_ann_precip["Quartile"].loc[
            selected_year
        ]
    else:
        total_precip = None
        precip_quartile = None

    if hasattr(data, "terraclim_mean_annual_precip"):
        mean_precip = data.terraclim_mean_annual_precip
        precip_magnitude = total_precip / mean_precip

        if precip_magnitude > 1:
            precip_sign = "greater"
        elif precip_magnitude <= 1:
            precip_sign = "less"
    else:
        total_precip = "NaN"
        precip_sign = None

    # evapotranspiration
    et_sign = data.et_wy_quartile.iloc[
        data.et_wy_quartile.index == selected_year
    ].values[0]

    et_vol_af = (
        data.ngen_basinwide_et_loss_m3[
            data.ngen_basinwide_et_loss_m3["water_year"] == selected_year
        ]["ACTUAL_ET_VOL_M3"].sum()
    ) * 0.000810714  # UNIT: m^3 to acre-feet

    # tributary flows
    baseflow_months = data.jalama_tributaries_monthly_cfs.loc[
        data.jalama_tributaries_monthly_cfs.index.month.isin(range(6, 9))
    ]
    baseflow_wy = baseflow_months.loc[
        baseflow_months["water_year"] == selected_year
    ]
    baseflow_min_cfs = (
        baseflow_wy.iloc[:, :3].min().min()
    )  # subset out "water_year" before min()
    baseflow_max_cfs = baseflow_wy.iloc[:, :3].max().max()  # " "

    # groundwater change
    gw_elevation_delta_wy = (
        data.ds_ngen["NET_GW_CHANGE_FEET"]
        .where(data.ds_ngen["wy"] == selected_year, drop=True)
        .mean(dim="catchment")  # basinwide mean
        .cumsum()  # running sum
        .to_pandas()
    )
    eoy_diff = gw_elevation_delta_wy.iloc[-1] - gw_elevation_delta_wy.iloc[0]
    max_level = gw_elevation_delta_wy.max()

    if eoy_diff > 0:
        eoy_diff_sign = "above"
    else:
        eoy_diff_sign = "below"

    # Format text output
    summary_text = (
        f"Water Year {selected_year} was {precip_quartile} rain year, with a total of "
        f"{total_precip:.1f} inches of precipitation in the preserve. "
        f"This was {precip_magnitude:.1f} times {precip_sign} than normal. "
        f"Average baseflow in the main tributaries to Jalama Creek was between {baseflow_min_cfs:.0f} "
        f"and {baseflow_max_cfs:.0f} cfs during the dry season (June-August). "
        f"Evapotranspiration in WY {selected_year} was {et_sign} "
        f" with a volume of {et_vol_af:,.0f} acre-feet. "
        f"Starting from Oct 1 {selected_year - 1}, the mean groundwater elevation in the basin increased "
        f"{max_level:.1f} feet during the rainy season, "
        f"and ended the water year {abs(eoy_diff):.1f} feet {eoy_diff_sign} the starting elevation."
    )

    return summary_text
