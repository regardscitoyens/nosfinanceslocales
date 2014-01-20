angular.module('app', ['ui.router', 'ui.bootstrap'])
    .constant('API_ROOT_URL', 'http://www.nosfinanceslocales.fr/api')
    .constant('TILES_ROOT_URL', 'http://{s}.tile.localfinance.fr/tiles') // get this info from server ?
    .constant('THUMBNAILS_URL', '/static/thumbnails')
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
        [ '$stateProvider', '$urlRouterProvider',
        function ($stateProvider, $urlRouterProvider) {
            $urlRouterProvider.when('', '/maps/');
            $urlRouterProvider.otherwise('/maps/');
            $stateProvider
                .state('about', {
                    url: '/about',
                    templateUrl: 'templates/about.html',
                })
                .state('localfinance', {
                    url: '/{id:[0-9]{1,4}}',
                    views: {
                        '': {
                            templateUrl: 'templates/localfinance.detail.html',
                            controller: 'LocalFinanceDetailCtrl'
                        },
                    }
                })
                .state('maps', {
                    abstract: true,
                    url: '/maps',
                    templateUrl: 'templates/maps.html',
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
                            templateUrl: 'templates/map.list.html',
                            controller: 'MapListCtrl'
                        }
                    }
                })
                .state('maps.detail', {
                    url: '/{var_name}',
                    views: {
                        '': {
                            templateUrl: 'templates/map.detail.html',
                            controller: 'MapDetailCtrl'
                        }
                    }
                });
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
            function fireDigestEverySecond() {
                $timeout(fireDigestEverySecond , 1000);
            };
            fireDigestEverySecond();
        }])
    .controller('MapDetailCtrl', ['$scope', '$stateParams', 'Resource', 'mapUtils', 'CitySearch',
        function($scope, $stateParams, Resource, mapUtils, CitySearch) {
            $scope.getCities = CitySearch.get;
            var colors = d3.scale.category10();;
            // get the timemap for this variable
            $scope.timemap = $scope.timemaps.filter(function(timemap) {
                return (timemap.var_name == $stateParams.var_name)
            })[0];
            // same for stats
            $scope.linesData = [
                {
                    name: 'FRANCE',
                    data: $scope.stats.filter(function(stat){
                        return (stat.var_name == $stateParams.var_name)
                    })[0].mean_by_year,
                    color: colors('FRANCE')
                }
            ];
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
            // take first map
            $scope.year = $scope.timemap.maps[0].year;
            $scope.opacity = 0.85;
            function findMapData(year){
                return $scope.timemap.maps.filter(function(m) {
                    return (m.year == year)
                })[0];
            }
            $scope.mapData = findMapData($scope.timemap.maps[0].year);
            $scope.onClick = function(data) {
                function checkLine(id) {
                    return ($scope.linesData.filter(function(d){return (data.id==d.id)}).length > 0)
                }
                if  (checkLine(data.id)) {
                    return ;
                }
                Resource('finance').get(data.id).then(function(results) {
                    // get var_name stat
                    var res = results.map(function(d){
                        return [d.year, parseFloat(d.data[$scope.timemap.var_name])];
                    })
                    if (!checkLine(data.id)) {
                        $scope.linesData.push({name: results[0].name, data: res, color: colors(results[0].name), id: data.id});
                    }
                });
                $scope.$apply();
            }
            $scope.onMouseOver = function(data) {
                $scope.mouseOverdata = data;
                $scope.$apply();
            }
            document.data = $scope.linesData;
        }])
    .directive('leafletMap', function (mapUtils) {
        return {
            restrict: "A",
            replace: false,
            scope: {
                timemap: '=',
                year: '=',
                opacityFactor: '=',
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
                var dgfipAttribution = 'Data by <a href="http://www.collectivites-locales.gouv.fr/">DGFiP</a> under <a href="http://wiki.data.gouv.fr/wiki/Licence_Ouverte_/_Open_Licence"> LO</a>'
                for(var imap=0;imap<$scope.timemap.maps.length;imap++) {
                    var map = $scope.timemap.maps[imap];
                    var layer = new L.TileLayer(
                        mapUtils.getTileUrl(map.id),
                        {opacity: 0, subdomains: 'abc',
                         attribution: dgfipAttribution}
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

                $scope.$watch('year', function(newVal, oldVal) {
                    return $scope.render(newVal);
                }, true);

                $scope.render = function(year) {
                    if (!year) {
                        return;
                    }
                    var yearLow = Math.floor(year), newUtfGrid = yearsToUtfGrids[yearLow];
                    for (var iyear=0;iyear<years.length;iyear++) {
                        if (years[iyear] == yearLow) {
                            yearsToLayers[yearLow].setOpacity(Math.max(1, 1-(year-yearLow) + 0.5));
                        } else if (years[iyear] == yearLow+1) {
                            yearsToLayers[yearLow+1].setOpacity(-(yearLow-year));
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
                        if (e.data) {
                            onClick(e.data);
                        }
                    });
                    currentUtfGrid.on('mouseover', function (e) {
                        if (e.data) {
                            onMouseOver(e.data);
                        }
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
                    .attr("class", "mytooltip popover")
                    .style("opacity", 0)
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
                            tooltip.transition().duration(200).style("opacity", 0.9);
                        })
                        .on("mouseout", function(d) {
                            tooltip.transition().duration(200).style("opacity", 0);
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
