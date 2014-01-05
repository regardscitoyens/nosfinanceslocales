angular.module('app', ['ui.router'])
    .config(
        [ '$stateProvider', '$urlRouterProvider',
        function ($stateProvider, $urlRouterProvider) {
            $urlRouterProvider
                .otherwise('/');
            $stateProvider
                .state('home', {
                    url: '/',
                    templateUrl: '/static/templates/home.html',
                    // You can pair a controller to your template. There *must* be a template to pair with.
                    controller: 'HomeCtrl'
                })
                .state('localfinance', {
                    url: '/{id:[0-9]{1,4}}',
                    views: {
                        '': {
                            templateUrl: '/static/templates/localfinance.detail.html',
                            controller: 'LocalFinanceDetailCtrl'
                        },
                    }
                })
                .state('maps', {
                    abstract: true,
                    url: '/maps',
                    views: {
                        '': {
                            templateUrl: '/static/templates/maps.html',
                        }
                    }
                })
                .state('maps.list', {
                    url: '/',
                    views: {
                        '': {
                            templateUrl: '/static/templates/map.list.html',
                            controller: 'MapListCtrl'
                        }
                    },
                })
                .state('maps.detail', {
                    url: '/{id}',
                    views: {
                        '': {
                            templateUrl: '/static/templates/map.detail.html',
                            controller: 'MapDetailCtrl'
                        }
                    }
                });
        }])
    .controller('Home', ['$scope', '$state', '',
        function($scope, $state) {
            $scope.$state = $state;
    }])
    .controller('MapsCtrl', ['$scope', '$state', '$http',
        function($scope, $state, $http) {
        }])
    .controller('MapListCtrl', ['$scope', '$state', '$http',
        function($scope, $state, $http) {
        }])
    .controller('MapDetailCtrl', ['$scope', '$state', '$http',
        function($scope, $state, $http) {
            $scope.mapData = {
                tileUrl: "http://{s}.tile.cloudmade.com/BC9A493B41014CAABB98F0471D759707/998/256/{z}/{x}/{y}.png",
                gridUrl: 'http://{s}.tiles.mapbox.com/v3/mapbox.geography-class/{z}/{x}/{y}.grid.json?callback={cb}'
            }
            $scope.onClick = function(e) {
            }
            $scope.onMouseOver = function(e) {
            }
        }])
    .directive('leafletMap', function () {
        return {
            restrict: "A",
            replace: false,
            scope: {
                mapData: '=',
                onClick: '&',
                onMouseOver: '&',
                onMouseOut: '&',
            },
            link: function($scope, element, attrs, controller) {
                element[0].width = '100%';
                var cloudmadeAttribution = 'Map data &copy; 2011 OpenStreetMap contributors, Imagery &copy; 2011 CloudMade',
                    cloudmade = new L.TileLayer(mapData.tileUrl, {attribution: cloudmadeAttribution});
                var utfGrid = new L.UtfGrid(mapData.gridUrl);

                var interactiveLayerGroup = L.layerGroup([cloudmade, utfGrid]);

                //Events
                utfGrid.on('click', function (e) {
                    if (e.data) {
                        $scope.onClick(e)
                    } else {
                    }
                });
                utfGrid.on('mouseover', function (e) {
                    if (e.data) {
                        $scope.onMouseOver(e)
                    } else {
                    }
                });
                utfGrid.on('mouseout', function (e) {
                        $scope.onMouseOut(e)
                    } else {
                });


                //Create our map with just the base TileLayer
                var map = L.map(element[0])
                                .setView([0, 0], 1)
                                .addLayer(interactiveLayerGroup);
            }
        }});
