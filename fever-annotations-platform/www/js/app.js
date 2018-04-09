var app = angular.module("annotateapp",['chart.js','ngRoute','sticky','ngSanitize']);

if(typeof(String.prototype.trim) === "undefined")
{
    String.prototype.trim = function()
    {
        return String(this).replace(/^\s+|\s+$/g, '');
    };
}


app.directive('ngConfirmClick', [
        function(){
            return {
                link: function (scope, element, attr) {
                    var msg = attr.ngConfirmClick || "Are you sure?";
                    var clickAction = attr.confirmedClick;
                    element.bind('click',function (event) {
                        if ( window.confirm(msg) ) {
                            scope.$eval(clickAction)
                        }
                    });
                }
            };
    }])






app.directive('modal', function(){
        return {
            template: '<div class="modal" tabindex="-1" role="dialog" aria-labelledby="myLargeModalLabel" aria-hidden="true"><div class="modal-dialog modal-lg"><div class="modal-content" ng-transclude><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button><h4 class="modal-title" id="myModalLabel">Modal title</h4></div></div></div></div>',
            restrict: 'E',
            transclude: true,
            replace:true,
            scope:{visible:'=', onShown:'&', onHide:'&'},
            link:function postLink(scope, element, attrs){

                $(element).modal({
                    show: false,
                    keyboard: attrs.keyboard,
                    backdrop: attrs.backdrop
                });

                scope.$watch(function(){return scope.visible;}, function(value){

                    if(value == true){
                        $(element).modal('show');
                    }else{
                        $(element).modal('hide');
                    }
                });

                $(element).on('shown.bs.modal', function(){
                  scope.$apply(function(){
                    scope.$parent[attrs.visible] = true;
                  });
                });

                $(element).on('shown.bs.modal', function(){
                  scope.$apply(function(){
                      scope.onShown({});
                  });
                });

                $(element).on('hidden.bs.modal', function(){
                  scope.$apply(function(){
                    scope.$parent[attrs.visible] = false;
                  });
                });

                $(element).on('hidden.bs.modal', function(){
                  scope.$apply(function(){
                      scope.onHide({});
                  });
                });
            }
        };
    }
);


app.directive('modalHeader', function(){
    return {
        template:'<div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button><h4 class="modal-title">{{title}}</h4></div>',
        replace:true,
        restrict: 'E',
        scope: {title:'@'}
    };
});

app.directive('modalBody', function(){
    return {
        template:'<div class="modal-body" ng-transclude></div>',
        replace:true,
        restrict: 'E',
        transclude: true
    };
});

app.directive('modalFooter', function(){
    return {
        template:'<div class="modal-footer" ng-transclude></div>',
        replace:true,
        restrict: 'E',
        transclude: true
    };

});


app.run(function($rootScope,$http) {
    $rootScope.working = false;
    $rootScope.done = false;

    $rootScope.username = "guest"
    $rootScope.total_count = 0;
    $rootScope.total_count_wf2 = 0;
    $rootScope.session_count = 0

    $rootScope.oracles = ["spikiris","jthrn","guest","timohowd","smicon","ngoudre","rdgauthi","marybisb","arrud","chrchrs","mitarpit","tcadwell"]
    $http.get("/count").then(function(response) {
        $rootScope.total_count = response.data.count;
        $rootScope.total_count_wf2 = response.data.count_wf2;
    });

    $http.get("/user").then(function(response) {
        $rootScope.username = response.data.username;
        $rootScope.isOracle = $rootScope.oracles.indexOf($rootScope.username) > -1;

    });

    setInterval(function() {
        $http.get("/count").then(function(response) {
            $rootScope.total_count = response.data.count;
            $rootScope.total_count_wf2 = response.data.count_wf2;
        });
    },60000);
});


app.factory('claimGenerationAnnotationService', ['$rootScope', function ($rootScope) {

    var service = {
        putClaims: function (http, operator, timer, id,claims, testingMode, callback) {
            if ($rootScope.working) {
                return;
            }
            $rootScope.working = true;
            http.post('/submit-claim', {"id": id,"operator": operator, "timer":timer, "true_claims": claims, "testing":testingMode}).then(function successCallback(response) {
                $rootScope.working = false;
                $rootScope.done = true;
                callback(response.data.pos)
            }, function errorCallback(response) {
                $rootScope.working = false;
                alert("A network error occurred\n" + response.statusText + "\n\nPlease report this and retry submitting claims")
            });
        },

        getNextSentence: function(http,callback) {
            http.get("/next").then(function(response) {
                callback(response.data);
            });
        }
    }

    return service;

}]);

app.factory("wikipediaService",["$rootScope", function($rootScope) {
    var service = {

        getWiki: function(http,name,callback) {

            http.get("/wiki/"+name).then(function successCallback(response) {
                callback(response.data)
            }, function errorCallback(response) {
                alert("Unable to add page\n"+response.statusText );
            });

        }

    }

    return service
}])


app.factory('claimMutationAnnotationService', ['$rootScope', function ($rootScope) {

    var service = {
        putClaims: function (http, operator, timer, id,claims,testingMode, callback) {
            if ($rootScope.working) {
                return;
            }
            $rootScope.working = true;
            http.post('/submit-mutations', {"id": id, "operator":operator, "timer":timer, "claims": claims,"testing":testingMode}).then(function successCallback(response) {
                $rootScope.working = false;
                $rootScope.done = true;
                callback(response.data.pos)
            },function errorCallback(response){
                $rootScope.working = false;
                alert("A network error occurred\n" + response.statusText + "\n\nPlease report this and retry submitting claims")
            });
        },

        getClaim: function(http,claim,id,callback) {
            http.get("/mutate/"+claim+"/"+id).then(function(response) {
                callback(response.data);
            });
        }
    }

    return service;

}]);

