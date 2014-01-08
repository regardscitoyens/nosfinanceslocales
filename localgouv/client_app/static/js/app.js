angular.module('app', ['ui.router'])
    .constant('API_ROOT_URL', '/api')
    .config(
        [ '$stateProvider', '$urlRouterProvider',
        function ($stateProvider, $urlRouterProvider) {
            $urlRouterProvider
                .otherwise('/maps');
            $stateProvider
                .state('home', {
                    url: '/',
                    templateUrl: 'templates/home.html',
                })
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
                    views: {
                        '': {
                            templateUrl: 'templates/maps.html',
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
                    url: '/{id}',
                    views: {
                        '': {
                            templateUrl: 'templates/map.detail.html',
                            controller: 'MapDetailCtrl'
                        }
                    }
                });
        }])
    .controller('Home', ['$scope', '$state',
        function($scope, $state) {
            $scope.$state = $state;
    }])
    .controller('MapsCtrl', ['$scope', '$state', '$http',
        function($scope, $state, $http, maps) {
        }])
    .controller('MapListCtrl', ['$scope', '$state', '$http', 'API_ROOT_URL',
        function($scope, $state, $http, API_ROOT_URL) {
            $http.get(API_ROOT_URL + '/timemaps')
                .success(function(data){
                    $scope.maps = data.results;
            });
        }])
    .controller('MapDetailCtrl', ['$scope', '$state', '$http',
        function($scope, $state, $http) {
            $scope.mapData = {
                baseTileUrl: "http://{s}.tile.cloudmade.com/BC9A493B41014CAABB98F0471D759707/998/256/{z}/{x}/{y}.png",
                tileUrl: "http://www.localfinance.fr/tiles/debt_per_person_2007/{z}/{x}/{y}.png",
                gridUrl: 'http://{s}.tiles.mapbox.com/v3/mapbox.geography-class/{z}/{x}/{y}.grid.json?callback={cb}'
            }
            $scope.onClick = function(data) {
                console.log(e.data);
            }
            $scope.onMouseOver = function(data) {
                console.log("yo");
            }
        }])
    .directive('leafletMap', function () {
        return {
            restrict: "A",
            replace: false,
            scope: {
                mapData: '=',
                click: '&onClick',
                mouseOver: '&onMouseOver',
                mouseOut: '&onMouseOut',
            },
            link: function($scope, element, attrs, controller) {
                var onClick = $scope.click(),
                    onMouseOver = $scope.mouseOver(),
                    onMouseOut = $scope.mouseOut();
                element[0].width = '100%';
                var cloudmadeAttribution = 'Map data &copy; 2011 OpenStreetMap contributors, Imagery &copy; 2011 CloudMade',
                    cloudmade = new L.TileLayer($scope.mapData.baseTileUrl, {attribution: cloudmadeAttribution}),
                    mylyr = new L.TileLayer($scope.mapData.tileUrl),
                    utfGrid = new L.UtfGrid($scope.mapData.gridUrl);

                var interactiveLayerGroup = L.layerGroup([cloudmade, mylyr, utfGrid]);

                //Events
                utfGrid.on('click', function (e) {
                    if (e.data) {
                        onClick(e.data)
                    } else {
                    }
                });
                utfGrid.on('mouseover', function (e) {
                    if (e.data) {
                        onMouseOver(e.data)
                    } else {
                    }
                });
                utfGrid.on('mouseout', function (e) {
                    onMouseOut()
                });

                //Create our map with just the base TileLayer
                var map = L.map(element[0])
                                .setView([0, 0], 1)
                                .addLayer(interactiveLayerGroup);
            }
        }});
