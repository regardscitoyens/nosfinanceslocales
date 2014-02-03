# NosFinancesLocales.fr

This is the code in production for the website [NosFinancesLocales.fr](http://www.nosfinanceslocales.fr).

The main goal of this project is to illustrate [french cities financial data](http://www.nosdonnees.fr/dataset/donnees-comptables-et-fiscales-des-collectivites-locales) recently freed by [Regards Citoyens](http://www.regardscitoyens.org).

It is also an opportunity to show server and client code and how to install such a stack. Special thanks to these awesome projects:
 * [mapnik](http://mapnik.org/) for cartography
 * [pyramid](http://www.pylonsproject.org/) for web server
 * [angularjs](http://angularjs.org/) for client app
 * [postgresql](http://www.postgresql.org/) for database


## INSTALL

Note: everything was run on a debian wheezy.


 * Postgresql 9.1 postgis 2.0
   ```bash
    aptitude install postgresql-9.1-postgis
    ```

 * mapnik 2.2.0 from source
   ```bash
    git clone https://github.com/mapnik/mapnik.git
    cd mapnik
    git checkout v2.2.0
    ./configure
    make
    make install
    ```

 * node v0.10.24 (cf. [build from source](https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager)
   ```bash
    sudo apt-get install python g++ make checkinstallmkdir ~/src && cd $_wget -N http://nodejs.org/dist/node-latest.tar.gztar xzvf node-latest.tar.gz && cd node-v*./configuresudo checkinstall -y --install=no --pkgversion 0.10.24  # Replace with current version number.
    sudo dpkg -i node_*
    ```

 * carto 0.9.5 [Carto map stylesheet compiler](https://github.com/mapbox/carto)
   ```bash
   npm install -g carto
    ```

  * install virtualenv
   ```bash
    apt-get install python-pip
    pip install virtualenv
    pip install virtualenvwrapper
    ```

## CONFIG

 * Create postgresql db and add necessary extensions
   ```bash
    createdb localfinance
    psql -d createdb
    CREATE EXTENSION hstore;
    CREATE EXTENSION postgis;
    CREATE EXTENSION unaccent; # for city search
    CREATE EXTENSION pg_trgm; # indexation for city search
    ```

TODO: add localfinance pyramid app in virtualenv


## PREPARE DB, FILL IT

python -m localfinance.scripts.initializedb production.ini
python -m localfinance.scripts.filladminzone production.ini data/COMMUNES_4326/COMMUNE.shp
python -m localfinance.scripts.filladminzonefinance production.ini data/city_all.csv


## POSTGRESQL OPTIMIZATION

Add indexes on:
 * CREATE INDEX adminzone_name_lower_unaccent_idx ON adminzone USING gist (lower(unaccent(name)) gist_trgm_ops);
 * CREATE INDEX adminzonefinance_adminzone_id_index ON adminzonefinance
   (adminzone_id)



## PRECOMPUTE STATS AND TILES

TODO: add bash script and improve code


## RUN

TODO: add make file