app.factory('claimStatsService',['$rootScope',function($rootScope) {

    var service = {
        putStats: function(http, operator, workflow, timeSinceLastSubmission, claimsSinceLastSubmission, testingMode) {
            http.post("/submit-stats", {"operator":operator,
            "workflow":workflow,
            "timeSinceLastSubmission":timeSinceLastSubmission,
            "claimsSinceLastSubmission":claimsSinceLastSubmission,
            "testing":testingMode}).then(function successCallback(resp){},function errorCallback(err) {
            console.log(err.statustText)});
        }
    }


    return service;
}]);

app.factory('claimsService',['$rootScope',function($rootScope) {
    
    var service = {
        
        getClaim: function(http,id,callback) {
            
            http.get("/claim/"+id).then(function(resp) {
                callback(resp.data);
            })
            
        },


        putAnnotations: function(http,id,timer,countAll,countCustom,verifiable,selections,supporting,refuting,testingMode,oracleMode,callback) {
            http.post("/labels/"+id, {"timer":timer,"countAll":countAll,"customCount":countCustom, "verifiable":verifiable,"sentences":selections,"oracleMode":oracleMode,"testingMode":testingMode,"supporting":supporting,"refuting":refuting}).then(function(response) {
                callback()
            });
        }
        
    }
    return service
    
}]);


app.factory('wf2ClaimAllocationService',['$rootScope',function($rootScope) {
    var service = {
        getNextClaim: function(http,oracle,test,callback) {
            payload = {}

            if (oracle) {
                payload = {"oracle":true}
            } else if (test) {
                payload = {"test":true}
            }
            http({url:"/nextsentence",params:payload,method:"GET"}).then(function(resp){
                callback(resp.data)
            });
        }

    }

    return service;
}]);

app.factory('localClaimsService', ['$rootScope', function ($rootScope) {

    var service = {

        model: {
            claims: ""
        },

        SaveState: function () {
            sessionStorage.claims = angular.toJson(service.model);

        },

        RestoreState: function () {
            service.model = angular.fromJson(sessionStorage.claims);
        }
    }

    $rootScope.$on("savestate", service.SaveState);
    $rootScope.$on("restorestate", service.RestoreState);

    return service;
}]);

app.factory("timerService", ['$rootScope',function($rootScope) {

    var service  = {
        "service": function () {
            this.minutes = 0
            this.seconds = 0
            this.totalSeconds = 0

            this.timer = "0:00"

            this.incrementTime = function() {
                this.seconds++;
                this.totalSeconds++;

                if (this.seconds >= 60) {
                    this.seconds = 0;
                    this.minutes++;
                }

                this.timer = "" + this.minutes + ":" + (this.seconds > 9 ? this.seconds : "0" + this.seconds);

            }

            this.start = function(onUpdate) {
                var t = this;
                this.interval = setInterval(function() {t.incrementTime(); onUpdate()}, 1000);
            }

        }
    }

    return service;

}]);



app.factory('countService', ['$rootScope', function ($rootScope) {
    var service = {
        model: {
            uuid:'',
            count: 0,
            testingMode: false,
            oracleMode: false
        },

        SaveState: function () {
            sessionStorage.count = angular.toJson(service.model);
            $rootScope.session_count = service.model.count;
        },

        RestoreState: function () {

            if(typeof sessionStorage !== "undefined" && sessionStorage.count !== null) {
                service.model = angular.fromJson(sessionStorage.count);

                    if (typeof service.model !== "undefined") {

                        $rootScope.session_count = service.model.count;
                    } else {
                        service.model = {count: 0, uuid: generateUUID(),testingMode: false, oracleMode:false};

                        $rootScope.session_count = service.model.count;
                    }

            } else {

            }
        }

    }

    $rootScope.$on("savestate", service.SaveState);
    $rootScope.$on("restorestate", service.RestoreState);

    return service;
}]);


app.factory('localMutationService', ['$rootScope', function ($rootScope) {

    var service = {

        model: {
            rephrase: "",
            negate: "",
            similar: "",
            dissimilar: "",
            specific: "",
            general: ""
        },

        SaveState: function () {
            sessionStorage.claims = angular.toJson(service.model);

        },

        RestoreState: function () {
            service.model = angular.fromJson(sessionStorage.claims);
        }
    }

    $rootScope.$on("savestate", service.SaveState);
    $rootScope.$on("restorestate", service.RestoreState);

    return service;
}]);



app.config(['$routeProvider', function($routeProvider) {
    $routeProvider.
        when('/', {
            templateUrl: 'views/welcome.html?n='+Math.random(),
            controller: 'WelcomeController'
        }).when("/generate-claims", {
            templateUrl: 'views/annotate-wf1a.html?n='+Math.random(),
            controller: 'WF1aController'
        }).when("/mutate-claims/:claim/:id", {
            templateUrl: 'views/annotate-wf1b.html?n=' + Math.random() ,
            controller: 'WF1bController'
        }).when("/tutorial", {
            templateUrl: 'views/tutorial.html?n='+ Math.random(),
            controller: 'TutorialController'
        }).
        when('/tutorial2', {
            templateUrl: 'views/tutorial2.html?n='+ Math.random(),
            controller: 'Tutorial2Controller'
        })
        .when('/walkthrough', {
            redirectTo: '/walkthrough/1'
        }).when('/walkthrough/:id', {
            templateUrl: 'views/annotate-wf1a.html?n='+ Math.random(),
            controller: 'WalkthroughController'
        }).
        when('/feedback/:id', {
            templateUrl: 'views/feedback-wf1a.html?n='+ Math.random(),
            controller: 'FeedbackController'
        }).
        when('/walkthrough2', {
            redirectTo: '/walkthrough2/1'
        }).
        when('/walkthrough2/:id', {
            templateUrl: 'views/annotate-wf1b.html?n='+ Math.random(),
            controller: 'Walkthrough2Controller'
        }).
        when('/feedback2/:id', {
            templateUrl: 'views/feedback-wf1b.html?n='+ Math.random(),
            controller: 'Feedback2Controller'
        }).
        when("/label-claims", {
            templateUrl: 'views/annotate-wf2.html?n='+Math.random(),
            controller: 'WF2Controller',
            reloadOnSearch:false
        }).
        when("/label-claims/:id", {
            templateUrl: 'views/annotate-wf2.html?n='+Math.random(),
            controller: 'WF2Controller',
            reloadOnSearch:false
        }).

        when("/dashboard", {
            templateUrl: 'views/dashboard.html?n='+Math.random(),
            controller: 'DashboardController'
        }).
        otherwise({
            redirectTo: '/'
        });


}]);



