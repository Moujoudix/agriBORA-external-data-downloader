# src/maize_data/downloaders/__init__.py
__all__ = [
    "run_kamis",
    "run_opendata_ke_socrata",
    "run_hdx_ckan_wfp_prices",
    "run_worldbank_wdi",
    "run_nasa_power",
    "run_era5_cds",
    "run_geoboundaries_adm1",
    "run_url_list",
    "run_uncomtrade_template",
]

def run_kamis(*args, **kwargs):
    from .kamis import run_kamis as f
    return f(*args, **kwargs)

def run_opendata_ke_socrata(*args, **kwargs):
    from .opendata_ke_socrata import run_opendata_ke_socrata as f
    return f(*args, **kwargs)

def run_hdx_ckan_wfp_prices(*args, **kwargs):
    from .hdx_ckan import run_hdx_ckan_wfp_prices as f
    return f(*args, **kwargs)

def run_worldbank_wdi(*args, **kwargs):
    from .worldbank_wdi import run_worldbank_wdi as f
    return f(*args, **kwargs)

def run_nasa_power(*args, **kwargs):
    from .nasa_power import run_nasa_power as f
    return f(*args, **kwargs)

def run_era5_cds(*args, **kwargs):
    from .era5_cds import run_era5_cds as f
    return f(*args, **kwargs)

def run_geoboundaries_adm1(*args, **kwargs):
    from .geoboundaries import run_geoboundaries_adm1 as f
    return f(*args, **kwargs)

def run_url_list(*args, **kwargs):
    from .url_list_downloader import run_url_list as f
    return f(*args, **kwargs)

def run_uncomtrade_template(*args, **kwargs):
    from .uncomtrade import run_uncomtrade_template as f
    return f(*args, **kwargs)
