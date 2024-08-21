# rHP-Pandas
Package `rhppandas` intends to recreate for rHEALPix what `h3pandas`, developed by Daniel Jahn (https://github.com/DahnJ/H3-Pandas), does for `h3-py`, the Python binding for Uber's H3 DGGS. It provides a bridge between package `rhealpixdggs` and the dataframes used by `pandas` and `geopandas`.

[!IMPORTANT]
> This is very much a work in progress, and in the early stages. Some of the API available in `h3pandas` remains unimplemented, none of it has been used in production. The package comes with some tests but we make no claims of completeness regarding those.

In other words: the package in its current form is mostly meant for developers, and not in a state that would be suitable for end users.

## Conda Environment
Use yaml file `environment.yml` to create a conda environment for basic use if you'd like to give the package a spin.

Adding yaml file `environment-dev.yml` to your conda environment will add the packages you need to run the automated tests.

[!NOTE]
> A large part of why some of the API remains unimplemented has to do with the relevant functions in the backend not being implemented yet either. Development of the wrapper API within `rhealpixdggs` is happening in tandem with `rhppandas`, with the intention of adding adapter functions one by one as the backend is fleshed out.

This also explains why `environment.yml` points to a branch of the `rhealpixdggs-py` repository instead of a release of the `rhealpixdggs` package.

## Usage Examples
Using a basic dataframe with lat/lng coordinates:
```
> from rhppandas import rhppandas
> import pandas as pd
>
> basic_dataframe = pd.DataFrame({"lat": [50, 51], "lng": [14, 15]})
> basic_dataframe
       lat  lng
    0   50   14
    1   51   15
```
* Add `rhealpixdggs` cell indices as the first column in the dataframe:
```
> geo2rhp = basic_dataframe.rhp.geo_to_rhp(9)
> geo2rhp
               lat  lng
    rhp_09              
    N216055611   50   14
    N208542111   51   15 
```
* Turn DGGS cell indices into points and add them in the `geometry` column:
```
> rhp2geo = geo2rhp.rhp.rhp_to_geo()
> rhp2geo
                lat  lng                   geometry
    rhp_09                                         
    N216055611   50   14  POINT (14.00085 50.00206)
    N208542111   51   15  POINT (14.99814 51.00185)
```
* Add cell boundaries as the `geometry` column:
```
> rhp2geoboundary = geo2rhp.rhp.rhp_to_geo_boundary()
> rhp2geoboundary
                lat  lng                                           geometry
    rhp_09                                                                 
    N216055611   50   14  POLYGON ((13.99625 50.00459, 14.0017 50.00459,...
    N208542111   51   15  POLYGON ((14.99349 51.00438, 14.99907 51.00438...
```
* Add a colum with cell resolutions to the dataframe:
```
> withresolution = geo2rhp.rhp.rhp_get_resolution()
> withresolution
                lat  lng  rhp_resolution
    rhp_09                              
    N216055611   50   14               9
    N208542111   51   15               9
```
* Add a column with the parent cell at resolution 0:
```
> withbasecell = geo2rhp.rhp.rhp_get_base_cell()
> withbasecell
                lat  lng rhp_base_cell
    rhp_09                            
    N216055611   50   14             N
    N208542111   51   15             N
```
* Add a column with the parent cell indices at resolution 5:
```
> withparent = geo2rhp.rhp.rhp_to_parent(5)
> withparent
                lat  lng  rhp_05
    rhp_09                      
    N216055611   50   14  N21605
    N208542111   51   15  N20854
```
* Add a column with the cell area:
```
> withcellarea = geo2rhp.rhp.cell_area()
> withcellarea
                lat  lng  rhp_cell_area
    rhp_09                             
    N216055611   50   14       0.258798
    N208542111   51   15       0.258798
```

## Running Tests
rhppandas uses pytest as its test framework. Type `pytest` in a shell with an active conda environment for rhppandas.

Typing `pytest --cov` will run the tests and print some info on test coverage of the code base.