var checkTextBoxesNotEmpty = function() {

    textboxes = angular.element(document).find("textarea")

    for(i=0; i<textboxes.length;i++) {
        if(!textboxes[i].value) {
            var r = confirm("At least one field has been left empty.\n\nIf this is intentional, press OK to continue submission. \nPress cancel to edit the claims again")
            if(r) {
                return true
            } else {
                return false
            }
        }
    }
    return true

};



var generateUUID = function() {

    var d = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });

    return uuid;
};



app.controller("DashboardController",function($scope,$http,$location) {



    $http.get("/dashboard").then(function successCallback(response) {
        $scope.last_updated = response.data.wf1.last_run + " UTC"
        $scope.live_count = response.data.wf1.live_count;
        $scope.sandbox_count = response.data.wf1.sandbox_count;
        $scope.done_today = response.data.wf1.done_today
        $scope.time_today = response.data.wf1.time_today
        $scope.done_this_week = response.data.wf1.done_this_week
        $scope.time_this_week = response.data.wf1.time_this_week
        $scope.done_last_week = response.data.wf1.done_last_week
        $scope.time_last_week = response.data.wf1.time_last_week


        $scope.wf2_last_updated = response.data.wf2.last_run + " UTC"
        $scope.wf2_live_count = response.data.wf2.live_count;
        $scope.wf2_total_left = response.data.wf2.total_left;
        $scope.wf2_sandbox_count = response.data.wf2.sandbox_count;
        $scope.wf2_done_today = response.data.wf2.done_today
        $scope.wf2_time_today = response.data.wf2.time_today
        $scope.wf2_done_this_week = response.data.wf2.done_this_week
        $scope.wf2_time_this_week = response.data.wf2.time_this_week
        $scope.wf2_done_last_week = response.data.wf2.done_last_week
        $scope.wf2_time_last_week = response.data.wf2.time_last_week


        $scope.p = response.data.oracle.p
        $scope.r = response.data.oracle.r
        $scope.p_tw = response.data.oracle.p_tw
        $scope.r_tw = response.data.oracle.r_tw
        $scope.p_lw = response.data.oracle.p_lw
        $scope.r_lw = response.data.oracle.r_lw

        $scope.chart_options = { elements : { line : { tension : 0 } } };

        $scope.chart_series = response.data.oracle.chart.series
        $scope.chart_labels = response.data.oracle.chart.labels
        $scope.chart_data = response.data.oracle.chart.data

        $scope.chart_series2 = response.data.oracle.chart2.series
        $scope.chart_labels2 = response.data.oracle.chart2.labels
        $scope.chart_data2 = response.data.oracle.chart2.data


    }, function errorCallback(response) {
        alert("Not authorised to view this page")
        $location.path("/")
    });

});

app.controller("WelcomeController",function($scope,$http,$location, countService) {

    $scope.start = function(testingMode) {

        countService.model.count = 0;
        countService.model.uuid = generateUUID();
        countService.model.testingMode = testingMode;
        countService.SaveState();


        $location.path("/generate-claims")
    }


    $scope.start2 = function(testingMode) {
        countService.model.count = 0;
        countService.model.uuid = generateUUID();
        countService.model.testingMode = testingMode;
        countService.model.oracleMode = false
        countService.SaveState();


        $location.path("/label-claims")
    }


    $scope.startOracle = function() {
        countService.model.count = 0;
        countService.model.uuid = generateUUID();
        countService.model.testingMode = false;
        countService.model.oracleMode = true;
        countService.SaveState();


        $location.path("/label-claims")
    }


    $scope.startwf2 = function() {
        $location.path("/label-claims")
    }
    
    
    $scope.tutorial = function() {
        $location.path("/tutorial")
    }

    $scope.total_count = 0;
    $http.get("/count").then(function(response) {
        $scope.total_count = response.data.count;
    });

});


function count_lines(text){
    return (text.match(/^\s*\S/gm) || "").length
}

app.controller("WF1aController",function($rootScope,$scope,$http,$location,$route, claimGenerationAnnotationService, timerService, countService,claimStatsService) {
    $rootScope.done = false;
    timer = new timerService.service();
    timer.start(function() { $scope.timer = timer.timer; $scope.$apply() })

    countService.RestoreState()
    if (typeof countService.model !== "undefined") {
        $scope.count = countService.model.count;
    } else {
        countService.model = {count: 0, uuid: generateUUID(),testingMode: false};
        $scope.count = 0;
    }

    startCount = countService.model.count;

    $scope.testingMode = countService.model.testingMode;

    $scope.set_article = function(data) {
        $scope.id = data.id;
        $scope.entity = data.entity;
        $scope.sentence = data.sentence;
        $scope.context_before = data.context_before;
        $scope.context_after = data.context_after;
        $scope.misinformation_type = data.misinformation_type;
        $scope.dictionary = {};
        angular.forEach(data.dictionary, function(obj,idx) {
            $scope.dictionary[idx] = obj;
        });
    };

    claimGenerationAnnotationService.getNextSentence($http,$scope.set_article)

    $scope.skip = function() {
        $route.reload();
    }

    $scope.home = function() {
        $location.path("/");
    }

    $scope.next_page = function(id) {
        $location.path('/mutate-claims/'+$scope.id+'/'+id);
    }

    $scope.submit = function() {
        if(checkTextBoxesNotEmpty()) {
            if (typeof $scope.true_claims !== "undefined") {
                countService.model.count += count_lines($scope.true_claims);

                countService.SaveState();
            }

            id = $scope.id
            claims = $scope.true_claims;

            claimsSinceLastSubmission = countService.model.count - startCount
            claimStatsService.putStats($http,countService.model.uuid,"wf1a",timer.totalSeconds,claimsSinceLastSubmission, countService.model.testingMode)

            claimGenerationAnnotationService.putClaims($http, countService.model.uuid, timer.totalSeconds, id, claims, countService.model.testingMode, $scope.next_page);

            clearInterval(timer.interval)
        }
    };

});


