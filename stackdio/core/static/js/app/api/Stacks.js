define(["lib/q", "app/stores", "app/models"], function (Q, stores, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/stacks/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;
                    var stack;


                    // Clear the store and the grid
                    stores.Stacks.removeAll();

                    for (i in items) {
                        stack = new models.Stack().create(items[i]);

                        // Inject the record into the store
                        stores.Stacks.push(stack);
                    }

                    console.log('stacks', stores.Stacks());

                    // Resolve the promise and pass back the loaded stacks
                    deferred.resolve(stores.Stacks());

                }
            });

            return deferred.promise;
        },
        save: function (stack) {
            var deferred = Q.defer();

            stack.hosts = JSON.stringify(stack.hosts);

            $.ajax({
                url: '/api/stacks/',
                type: 'POST',
                data: stack,
                headers: {
                    "X-CSRFToken": stackdio.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    stores.Stacks.push(response);
                    deferred.resolve();
                }
            });

            return deferred.promise;
        },
        delete: function (record) {

        }
    }
});