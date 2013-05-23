
$(function() {

    "use strict";

    var $ = window.jQuery,
        _ = window._,
        Templates = window.Templates,
        user_list_sort_field = null,
        user_list_sort_ascending = true;
    
    function display_users() {
        var params = {
            sort_field: user_list_sort_field,
            sort_order: user_list_sort_ascending ? "ascending" : "descending"
        };
        $.ajax({
            type: "GET",
            dataType: "json",
            contentType: "application/json",
            url: "/api/users",
            data: params
        }).done(function(data) {
            var $user_list = $(Templates.templates["user-list"](data));
            $(".user-list").replaceWith($user_list);
            setTimeout(display_users, 2000);
        });
    };

    function display_apps() {
        $.ajax({
            type: "GET",
            dataType: "json",
            contentType: "application/json",
            url: "/api/apps"
        }).done(function(data) {
            var $app_list = $(Templates.templates["app-list"]({ clusters: data }));
            $(".app-list").replaceWith($app_list);
            setTimeout(display_apps, 1000);
        });
    };

    $("body").on("click", ".user-list th", function(e) {
        var sort_field = $(this).data("field");
        if (sort_field == user_list_sort_field) {
            user_list_sort_ascending = ! user_list_sort_ascending;
        }
        else {
            user_list_sort_field = sort_field;
            user_list_sort_ascending = true;
        }
        display_users();
        e.preventDefault();
        e.stopPropagation();
    });
    
    // Display users on first load
    display_users();
    display_apps();

});