app.controller("WF1bController",function($rootScope,$scope,$http,$location,$route,$routeParams, claimMutationAnnotationService, timerService, countService,claimStatsService) {
    $rootScope.done = false;
    timer = new timerService.service()
    timer.start(function() { $scope.timer = timer.timer; $scope.$apply() })
    countService.RestoreState()
    if (typeof countService.model !== "undefined") {
        $scope.count = countService.model.count;
    } else {
        countService.model = {count: 0, uuid: generateUUID(), testingMode:false};
        $scope.count = 0;
    }


    $scope.testingMode = countService.model.testingMode;
    console.log(countService.model)

    startCount = countService.model.count;


    $scope.claim_types = ["rephrase","similar","dissimilar","specific","general","negate"]

    $scope.set_article = function(response) {
        data = response.article

        $scope.id = data.id;
        $scope.entity = data.entity;
        $scope.sentence = data.sentence;
        $scope.context_before = data.context_before;
        $scope.context_after = data.context_after;
        $scope.dictionary = {};

        $scope.rephrase = {}
        $scope.negate = {}
        $scope.substitute_dissimilar = {}
        $scope.substitute_similar = {}
        $scope.specific = {}
        $scope.general = {}

        if (typeof response.annotation.true_claims === 'undefined') {
            $location.path('/generate-claims');
            return
        } else {
            $scope.claims = response.annotation.true_claims.split("\n")
        }

        if($scope.claims.length == 0) {
            $location.path('/generate-claims');
            return
        }

        angular.forEach(data.dictionary, function(obj,idx) {
            $scope.dictionary[idx] = obj;
        });

    };



    claimMutationAnnotationService.getClaim($http,$routeParams['claim'],$routeParams['id'],$scope.set_article)

    $scope.next_page = function() {
        $location.path('/generate-claims');
    }

    $scope.submit = function() {
        if(checkTextBoxesNotEmpty()) {
            angular.forEach($scope.rephrase, function(obj,idx) {
                if (typeof obj !== "undefined") {
                    countService.model.count+= count_lines(obj)
                }
            });

            angular.forEach($scope.negate, function(obj,idx) {
                if (typeof obj !== "undefined") {
                    countService.model.count+= count_lines(obj)
                }
            });

            angular.forEach($scope.substitute_similar, function(obj,idx) {
                if (typeof obj !== "undefined") {
                    countService.model.count+= count_lines(obj)
                }
            });

            angular.forEach($scope.substitute_dissimilar, function(obj,idx) {
                if (typeof obj !== "undefined") {
                    countService.model.count+= count_lines(obj)
                }
            });

            angular.forEach($scope.specific, function(obj,idx) {
                if (typeof obj !== "undefined") {
                    countService.model.count+= count_lines(obj)
                }
            });

            angular.forEach($scope.general, function(obj,idx) {
                if (typeof obj !== "undefined") {
                    countService.model.count+= count_lines(obj)
                }
            });

            countService.SaveState()

            id =$routeParams['id'];
            claims = $scope.true_claims;

            claimsSinceLastSubmission = countService.model.count - startCount
            claimStatsService.putStats($http,countService.model.uuid,"wf1b",timer.totalSeconds,claimsSinceLastSubmission, countService.model.testingMode)

            claimMutationAnnotationService.putClaims($http,countService.model.uuid, timer.totalSeconds, id,
                {"rephrase": $scope.rephrase,
                 "negate": $scope.negate,
                 "substitute_similar": $scope.substitute_similar,
                 "substitute_dissimilar":$scope.substitute_dissimilar,
                 "specific": $scope.specific,
                 "general":$scope.general},
                countService.model.testingMode, $scope.next_page);

            clearInterval(timer.interval)
        }
    };

});


