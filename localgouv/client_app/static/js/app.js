angular.module('app', ['ui.router', 'ui.bootstrap'])
    .constant('CLOUDMADE_API_KEY', '96d88d05d11e4ce4b841290fa31277fb')
    .constant('API_ROOT_URL', 'http://www.localfinance.fr/api')
    .constant('TILES_ROOT_URL', 'http://www.localfinance.fr/tiles') // get this info from server ?
    .constant('THUMBNAILS_URL', 'http://www.localfinance.fr/static/thumbnails')
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
                        })
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
    .controller('MapDetailCtrl', ['$scope', '$stateParams', 'Resource', 'mapUtils',
        function($scope, $stateParams, Resource, mapUtils) {
            // get the timemap for this variable
            $scope.timemap = $scope.timemaps.filter(function(timemap) {
                return (timemap.var_name == $stateParams.var_name)
            })[0];
            // same for stats
            $scope.stat = $scope.stats.filter(function(stat) {
                return (stat.var_name == $stateParams.var_name)
            })[0];
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
                Resource('finance').get(data.id).then(function(results) {
                    $scope.cityFinance = results;
                });
                $scope.$apply();
            }
            $scope.onMouseOver = function(data) {
                $scope.mouseOverdata = data;
                $scope.$apply();
            }
        }])
    .directive('leafletMap', function (mapUtils, CLOUDMADE_API_KEY) {
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

                var basemap = new L.TileLayer("http://{s}.tile.stamen.com/toner" +
                        "/{z}/{x}/{y}.png"), utfGrid;
                var layers = [basemap];
                var yearsToLayers = {}, yearsToUtfGrids = {}, utfGrid, years = [];
                for(var imap=0;imap<$scope.timemap.maps.length;imap++) {
                    var map = $scope.timemap.maps[imap];
                    var layer = new L.TileLayer(mapUtils.getTileUrl(map.id),{opacity: 0})
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
                    maxZoom: refmap.maxzoom // should take the min of max
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
                    if (utfGrid) {
                        lmap.removeLayer(utfGrid);
                    }
                    lmap.addLayer(newUtfGrid);
                    utfGrid = newUtfGrid;

                    //Events
                    utfGrid.on('click', function (e) {
                        if (e.data) {
                            onClick(e.data);
                        }
                    });
                    utfGrid.on('mouseover', function (e) {
                        if (e.data) {
                            onMouseOver(e.data);
                        }
                    });
                    utfGrid.on('mouseout', function (e) {
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
            },
            link: function($scope, element, attrs, controller) {
                var tooltip = d3.select(element[0])
                    .append("div")
                    .attr("class", "tooltip")
                    .style("opacity", 1);
                var margin = {top: 20, right: 20, bottom: 30, left: 50},
                    width = 400 - margin.left - margin.right,
                    height = 250 - margin.top - margin.bottom;
                var parseDate = d3.time.format("%Y").parse;
                $scope.render = function(data) {
                    var x = d3.time.scale()
                        .range([0, width])
                        .domain(d3.extent(data, function(d){return parseDate(d[0].toString())}));
                    var y = d3.scale.linear()
                        .range([height, 0])
                        .domain(d3.extent(data, function(d){return d[1]}));
                    //Create SVG element
                    var line = d3.svg.line()
                        .x(function(d){return x(parseDate(d[0].toString()))})
                        .y(function(d){return y(d[1])});
                    var svg = d3.select(element[0])
                        .append("svg")
                        .attr("width", width + margin.left + margin.right)
                        .attr("height", height + margin.top + margin.bottom)
                        .append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
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
                        .call(yAxis);
                    svg.append("path")
                        .datum(data)
                        .attr("class", "line")
                        .attr("d", line);
                    svg.selectAll('circle')
                        .data(data)
                        .enter()
                        .append('circle')
                        .attr("r",5)
                        .attr("cx", function(d) { return x(parseDate(d[0].toString())); })
                        .attr("cy", function(d) { return y(d[1]); })
                        .attr("class", "linecircle")
                        .style("pointer-events","all")
                        .append('title')
                        .text(function(d) { return d[0] + ' : ' + d[1];});
                }
                $scope.render($scope.data);
            }
        }
    });
