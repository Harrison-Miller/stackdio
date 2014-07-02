define([
    'q', 
    'knockout',
    'util/galaxy',
    'util/form',
    'store/Stacks',
    'store/StackHosts',
    'store/StackSecurityGroups',
    'store/StackActions',
    'store/Profiles',
    'store/InstanceSizes',
    'store/Blueprints',
    'store/BlueprintHosts',
    'store/BlueprintComponents',
    'api/api'
],
function (Q, ko, $galaxy, formutils, StackStore, StackHostStore, StackSecurityGroupStore, StackActionStore, ProfileStore, InstanceSizeStore, BlueprintStore, BlueprintHostStore, BlueprintComponentStore, API) {
    var vm = function () {
        var self = this;

        /*
         *  ==================================================================================
         *   V I E W   V A R I A B L E S
         *  ==================================================================================
        */
        self.selectedBlueprint = ko.observable(null);
        self.blueprintHostDefinitions = ko.observable(null);
        self.selectedStack = ko.observable(null);
        self.stackTitle = ko.observable();
        self.blueprintTitle = ko.observable();
        self.blueprintProperties = ko.observable();
        self.stackPropertiesStringified = ko.observable();
        self.editMode = ko.observable('create');

        self.historicalLogText = ko.observable();
        self.launchLogText = ko.observable();
        self.orchestrationLogText = ko.observable();
        self.orchestrationErrorLogText = ko.observable();
        self.provisioningLogText = ko.observable();
        self.provisioningErrorLogText = ko.observable();

        self.StackStore = StackStore;
        self.StackHostStore = StackHostStore;
        self.StackSecurityGroupStore = StackSecurityGroupStore;
        self.StackActionStore = StackActionStore;
        self.ProfileStore = ProfileStore;
        self.InstanceSizeStore = InstanceSizeStore;
        self.BlueprintHostStore = BlueprintHostStore;
        self.BlueprintComponentStore = BlueprintComponentStore;
        self.BlueprintStore = BlueprintStore;
        self.$galaxy = $galaxy;

        /*
         *  ==================================================================================
         *   R E G I S T R A T I O N   S E C T I O N
         *  ==================================================================================
        */
        self.id = 'stack.accessrules';
        self.templatePath = 'stack.accessrules.html';
        self.domBindingId = '#stack-accessrules';

        try {
            $galaxy.join(self);
        } catch (ex) {
            console.log(ex);            
        }


        /*
         *  ==================================================================================
         *   E V E N T   S U B S C R I P T I O N S
         *  ==================================================================================
         */
        $galaxy.network.subscribe(self.id + '.docked', function (data) {
            BlueprintStore.populate().then(function () {
                return StackStore.populate();
            }).then(function () {
                self.init(data);
            });
        });


        /*
         *  ==================================================================================
         *   V I E W   M E T H O D S
         *  ==================================================================================
         */

        self.init = function (data) {
            var blueprint = null;
            var stack = null;
            var stackHosts = [];

            // Automatically select the first tab in the view so that if the user had
            // clicked on the logs or orchestraton tab previously, it doesn't end up
            // showing a blank view
            $('#stack-tabs a[id="accessrules"]').tab('show');

            self.stackPropertiesStringified('');

            if (data.hasOwnProperty('stack')) {
                self.editMode('update');

                stack = StackStore.collection().filter(function (s) {
                    return s.id === parseInt(data.stack, 10);
                })[0];

                self.stackTitle(stack.title);

                // Get security groups 
                getSecurityGroups(stack);

            } else {
                $galaxy.transport('stack.list');
            }

            self.selectedStack(stack);
        };

        self.goToTab = function (obj, evt) {
            var tab=evt.target.id;
            $galaxy.transport({
                location: 'stack.'+tab,
                payload: {
                    stack: self.selectedStack().id
                }
            });
        };
 
        self.addRule = function (obj, evt) {
            var curId = evt.target.form.id;
            var col = self.StackSecurityGroupStore.collection();
            var curGroup = null;

            for (var i = 0; i < col.length; ++i) {
                if (col[i].id.toString() === curId) {
                    curGroup = col[i];
                    break;
                }
            }
            
            var record = formutils.collectFormFields(evt.target.form);
            
            var from_port = null;
            var to_port = null;

            if (record.add_rule_port_range.value.indexOf("-") > -1) {
                var spl = record.add_rule_port_range.value.split("-");
                from_port = parseInt(spl[0]);
                to_port = parseInt(spl[1]);
            } else {
                from_port = parseInt(record.add_rule_port_range.value);
                to_port = from_port;
            }

            API.SecurityGroups.updateRule(curGroup, {
                "action" : "authorize",
                "protocol": record.add_rule_protocol.value,
                "from_port": from_port,
                "to_port": to_port,
                "rule": record.add_rule_ip_address.value === "" ? record.add_rule_group.value : record.add_rule_ip_address.value
            }).then(function () {
                formutils.clearForm(curId);
                getSecurityGroups(self.selectedStack());
            });
        };

        self.deleteRule = function (obj, evt) {
            var curId = evt.target.form.id.split("_")[0];
            var col = self.StackSecurityGroupStore.collection();
            var curGroup = null;

            for (var i = 0; i < col.length; ++i) {
                if (col[i].id.toString() === curId) {
                    curGroup = col[i];
                    break;
                }
            }

            var record = formutils.collectFormFields(evt.target.form);

            API.SecurityGroups.updateRule(curGroup, {
                "action" : "revoke",
                "protocol": record.rule_protocol.value,
                "from_port": parseInt(record.rule_from_port.value),
                "to_port": parseInt(record.rule_to_port.value),
                "rule": record.rule_rule.value
            }).then(function () {
                getSecurityGroups(self.selectedStack());
            });

        }

        function getSecurityGroups(stack) {
            API.Stacks.getSecurityGroups(stack).then(function (groups) {
                
                groups.results.forEach(function (group) {
                    group.rules.forEach(function (rule) {
                        rule.uid = group.id + "_" + rule.protocol + "-" + rule.from_port + "-" + rule.to_port;
                    });
                });

                self.StackSecurityGroupStore.collection.removeAll();
                self.StackSecurityGroupStore.add(groups.results);
            }).then(function () {
                self.StackSecurityGroupStore.collection.sort(function (left, right) {
                    return left.blueprint_host_definition.title < right.blueprint_host_definition.title ? -1 : 1;   
                });
            });

        }
      
        self.getStatusType = function(status) {
            switch(status) {
                case 'waiting':
                    return 'info';
                case 'running':
                    return 'warning';
                case 'finished':
                    return 'success';
                default:
                    return 'default';
            }
	    };

    };
    return new vm();
});