app.controller("WF2Controller",function($scope,$routeParams,$anchorScroll, $http,$location,$route,wf2ClaimAllocationService,countService,claimsService, timerService,claimStatsService, wikipediaService) {
    timer = new timerService.service();
    timer.start(function() { $scope.timer = timer.timer; $scope.$apply() })

    countService.RestoreState()
    if (typeof countService.model !== "undefined") {
        $scope.count = countService.model.count;
    } else {
        countService.model = {count: 0, uuid: generateUUID(),testingMode: false};
        $scope.count = 0;
    }

    startCount = countService.model.count;
    $scope.testingMode = countService.model.testingMode;

    $scope.oracleMode = countService.model.oracleMode;


    $scope.load_claim = function(id) {
        $scope.extra_context = new Set()

        claimsService.getClaim($http,id,function(data) {
            $scope.entity = data.entity
            $scope.rootEntity = data.entity
            $scope.claims = data.claims
            $scope.body = data.body
            $scope.lines = String(data.body).split(/\r?\n/)
            $scope.sentence = data.sentence
            $scope.combined = 0;
            $scope.line_links = $scope.getLinks($scope.lines);
            console.log($scope.line_links)
            $scope.id = id
            $scope.claim = data.claim

        });


    };

    $scope.load_end_screen = function() {
        $scope.showModalEnd = true;
    };

    $scope.goHome = function() {
        $location.path("/");
    }

    $scope.showModal2 = false;

    if(typeof $routeParams.id ==='undefined') {
        claim_id = wf2ClaimAllocationService.getNextClaim($http,$scope.oracleMode,$scope.testingMode,function(data) {
            id = data.claim_id;
            if (id)
                $scope.load_claim(id);
            else
               $scope.load_end_screen();
        });
    } else {
        $scope.load_claim($routeParams.id)
    }

    $scope.getEntities = function(line) {
        ents = new Set();

        bits = line.split(/\t/)
        if(bits.length>2) {
            for (pos = 3; pos<=bits.length; pos+=2) {
                found = bits[pos]
                ents.add(found)
            }
        }

        return Array.from(ents);
    }


    $scope.emptyDict = true;

    $scope.dictionary = {}
    $scope.active = -1;
    $scope.getInfo= function(id, golink) {



        id = id.toString();

        if(id==$scope.active) {
            callback = function() { $scope.goto(golink) } || function () { }
            callback();
            return;
        }

        if($scope.active >= 0) {
            console.log($scope.selections[$scope.active])
            if (hasTrueEntries($scope.selections[$scope.active])) {

                r = confirm("The current sentence has unsaved selections from the dictionary.\nThese are linked to the currently selected sentence and could be forgotten or lost if not saved now. \nContinue?")
                if(r) {
                } else {
                    return;
                }
            }

        }


        index = $scope.support_sents.indexOf(id);
        if (index > -1) {
           $scope.support_sents.splice(index, 1);
        }



        index = $scope.refute_sents.indexOf(id);
        if (index > -1) {
           $scope.refute_sents.splice(index, 1);
        }


        if(id>=0) {
            $scope.numberOfSentencesVisited += 1;
        }

        $scope.dictionary = {};
        $scope.originalSelected = []

        $scope.active = id;

        $scope.emptyDict = true;

        if(!($scope.active in $scope.selections)) {
            $scope.selections[$scope.active] = {}
        }

        entities = $scope.getEntities($scope.lines[id]);


        if (entities.length > 0) {
            $scope.loading = true;
            $scope.emptyDict = false;
            $http.get("/dictionary/"+$scope.entity+"/"+$scope.active).then(function successCallback(response){
                $scope.loading = false;
                $scope.dictionary = response.data




                dictKeys = Object.keys($scope.dictionary);

                for(i = 0; i<dictKeys.length; i++) {
                    activeKeys =  Object.keys($scope.selections[$scope.active])

                    if(activeKeys.indexOf(dictKeys[i])==-1) {

                        $scope.selections[$scope.active][dictKeys[i]] ={}
                    }
                }



                if ($scope.active in $scope.customItems) {
                    for (i = 0; i< $scope.customItems[$scope.active].length; i++) {
                        $scope.dictionary[$scope.customItems[$scope.active][i][0]] = $scope.customItems[$scope.active][i][1]
                    }
                }

                callback = function() { $scope.goto(golink) } || function () { }
                callback();

                $scope.emptyDict = (Object.keys($scope.dictionary).length == 0)
                console.log($scope.emptyDict)
            });


        } else {

            if ($scope.active in $scope.customItems) {
                for (i = 0; i< $scope.customItems[$scope.active].length; i++) {
                    $scope.dictionary[$scope.customItems[$scope.active][i][0]] = $scope.customItems[$scope.active][i][1]
                }
            }


            $scope.emptyDict = (Object.keys($scope.dictionary).length == 0)
        }
    }


    $scope.getLinks = function(lines) {
        line_htmls = {}
        for(i=0; i<lines.length; i++) {
            line_entity_alias = {}
            line = lines[i]
            bits = line.split(/\t/)
            if(bits.length>2) {
                for (pos = 3; pos<=bits.length; pos+=2) {
                    found = bits[pos]

                    line_entity_alias[bits[pos-1]] = bits[pos]
                }
            }


            keys = Object.values(line_entity_alias).sort(function(a, b){
                //Longest first
                return b.length - a.length;
            });


            toRemoveK = []
            for(key1 in keys) {
                for(key2 in keys) {
                    if (keys[key1].length>keys[key2].length) {
                        if(keys[key1].indexOf(keys[key2])!=-1) {
                            toRemoveK.push(keys[key2])
                        }
                    }
                }

            }


            for (item in toRemoveK) {
                keys.splice(keys.indexOf(toRemoveK[item]),1)
            }



            vals = Object.keys(line_entity_alias).sort(function(a, b){
                //Longest first
                return b.length - a.length;
            });

            toRemoveV = []
            for(key1 in vals) {
                for(key2 in vals) {
                    if (vals[key1].length>vals[key2].length) {
                        if(vals[key1].indexOf(vals[key2])!=-1) {
                            toRemoveV.push(vals[key2])
                        }
                    }
                }
            }

            for (item in toRemoveV) {
                vals.splice(vals.indexOf(toRemoveV[item]),1)
            }


            cuts = []


            for(j=0; j<vals.length; j++) {
                surface_form = vals[j]
                destination = line_entity_alias[vals[j]];


                if (keys.indexOf(destination)==-1 && toRemoveV.indexOf(surface_form)==-1) {
                    continue;
                }


                start_idx = bits[1].indexOf(surface_form)

                if(start_idx<0) {
                    continue;
                }

                if(start_idx > 2 && bits[1][start_idx-1]=="]" && (bits[1][start_idx-2]=="N" || bits[1][start_idx-2] == "T" || bits[1][start_idx-2]=="R")) {
                    continue;
                }

                before_text = bits[1].substring(0, start_idx)
                link_text = bits[1].substring(start_idx,start_idx+surface_form.length);


                after_text = bits[1].substring(start_idx+surface_form.length)

                cuts.push([start_idx,surface_form.length, "[START]"+destination.split(" ").join("[JOIN]")+"[SEPARATOR]"+link_text.split(" ").join("[JOIN]")+"[END]"]);
            }


            cuts = Object.values(cuts).sort(function(a, b){
                //order by start idx ascending
                return  a[0]-b[0];
            });


            added = 0;
            for (c = 0; c<cuts.length; c++) {
                cut = cuts[c]

                start_idx =  cut[0]
                before_text = bits[1].substring(0, added+start_idx)
                link_text = bits[1].substring(added+start_idx,added+start_idx+cut[1]);
                after_text = bits[1].substring(added+start_idx+cut[1])

                newb1 = before_text+cut[2]+after_text


                added += (newb1.length-bits[1].length)
                bits[1] = newb1
            }

            line_htmls[i] = []
            last_idx = 0;
            while(bits[1].indexOf("[START]") > -1) {
                start_idx = bits[1].indexOf("[START]")
                sep_idx = bits[1].indexOf("[SEPARATOR]")
                end_idx = bits[1].indexOf("[END]")
                last_idx = end_idx;

                if(start_idx>0) {
                    line_htmls[i].push({ "link":null, "text":bits[1].substring(0,start_idx).replace("[JOIN]"," ") })
                }

                if(start_idx>=0) {
                   line_htmls[i].push({ "link": bits[1].substring(start_idx+7,sep_idx).split("[JOIN]").join(" "), "text": bits[1].substring(sep_idx+11,end_idx).split("[JOIN]").join(" ")   })
                }

                if(end_idx>-1) {
                    bits[1] = bits[1].substring(end_idx+5);
                }

            }


            if(bits[1].length>0) {
                line_htmls[i].push({ "link":null, "text":bits[1] })
            }


        }

        return line_htmls;
    }



    $scope.goto = function(entity) {
        $location.hash("dict_"+entity).replace()
        $anchorScroll();

    }

    $scope.isEmpty == function (obj) {
      return Object.keys(obj).length === 0;
    }

    $scope.selections = {}

    $scope.loading = false;

    $scope.support_sents = []
    $scope.refute_sents = []

    $scope.supports = function(id) {
        index = $scope.refute_sents.indexOf(id);
        if (index > -1) {
           $scope.refute_sents.splice(index, 1);
        }

        if($scope.support_sents.indexOf(id) == -1) {
            $scope.support_sents.push(id)
        }

        $scope.active = -1;
        $scope.dictionary = {}
    }

    $scope.refutes = function (id) {
        index = $scope.support_sents.indexOf(id);
        if (index > -1) {
           $scope.support_sents.splice(index, 1);
        }

        if($scope.refute_sents.indexOf(id) == -1) {
            $scope.refute_sents.push(id)
        }


        $scope.active = -1;
        $scope.dictionary = {}
    }

    $scope.cancel = function (id) {
        index = $scope.support_sents.indexOf(id);
        if (index > -1) {
           $scope.support_sents.splice(index, 1);
        }

        index = $scope.refute_sents.indexOf(id);
        if (index > -1) {
           $scope.refute_sents.splice(index, 1);
        }


        $scope.active = -1;
        $scope.dictionary = {}
    }

    $scope.numberOfSentencesVisited = 0;

    // Submit type -1 to indicate flagging for review (default type is 1)
    $scope.onSubmit = function(submit_type) {
        claimsService.putAnnotations(
                $http,
                $scope.id,
                timer.totalSeconds,
                $scope.numberOfSentencesVisited,
                $scope.numberOfCustomItemsAdded,
                submit_type,
                $scope.selections,
                $scope.support_sents,
                $scope.refute_sents,
                $scope.testingMode,
                $scope.oracleMode,
            function() {
                countService.model.count += 1
                countService.SaveState()
                $route.reload()
            }
        )

        claimStatsService.putStats($http,$scope.id.toString(),"wf2",timer.totalSeconds,1, true)
        clearInterval(timer.interval)


    }


    $scope.onSkip = function(skip_type) {
        $scope.showModal2 = false;

        claimsService.putAnnotations(
                $http,
                $scope.id,
                timer.totalSeconds,
                $scope.numberOfSentencesVisited,
                $scope.numberOfCustomItemsAdded,
                skip_type,
                [],
                {},
                {},
                $scope.testingMode,
                $scope.oracleMode,
            function() {
                if(skip_type>0) {
                    countService.model.count += 1
                    countService.SaveState()
                }
                $route.reload()


            }
        )


        claimStatsService.putStats($http,$scope.id.toString(),"wf2",timer.totalSeconds,1, $scope.testingMode)
        clearInterval(timer.interval)


    }


    $scope.numberOfCustomItemsAdded = 0
    $scope.addCustom = function(url) {
        url = url.replace("https://en.wikipedia.org/wiki/","")
        url = url.replace("http://en.wikipedia.org/wiki/","")
        url = url.replace("en.wikipedia.org/wiki/","")
        url = url.replace("www.wikipedia.org/wiki/","")


        if (url.trim().length > 0) {
            $scope.addItem(url)
            $scope.numberOfCustomItemsAdded += 1

        }

    }



    $scope.addOriginal = function() {
        needsVal = false;
        for (i in $scope.support_sents) {
            sid = $scope.support_sents[i]
            if ($scope.entity in $scope.selections[sid]) {
                if ($scope.active in $scope.selections[sid][$scope.entity]) {
                    needsVal = true;
                    break;
                }
            }

        }

        for (i in $scope.refute_sents) {
            sid = $scope.refute_sents[i]

            if ($scope.entity in $scope.selections[sid]) {
                if ($scope.active in $scope.selections[sid][$scope.entity]) {
                    needsVal = true;
                    break;
                }
            }

        }

        if(needsVal) {
            res = confirm("This sentence has already been selected as part of another annotation that uses the original page. Unless you intend to add new information, continuing will result in a duplicate annotation.")
            if(!res) {
                return;
            }
        }
        $scope.addItem($scope.entity);
    }

    $scope.customItems = {}
    $scope.addItem = function(item) {
        if(item in Object.keys($scope.dictionary)) {
            return;
        }

        wikipediaService.getWiki($http,item,function (data) {
            if(data.text.trim().length == 0) {
                data.text = "0\tNo Information"
            }

            console.log("got");
            clean_text = []
            lines = data.text.split("\n");
            for (i=0;i<lines.length;i++ ) {
                line = lines[i]
                clean_text.push(line.split("\t").length>1? line.split("\t")[1]  :"");

            }
            $scope.dictionary[data.canonical_entity] = clean_text.join("\n");

            if (typeof $scope.customItems[$scope.active] === "undefined") {
                $scope.customItems[$scope.active] = []
            }
            $scope.customItems[$scope.active].push([data.canonical_entity,clean_text.join("\n")])
            $scope.showModal1=false;

        })

    }


});


