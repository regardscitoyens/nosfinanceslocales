angular.module('app', ['ui.router', 'ui.bootstrap'])
    .constant('API_ROOT_URL', 'http://www.nosfinanceslocales.fr/api')
    .constant('TILES_ROOT_URL', 'http://{s}.tile.nosfinanceslocales.fr/tiles') // get this info from server ?
    .constant('THUMBNAILS_URL', '/static/thumbnails')
    .constant('TEMPLATE_URL', '/static/templates')
    .factory('mapUtils', function(TILES_ROOT_URL, THUMBNAILS_URL) {
        return {
            getTileUrl: function(map_id) {
                return TILES_ROOT_URL + '/' + map_id + "/{z}/{x}/{y}.png";
            },
            getGridUrl: function(map_id) {
                return TILES_ROOT_URL + '/' + map_id + "/{z}/{x}/{y}.grid.json";
            },
            getThumbnailUrl: function(map_id) {
                return THUMBNAILS_URL + '/' + map_id + '.png';
            }
        };
    })
    .factory('Resource', function($http, API_ROOT_URL) {
        function Factory(name) {
            var resource = {
                get: function(id) {
                    return $http.get(API_ROOT_URL + '/' + name + '/' + id)
                        .then(function(response) {
                            return response.data.results;
                        });
                },
                all: function() {
                    return $http.get(API_ROOT_URL + '/' + name + 's')
                        .then(function(response) {
                            return response.data.results;
                        });
                }
            }
            return resource;
        }
        return Factory
    })
    .factory('CitySearch', function($http, API_ROOT_URL) {
        return {
            get: function(term) {
                return $http.get(API_ROOT_URL + '/' + 'city_search' + '?term=' + term)
                    .then(function(response) {
                        return response.data.results;
                    });
            }
        }
    })
    .config(
        [ '$stateProvider', '$urlRouterProvider', '$locationProvider', 'TEMPLATE_URL',
        function ($stateProvider, $urlRouterProvider, $locationProvider, TEMPLATE_URL) {
            $locationProvider.html5Mode(true);
            $urlRouterProvider.otherwise('/');
            $stateProvider
                .state('about', {
                    url: '/about',
                    templateUrl: TEMPLATE_URL + '/about.html',
                })
                .state('localfinance', {
                    url: '/{id:[0-9]{1,4}}',
                    views: {
                        '': {
                            templateUrl: TEMPLATE_URL + '/localfinance.detail.html',
                            controller: 'LocalFinanceDetailCtrl'
                        },
                    }
                })
                .state('maps', {
                    abstract: true,
                    url: '',
                    templateUrl: TEMPLATE_URL + '/maps.html',
                    controller: 'MapsCtrl',
                    resolve: {
                        timemaps: function(Resource) {
                            return Resource('timemap').all()
                        },
                        stats: function(Resource) {
                            return Resource('stat').all();
                        }
                    }
                })
                .state('maps.list', {
                    url: '/',
                    views: {
                        '': {
                            templateUrl: TEMPLATE_URL + '/map.list.html',
                            controller: 'MapListCtrl'
                        }
                    }
                })
                .state('maps.detail', {
                    url: '/{var_name:[0-9a-zA-Z_]+}?ids',
                    views: {
                        '': {
                            templateUrl: TEMPLATE_URL + '/map.detail.html',
                            controller: 'MapDetailCtrl'
                        }
                    }
                })
        }])
    .controller('Home', ['$scope', '$state',
        function($scope, $state, stats) {
            $scope.$state = $state;
            $scope.stats = stats;
    }])
    .controller('MapsCtrl', ['$scope', '$state', 'mapUtils', 'timemaps', 'stats',
        function($scope, $state, mapUtils, timemaps, stats) {
            $scope.mapUtils = mapUtils;
            $scope.timemaps = timemaps;
            $scope.stats = stats;
        }])
    .controller('MapListCtrl', ['$scope', '$state', '$timeout',
        function($scope, $state, $timeout) {
            $scope.thumbailUrls = [];
        }])
    .controller('MapDetailCtrl', ['$scope', '$state', '$stateParams', 'Resource', 'mapUtils', 'CitySearch',
        function($scope, $state, $stateParams, Resource, mapUtils, CitySearch) {
            // Colors used for line chart
            var colors = d3.scale.category10();

            // Fetch city finance data and add it to linesData
            function isCityLoaded(id) {
                return ($scope.linesData.filter(function(d){return (id==d.id)}).length > 0)
            }
            $scope.loadCityFinance = function(id) {
                if  (isCityLoaded(id)) {
                    return ;
                }
                Resource('finance').get(id).then(function(results) {
                    if (results.length == 0) {
                        console.log("No data");
                        return;
                    }
                    // get var_name stat
                    var res = results.map(function(d){
                        return [d.year, parseFloat(d.data[$scope.timemap.var_name])];
                    })
                    if (!isCityLoaded(id)) {
                        $scope.linesData.push({name: results[0].name, data: res, color: colors(results[0].name), id: id});
                    }
                });
            }

            $scope.getCities = CitySearch.get;
            $scope.centerMapAndLoadStatCity = function(city) {
                // first update map
                $scope.mapOptions = {
                    zoom: 8,
                    lat: city.lat,
                    lng: city.lng
                }

                // then get stats of the city
                //$scope.loadCityFinance(city.id);
                $state.transitionTo('maps.detail', {
                    var_name: $stateParams.var_name,
                });
            };

            // Data for line chart
            $scope.linesData = [
                {
                    name: 'FRANCE',
                    data: $scope.stats.filter(function(stat){
                        return (stat.var_name == $stateParams.var_name)
                    })[0].mean_by_year,
                    color: colors('FRANCE')
                }
            ];

            // get the timemap for this variable
            $scope.timemap = $scope.timemaps.filter(function(timemap) {
                return (timemap.var_name == $stateParams.var_name)
            })[0];

            $scope.removeLine = function(id) {
                // make impossible to remove france
                if (id) {
                    $scope.linesData.some(function(d, i) {
                        if (d.id==id){
                            $scope.linesData.splice(i, i);
                            return true;
                        }
                    });
                }
            }

            // Maps config
            function findMapData(year){
                return $scope.timemap.maps.filter(function(m) {
                    return (m.year == year)
                })[0];
            }
            // take first map
            $scope.year = $scope.timemap.maps[0].year;
            $scope.opacity = 0.8;
            $scope.mapData = findMapData($scope.timemap.maps[0].year);

            $scope.$on('onMapMouseOver', function(e, data) {
                $scope.mouseOverdata = data;
                $scope.$apply();
            });

            // Handle load of city finance data
            function loadCityFinanceIdsFromState() {
                if (!$stateParams.ids) return;
                $stateParams.ids.split(",").forEach(function(id) {
                    $scope.loadCityFinance(+id);
                });
            }
            loadCityFinanceIdsFromState();

            $scope.$watch('linesData', function(newval, oldval) {
                var ids = newval.filter(function(d) { return (d.id)})
                    .map(function(d) {return d.id});
                if (ids.length == 0) return;
                $state.transitionTo('maps.detail', {
                    var_name: $stateParams.var_name,
                    ids: ids.join(',')
                }, {
                    reloadOnSearch: false,
                    notify:false
                });
            }, true);

            // map interaction
            $scope.$on('onMapClick', function(e, data) {
                if (!data) return;
                $scope.loadCityFinance(data.id)
                $scope.$apply();
            });
        }])
    .directive('leafletMap', function ($rootScope, mapUtils) {
        return {
            restrict: "A",
            replace: false,
            scope: {
                timemap: '=',
                variables: '=',
                options: '=',
                click: '&onClick',
                mouseOver: '&onMouseOver',
                mouseOut: '&onMouseOut'
            },
            link: function($scope, element, attrs, controller) {
                var onClick = $scope.click(),
                    onMouseOver = $scope.mouseOver(),
                    onMouseOut = $scope.mouseOut();
                var refmap = $scope.timemap.maps[0];

                var southWest = L.latLng(refmap.extent[1],
                                         refmap.extent[0]),
                    northEast = L.latLng(refmap.extent[3],
                                         refmap.extent[2]),
                    bounds = L.latLngBounds(southWest, northEast);
                var stamenAttribution = 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>';
                var basemap = new L.TileLayer(
                        "http://{s}.tile.stamen.com/toner/{z}/{x}/{y}.png",
                        {attribution: stamenAttribution});
                var layers = [basemap];
                var yearsToLayers = {}, yearsToUtfGrids = {}, currentUtfGrid, years = [];
                var rcAttribution = '<a href="http://www.nosdonnees.fr/dataset/donnees-comptables-et-fiscales-des-collectivites-locales">Data</a> freed by <a href="http://www.regardscitoyens.org">Regards Citoyens</a> <img src="/static/img/opendata.png" height="12">'
                for(var imap=0;imap<$scope.timemap.maps.length;imap++) {
                    var map = $scope.timemap.maps[imap];
                    var layer = new L.TileLayer(
                        mapUtils.getTileUrl(map.id),
                        {opacity: 0, subdomains: 'abc',
                         attribution: rcAttribution}
                    );
                    layers.push(layer);
                    yearsToLayers[map.year] = layer;
                    yearsToUtfGrids[map.year] = new L.UtfGrid(mapUtils.getGridUrl(map.id), {useJsonP: false});
                    years.push(map.year);
                }

                var interactiveLayerGroup = L.layerGroup(layers);

                var options = {
                    center: L.latLng(46.22587886848165, 2.21040301636657),
                    zoom: 6,
                    minZoom: refmap.minzoom, // should take the max of min
                    maxZoom: refmap.maxzoom, // should take the min of max
                };

                // leaflet map
                var lmap = L.map(element[0], options)
                    .addLayer(interactiveLayerGroup);

                $scope.$watch('options', function(newVal, oldVal) {
                    if (!newVal) return;
                    lmap.setView(new L.LatLng(newVal.lat, newVal.lng), newVal.zoom);
                }, true);

                $scope.$watch('variables', function(newVal, oldVal) {
                    return $scope.render(newVal.opacity, newVal.year);
                }, true);

                $scope.render = function(opacity, year) {
                    if (!year) {
                        return;
                    }
                    var yearLow = Math.floor(year), newUtfGrid = yearsToUtfGrids[yearLow];
                    for (var iyear=0;iyear<years.length;iyear++) {
                        // XXX: find a better way to set opacity for better ux
                        var x = (year-yearLow);
                        if (years[iyear] == yearLow) {
                            yearsToLayers[yearLow].setOpacity(opacity * (1 - x * x * x));
                        } else if (years[iyear] == yearLow+1) {
                            yearsToLayers[yearLow+1].setOpacity(opacity * (x + x * x)/2);
                        } else {
                            yearsToLayers[years[iyear]].setOpacity(0);
                        }
                    }
                    if (currentUtfGrid) {
                        lmap.removeLayer(currentUtfGrid);
                    }
                    lmap.addLayer(newUtfGrid);
                    currentUtfGrid = newUtfGrid;

                    //Events
                    currentUtfGrid.on('click', function (e) {
                        $rootScope.$broadcast('onMapClick', e.data);
                        //if (e.data) {
                        //    onClick(e.data);
                        //}
                    });
                    currentUtfGrid.on('mouseover', function (e) {
                        $rootScope.$broadcast('onMapMouseOver', e.data);
                        //if (e.data) {
                        //    onMouseOver(e.data);
                        //}
                    });
                    currentUtfGrid.on('mouseout', function (e) {
                    });

                }
            }
        }})
    .directive('lineChart', function () {
        return {
            restrict: "A",
            replace: false,
            scope: {
                data: '=',
                name: '='
            },
            link: function($scope, element, attrs, controller) {
                // data = [{name: '', data: ''},]
                var tooltip = d3.select(document.createElement('div'))
                    .append("div")
                    .attr("class", "popover")
                    .style("display", 'none');
                document.body.appendChild(tooltip.node());

                var margin = {top: 20, right: 20, bottom: 30, left: 50},
                    width = 400 - margin.left - margin.right,
                    height = 250 - margin.top - margin.bottom;
                var parseDate = d3.time.format("%Y").parse;
                var svg;

                $scope.render = function(data) {
                    if (!data) {
                        return;
                    }
                    d3.select(element[0]).selectAll('svg').remove();

                    var svg = d3.select(element[0])
                        .append("svg")
                        .attr("width", width + margin.left + margin.right)
                        .attr("height", height + margin.top + margin.bottom)
                        .append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
                    // take the first series to set x
                    var x = d3.time.scale()
                        .range([0, width])
                        .domain(d3.extent(data[0].data, function(d){return parseDate(d[0].toString())}));
                    var y = d3.scale.linear()
                        .range([height, 0])
                        .domain([
                            d3.min(data, function(line) {return d3.min(line.data, function(d){return d[1]})}) * 0.95,
                            d3.max(data, function(line) {return d3.max(line.data, function(d){return d[1]})}) * 1.05
                            ]);
                    //Create SVG element
                    var line = d3.svg.line()
                        .x(function(d){return x(parseDate(d[0].toString()))})
                        .y(function(d){return y(d[1])});
                    var xAxis = d3.svg.axis()
                        .scale(x)
                        .orient('bottom')
                        .ticks(d3.time.years, 5);
                    svg.append("g")
                        .attr('class', 'x axis')
                        .attr("transform", "translate(0," + height + ")")
                        .call(xAxis);
                    var yAxis = d3.svg.axis().scale(y).orient("left");
                    svg.append("g")
                        .attr('class', 'y axis')
                        .call(yAxis)
                        .append("text")
                        .attr("transform", "rotate(-90)")
                        .attr("y", 6)
                        .attr("dy", ".71em")
                        .style("text-anchor", "end")
                        .text($scope.name);
                    var lines = svg.selectAll(".gline")
                        .data(data)
                        .enter().append("g")
                        .attr("class", "gline");
                    lines.append("path")
                        .attr("class", "line")
                        .attr("d", function(d) { return line(d.data); })
                        .style("stroke", function(d) { return d.color; });
                    lines.selectAll("circle")
                        .data(function(d, i) { return d.data.map(function(el){return [el[0], el[1], d.color]});})
                        .enter()
                        .append("circle")
                        .attr("stroke", function(d, i) {return d[2]})
                        .attr("r", 4)
                        .attr("cx", function(d) { return x(parseDate(d[0].toString())); })
                        .attr("cy", function(d) { return y(d[1]); })
                        .attr("class", "linecircle")
                        .on("mouseover", function(d) {
                            tooltip.html("<div class='popover-content'> <b>" +
                                d[0] + " : " + d3.format(".2f")(d[1]) +
                                "</b></div>");
                            tooltip.style("left", d3.event.pageX + 10 + "px");
                            tooltip.style("top", d3.event.pageY - 50 + "px");
                            tooltip.style("display", 'block')
                        })
                        .on("mouseout", function(d) {
                            tooltip.style("display", 'none')
                        })
                        .style("pointer-events","all")
                        .append('title')
                        .text(function(d) { return d[0] + ' : ' + d[1];});
                }
                $scope.$watchCollection('data', function(newData, oldData) {
                    $scope.render(newData);
                });
            }
        }
    });
