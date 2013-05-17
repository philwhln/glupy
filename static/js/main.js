
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
            $(".user-stats span[data-field=total]").html(data.total);
            display_twitter_follow_buttons();
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

});