function hasTrueEntries(d) {
    keys = Object.keys(d)

    for (i = 0; i<keys.length; i++) {

        o = d[keys[i]]
        okeys = Object.keys(o)
        for (j = 0; j< okeys.length; j++) {
            if(o[okeys[j]]) {
                return true;
            }
        }

    }

    return false;
}


app.filter('paras', function () {
    return function(text){
        text = String(text).trim();

        splits = text.split(/\r?\n/)

        console.log(splits)
        ret = ""
        for(i=0; i<splits.length; i++) {
            ret = ret+"<p id='sentence"+i+">"+splits[i].split('\t')[2]+"</p>"
            console.log(i)
        }
        return ret;
    }
});

app.controller("TutorialController",function($scope,$http,$location,claimGenerationAnnotationService) {
    $scope.section1_show = true

    $scope.set_article = function(response) {
        data = response

        $scope.id = data.id;
        $scope.entity = data.entity;
        $scope.sentence = data.sentence;
        $scope.context_before = data.context_before;
        $scope.context_after = data.context_after;
        $scope.misinformation_type = response.mutation;
        $scope.dictionary = {}
        $scope.true_claims = ""
        $scope.false_claim = {}


        angular.forEach(data.dictionary, function(obj,idx) {
            $scope.dictionary[idx] = obj;
        });
    };

    $scope.tryout = function() {
        $location.path("/walkthrough")
    }

    $scope.showcontext = false;
    $scope.toggleContext = function() {
        $scope.showcontext = !$scope.showcontext   ;
    };



    $http.get("/get_tutorial/124").then(function(response) {
        console.log(response.data)
        $scope.set_article(response.data);
    });


});

