define(["knockout",
        "app/settings",
        "app/util/form",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, settings, formutils, models, stores, API) {

   return function stackViewModel () {
        var self = this;

        self.stackActions = ['Stop', 'Terminate', 'Start', 'Launch'];
        self.stackHostActions = ['Stop', 'Terminate', 'Start'];
        self.selectedProfile = null;
        self.selectedAccount = null;

        self.doStackAction = function (action, evt, stack) {
            var data = JSON.stringify({
                action: action.toLowerCase()
            });

            $.ajax({
                url: '/api/stacks/' + stack.id + '/',
                type: 'PUT',
                data: data,
                headers: {
                    "X-CSRFToken": stackdio.csrftoken,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                success: function (response) {
                    console.log(response);
                    API.Stacks.load();
                }
            });
        };


        self.doStackHostAction = function (action, evt, host) {
            var data = JSON.stringify({
                action: action.toLowerCase()
            });

            // $.ajax({
            //     url: '/api/stacks/' + stack.id + '/',
            //     type: 'PUT',
            //     data: data,
            //     headers: {
            //         "X-CSRFToken": stackdio.csrftoken,
            //         "Accept": "application/json",
            //         "Content-Type": "application/json"
            //     },
            //     success: function (response) {
            //         console.log(response);
            //         API.Stacks.load();
            //     }
            // });
        };

        self.saveStack = function (autoLaunch) {
            var h, host, hosts = stores.NewHosts();

            var stack = {
                cloud_provider: self.selectedAccount.id,
                auto_launch: autoLaunch === true,
                title: document.getElementById('stack_title').value,
                description: document.getElementById('stack_purpose').value,
                hosts: hosts
            };

            API.Stacks.save(stack)
                .then(function () {
                    stores.NewHosts.removeAll();

                    // Clear the stack form
                    $('#stack_title').val('');
                    $('#stack_purpose').val('');

                    // Hide the stack form
                    $( "#stack-form-container" ).dialog("close");

                    $("#alert-success").show();
                });
        }

        self.launchStack = function (model, evt) {
            self.saveStack(true);
        };

        self.showStackDetails = function (stack) {
            API.StackHosts.load(stack)
                .then(function (response) {
                    self.showStackHosts();
                });
            return;
        };


        // 
        //      S T A C K   H O S T S
        // 
        self.showHostMetadata = function (host) {
            stores.HostMetadata.removeAll();
            _.each(host.ec2_metadata, function (v, k, l) {
                if (typeof v !== "object") {
                    stores.HostMetadata.push({ key: k, value: v });
                }
            });

            $("#host-metadata-container").dialog("open");
        };

        self.closeHostMetadata = function () {
            $( "#host-metadata-container" ).dialog("close");
        };



        // 
        //      N E W   H O S T S
        // 
        self.addHost = function (model, evt) {
            var record = formutils.collectFormFields(evt.target.form);
            var v, vol;

            // Create a new host definition
            var host = new models.NewHost().create({ 
                id: '',
                host_count: record.host_count.value,
                host_pattern: record.host_hostname.value,
                host_size: record.host_instance_size.value,
                cloud_profile: self.selectedProfile.id,
                roles: record.host_roles,
                host_security_groups: record.host_security_groups.value
            });

            host.salt_roles = _.map(host.roles, function (r) { return r.value; });

            // Add the chosen instance size to the host definition
            host.size = _.find(stores.InstanceSizes(), function (i) {
                return i.id === parseInt(record.host_instance_size.value, 10);
            });

            // Add some HTML to display for the chosen roles
            host.flat_roles = _.map(host.roles, function (r) { 
                return '<div style="line-height:15px !important;">' + r.text + '</div>'; 
            }).join('');

            // Add spot instance config
            if (record.spot_instance_price.value !== '') {
                host.spot_config = {};
                host.spot_config.spot_price = record.spot_instance_price.value;
            }

            // Add volumes to the host
            host.volumes = [];
            for (v in stores.HostVolumes()) {
                vol = stores.HostVolumes()[v];
                host.volumes.push({
                    snapshot: vol.snapshot.id,
                    device: vol.device,
                    mount_point: vol.mount_point
                });
            }

            console.log('new host', host);
            stores.NewHosts.push(host);

            // Clear out the spot instance bid price field
            document.getElementById('spot_instance_price').value = "";
        };

        self.removeHost = function (host) {
            stores.NewHosts.remove(host);
        };


        self.showStackHosts = function () {
            $( "#stack-details-container" ).dialog("open");
        };

        self.closeStackHosts = function () {
            $( "#stack-details-container" ).dialog("close");
        };

        self.showStackForm = function (account) {
            self.selectedAccount = account;
            $( "#stack-form-container" ).dialog("open");
        };

        self.closeStackForm = function () {
            $( "#stack-form-container" ).dialog("close");
        };

        self.showHostForm = function (profile) {
            self.selectedProfile = profile;
            $('#host_instance_size').selectpicker('val', profile.default_instance_size);
            $( "#host-form-container" ).dialog("open");
        };

        self.closeHostForm = function () {
            formutils.clearForm('host-form');
            $( "#host-form-container" ).dialog("close");
        };

        self.showSuccess = function () {
            $("#alert-success").show();
            setTimeout('$("#alert-success").hide()', 3000);
        };


        /*
         *  ==================================================================================
         *  D I A L O G   E L E M E N T S
         *  ==================================================================================
         */
        $("#stack-details-container").dialog({autoOpen: false, width: 650, modal: false });
        $("#host-metadata-container").dialog({autoOpen: false, width: 500, modal: false });
        $("#host-form-container").dialog({position: [(window.innerWidth / 2) - 275,50], autoOpen: false, width: 600, modal: true });
        $("#stack-form-container").dialog({autoOpen: false, width: window.innerWidth - 225, height: 500, position: [200,50], modal: false });



        /*
         *  ==================================================================================
         *  D A T A   T A B L E   E L E M E N T S
         *  ==================================================================================
         */
        $('#stacks').dataTable({
            "bPaginate": false,
            "bLengthChange": false,
            "bFilter": true,
            "bSort": false,
            "bInfo": false,
            "bAutoWidth": true,
            "bFilter": false
        });

        $('#stack-hosts').dataTable({
            "bPaginate": false,
            "bLengthChange": false,
            "bFilter": true,
            "bSort": false,
            "bInfo": false,
            "bAutoWidth": true,
            "bFilter": false
        });







   }

});