app.controller("WalkthroughController",function($controller,$scope,$http,$location,$routeParams, localClaimsService) {

    $scope.set_article = function(data) {
        $scope.id = data.id;
        $scope.entity = data.entity;
        $scope.sentence = data.sentence;
        $scope.context_before = data.context_before;
        $scope.context_after = data.context_after;
        $scope.misinformation_type = data.misinformation_type;
        $scope.dictionary = {};
        angular.forEach(data.dictionary, function(obj,idx) {
            $scope.dictionary[idx] = obj;
        });
    };

    $scope.true_claims = ""
    tasks = {}

    tasks[1] = 440
    tasks[2] = 723
    tasks[3] = 192

    $scope.submit = function() {
        localClaimsService.model.claims = $scope.true_claims;
        localClaimsService.SaveState();
        $location.path("/feedback/"+$routeParams['id'])
    }

    $scope.get_next_article = function() {
        $http.get('/get_tutorial/'+tasks[$routeParams['id']]).then(function (resp) {
            $scope.set_article(resp.data)
        });

    }

        $scope.skip = function() {

        $location.path("/feedback/"+$routeParams['id'])
    }

    $scope.home = function() {
        $location.path("/");
    }

    $scope.get_next_article()
});







app.controller("Walkthrough2Controller",function($controller,$scope,$http,$location,$routeParams, localMutationService) {

    $scope.rephrase = {}
    $scope.negate = {}
    $scope.substitute_dissimilar = {}
    $scope.substitute_similar = {}
    $scope.specific = {}
    $scope.general = {}


    tasks = {}
    tasks[1] = "227/0"
    tasks[2] = "702/0"
    tasks[3] = "145/0"

    $scope.submit = function() {

        localMutationService.model.rephrase = $scope.rephrase;
        localMutationService.model.negate = $scope.negate;
        localMutationService.model.similar = $scope.substitute_similar;
        localMutationService.model.dissimilar = $scope.substitute_dissimilar;
        localMutationService.model.specific = $scope.specific;
        localMutationService.model.general = $scope.general;
        localMutationService.SaveState();

        $location.path("/feedback2/"+$routeParams['id'])
    }


    $scope.skip = function() {

        $location.path("/feedback2/"+$routeParams['id'])
    }

    $scope.home = function() {
        $location.path("/");
    }


    $scope.get_next_article = function() {
        $http.get('/mutate_old/'+tasks[$routeParams['id']]).then(function (resp) {
            $scope.set_article = function(response) {
                data = response.article

                console.log(data)
                $scope.entity = data.entity;
                $scope.sentence = data.sentence;
                $scope.context_before = data.context_before;
                $scope.context_after = data.context_after;
                $scope.dictionary = {};


                $scope.claims = response.annotation.true_claims.split("\n")

                angular.forEach(data.dictionary, function(obj,idx) {
                    $scope.dictionary[idx] = obj;
                });
            };
            $scope.set_article(resp.data)
        });

    }

    $scope.get_next_article()
});

app.controller("FeedbackController",function($controller,$scope,$http,$location,$routeParams, localClaimsService) {

    localClaimsService.RestoreState()

    if(typeof localClaimsService.model === "undefined") {
    	localClaimsService.model = {claims:""}    
    }

    $controller("WalkthroughController",{$scope:$scope,$http:$http,$location:$location})

    claims = {}

    claims[1] = "The terrain in Canada is mostly forest and tundra.\nParts of Canada are subject to low temperatures.\nCanada is in North America."
    claims[2] = "Germany has a lower rate of immigration than the United States.\nThe United States has a higher immigration rate than Germany.\n Germany's immigration rate is higher than Japan's."
    claims[3] = "The song Black or White was released by Michael Jackson.\nMichael Jackson released Scream in the 1990s.\nMichael Jackson released videos for the songs 'Black or White' and 'Scream'.\n"


    $scope.submit = function() {
        if (parseInt($routeParams['id']) > 1) {
            $location.path("/tutorial2")
            return
        }
	
        localClaimsService.model.claims = $scope.true_claims;
        localClaimsService.SaveState();
        $location.path("/walkthrough/"+(parseInt($routeParams['id'])+1))
    }


    $scope.skip = function() {
        $route.reload();
    }

    $scope.home = function() {
        $location.path("/");
    }


    $scope.our_claims = claims[$routeParams['id']]
    if (typeof localClaimsService.model !== "undefined") {
    	$scope.true_claims = localClaimsService.model.claims
    }



});


app.controller("Tutorial2Controller",function($scope,$http,$location) {
    $scope.section1_show = true

    $scope.set_article = function(response) {
        data = response

        $scope.id = data.id;
        $scope.entity = data.entity;
        $scope.sentence = data.sentence;
        $scope.context_before = data.context_before;
        $scope.context_after = data.context_after;
        $scope.misinformation_type = response.mutation;
        $scope.dictionary = {}
        $scope.true_claims = ""

        $scope.false_claim = {}

        $scope.claims = "One of the land borders that India shares is with the world's most populous country.\nIndia borders 6 countries. \nThe Republic of India is situated between Pakistan and Burma. ".split("\n")
        responses = ["India borders Greece\nIndia shares a land border with Japan","India borders 5 countries.\nIndia borders 2 continents.","India is situated between Germany and Mongolia."]

        for(var i =0, len = $scope.claims.length; i<len; i++) {
            $scope.false_claim[$scope.claims[i]] = responses[i]
        }

        angular.forEach(data.dictionary, function(obj,idx) {
            $scope.dictionary[idx] = obj;
        });
    };

    $scope.tryout = function() {
        $location.path("/walkthrough2")
    }

    $scope.showcontext = false;
    $scope.toggleContext = function() {
        $scope.showcontext = !$scope.showcontext   ;
    };


    $http.get("/get/124").then(function(response) {
        console.log(response.data)
        $scope.set_article(response.data);

        $scope.misinformation_type = "dis"

    });



});



app.controller("Feedback2Controller",function($controller,$scope,$http,$location,$routeParams, localMutationService) {

    localMutationService.RestoreState()

    claims = {}

    $scope.suggest_rephrase = {}
    $scope.suggest_negate = {}
    $scope.suggest_dissimilar = {}
    $scope.suggest_similar = {}
    $scope.suggest_specific = {}
    $scope.suggest_general = {}


/*
{
        "rephrase":
        "negate":
        "similar":
        "dissimilar":
        "specific":
        "general":
    }
    */
    claims[1] = [{
        "rephrase": "Lady Gaga was part of American Horror Story: Hotel.",
        "negate": "Lady Gaga had nothing to do with American Horror Story.\nLady Gaga has never worked on a TV series.\nLady Gaga only worked on the second season of American Horror Story.",
        "similar": "Lady Gaga worked on Sex in the City.",
        "dissimilar": "Lady Gaga worked on a boat.",
        "specific": "Lady Gaga produced the show: American Horror Story: Hotel.\nLady Gaga worked on two episodes in the fifth season of American Horror Story.",
        "general": "Lady Gaga has worked on a TV series."
    },{
        "rephrase": "Lady Gaga was awarded a Golden Globe.\nGaga received a Globe.",
        "negate": "Gaga hasn't received an award for acting.\nGaga has only won an Oscar.",
        "similar": "Lady Gaga won an Oscar.\nLady Gaga won a Bafta.",
        "dissimilar": "Lady Gaga won a Grammy award.",
        "specific": "Lady Gaga was awarded the Golden Globe for best Supporting Actor in American Horror Story: Hotel.",
        "general": "Lady Gaga has been awarded for her work.",
    }]

    claims[2] = [{
        "rephrase": "",
        "negate": "",
        "similar": "",
        "dissimilar": "",
        "specific": "",
        "general":""
    },{
        "rephrase": "",
        "negate": "",
        "similar": "",
        "dissimilar": "",
        "specific": "",
        "general": ""
    }]

    tasks = {}
    tasks[1] = "227/0"
    tasks[2] = "702/0"
    tasks[3] = "145/0"


    $scope.submit = function() {
        if (parseInt($routeParams['id']) > 0) {
            $location.path("/")
            return
        }


        $location.path("/walkthrough2/"+(parseInt($routeParams['id'])+1))
    }


    $scope.get_next_article = function() {
        $http.get('/mutate_old/'+tasks[$routeParams['id']]).then(function (resp) {
            $scope.set_article = function(response) {
                data = response.article

                console.log(data)
                $scope.entity = data.entity;
                $scope.sentence = data.sentence;
                $scope.context_before = data.context_before;
                $scope.context_after = data.context_after;
                $scope.dictionary = {};


                $scope.claims = response.annotation.true_claims.split("\n")


                angular.forEach(data.dictionary, function(obj,idx) {
                    $scope.dictionary[idx] = obj;
                });



                $scope.rephrase = localMutationService.model.rephrase;
                $scope.negate = localMutationService.model.negate;
                $scope.substitute_similar = localMutationService.model.similar;
                $scope.substitute_dissimilar = localMutationService.model.dissimilar;
                $scope.specific = localMutationService.model.specific ;
                $scope.general = localMutationService.model.general;


                for(var i =0, len = suggested.length; i<len; i++) {
                    $scope.suggest_rephrase[$scope.claims[i]] = suggested[i]["rephrase"]
                    $scope.suggest_negate[$scope.claims[i]] = suggested[i]["negate"]
                    $scope.suggest_similar[$scope.claims[i]] = suggested[i]["similar"]
                    $scope.suggest_dissimilar[$scope.claims[i]] = suggested[i]["dissimilar"]
                    $scope.suggest_specific[$scope.claims[i]] = suggested[i]["specific"]
                    $scope.suggest_general[$scope.claims[i]] = suggested[i]["general"]
                }
            };
            $scope.set_article(resp.data)
        });

    }



    $scope.our_claim = {}
    suggested = claims[$routeParams['id']]



    $scope.get_next_article()


});
